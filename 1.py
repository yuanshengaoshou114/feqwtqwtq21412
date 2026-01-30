import json
from collections import defaultdict
from pathlib import Path
from typing import List, Dict, Set, Any
from datetime import datetime
import re

def find_data_file(filename: str, search_paths: List[Path] = None) -> Path:
    if search_paths is None:
        search_paths = [
            Path("raw-data/CN/ShareCfg"),
            Path("raw-data/CN/sharecfgdata"),
            Path("raw-data/CN/GameCfg"),
            Path("raw-data/CN"),
            Path("raw-data"),
            Path("."),
            Path("sharecfgdata"),
            Path("ShareCfg"),
            Path("GameCfg")
        ]
  
    print(f"[DEBUG] 开始搜索文件: {filename}")
    for path in search_paths:
        file_path = path / filename
        if file_path.exists():
            print(f"[SUCCESS] 找到文件: {file_path}")
            return file_path
        else:
            print(f"[DEBUG] 未在 {file_path} 找到")
  
    print(f"[ERROR] 文件 {filename} 在所有路径中均未找到")
    return None

def load_json_file(file_path: Path) -> Dict:
    print(f"[INFO] 尝试加载文件: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict):
                print(f"[SUCCESS] 加载成功 (dict)，键数量: {len(data)}")
                return data
            elif isinstance(data, list):
                converted = {str(i): item for i, item in enumerate(data) if item is not None}
                print(f"[WARNING] 原文件是 list，已转换为 dict，条目数: {len(converted)}")
                return converted
            else:
                print(f"[ERROR] 文件格式异常，顶层类型: {type(data)}")
                return {}
    except Exception as e:
        print(f"[ERROR] 加载失败 {file_path}: {str(e)}")
        return {}

def replace_namecodes(data: Any, code_mapping: Dict) -> Any:
    def replace_match(match):
        code = match.group(1)
        return code_mapping.get(code, {}).get('name', match.group(0))
  
    pattern = r'{namecode:(\d+)}'
  
    if isinstance(data, str):
        return re.sub(pattern, replace_match, data)
    elif isinstance(data, dict):
        return {k: replace_namecodes(v, code_mapping) for k, v in data.items()}
    elif isinstance(data, list):
        return [replace_namecodes(v, code_mapping) for v in data]
    return data

def process_ships(original_data: Dict, code_mapping: Dict) -> List[Dict]:
    print(f"[INFO] 开始处理 ships，原始数据条目: {len(original_data)}")
    seen_groups: Set[str] = set()
    result = []
  
    sorted_ships = sorted(original_data.items(), key=lambda x: int(x[0]))
  
    for idx, (ship_id, ship_data) in enumerate(sorted_ships, start=1):
        processed_data = replace_namecodes(ship_data, code_mapping)
      
        raw_group = processed_data.get("ship_group")
        ship_group = ""
      
        if isinstance(raw_group, list):
            ship_group = next((str(x) for x in raw_group if x), "")
        elif raw_group:
            ship_group = str(raw_group)
          
        final_group = ship_group if ship_group not in seen_groups else ""
        if ship_group:
            seen_groups.add(ship_group)
      
        result.append({
            "id": ship_id,
            "id2": str(idx),
            "name": processed_data.get("name", ""),
            "ship_group": final_group,
            "painting": processed_data.get("painting", "")
        })
  
    print(f"[SUCCESS] ships 处理完成，生成记录: {len(result)}")
    return result

def process_skins(original_data: Dict, code_mapping: Dict) -> List[Dict]:
    print(f"[INFO] 开始处理 skins，原始数据条目: {len(original_data)}")
    result = []
    skin_idx = 1
  
    for ship_id, ship_data in sorted(original_data.items(), key=lambda x: int(x[0])):
        processed_data = replace_namecodes(ship_data, code_mapping)
      
        if "painting" in processed_data:
            result.append({
                "id": str(skin_idx),
                "original_id": ship_id,
                "name": processed_data["name"],
                "painting": processed_data["painting"]
            })
            skin_idx += 1
  
    print(f"[SUCCESS] skins 处理完成，生成皮肤: {len(result)}")
    return result

def process_words(words_data: Dict, code_mapping: Dict) -> Dict:
    print(f"[INFO] 开始处理 words，原始数据条目: {len(words_data)}")
    processed_words = {}
    for word_id, word_data in words_data.items():
        processed_data = replace_namecodes(word_data, code_mapping)
        processed_words[word_id] = {
            **processed_data,
            "linked_ship_id": word_id
        }
    print(f"[SUCCESS] words 处理完成，生成台词组: {len(processed_words)}")
    return processed_words

def generate_combined_data(ship_data: Dict, words_data: Dict, code_mapping: Dict) -> Dict:
    print("[INFO] 开始生成综合数据...")
    ships = process_ships(ship_data, code_mapping)
    skins = process_skins(ship_data, code_mapping)
    words = process_words(words_data, code_mapping)
  
    id_mapping = {
        "ship": {
            "id_to_id2": {s["id"]: s["id2"] for s in ships},
            "id2_to_id": {s["id2"]: s["id"] for s in ships}
        },
        "skin": {
            "id_to_original": {s["id"]: s["original_id"] for s in skins},
            "original_to_id": {s["original_id"]: s["id"] for s in skins}
        }
    }
  
    zuming_data = {
        "ships": [
            {
                "id": ship["id"],
                "name": ship["name"],
                "ship_group": ship["ship_group"]
            }
            for ship in ships
        ]
    }
  
    result = {
        "metadata": {
            "version": "3.1",
            "generate_time": datetime.now().isoformat(),
            "id_scheme": {
                "ships": "id=原始ID, id2=连续编号",
                "skins": "id=新编号, original_id=舰船原始ID",
                "words": "保留原始ID"
            }
        },
        "ships": ships,
        "skins": skins,
        "words": words,
        "id_mapping": id_mapping,
        "zuming_data": zuming_data
    }
  
    print(f"[SUCCESS] 综合数据生成完成，总大小约 {len(json.dumps(result)) // 1024} KB")
    return result

def convert_chat_language(data: Dict) -> Dict:
    result = {}
    for key, item in data.items():
        if isinstance(item, dict):
            result[key] = {
                "param": item.get("param", ""),
                "ship_group": item.get("ship_group", 0)
            }
    return result

def convert_skill_display(data: Dict) -> Dict:
    result = {}
    for key, item in data.items():
        if isinstance(item, dict):
            result[key] = {
                "name": item.get("name", "")
            }
    return result

def convert_activity_ship_group(data: Dict) -> Dict:
    result = {}
    for key, item in data.items():
        if isinstance(item, dict):
            result[key] = {
                "name": item.get("name", ""),
                "background": item.get("background", ""),
                "ship_group": item.get("ship_group", 0)
            }
    return result

def convert_skill_data(data: Dict) -> Dict:
    result = {}
    for key, item in data.items():
        if isinstance(item, dict):
            result[key] = {
                "name": item.get("name", ""),
                "desc": item.get("desc", ""),
                "desc_get": item.get("desc_get", "")
            }
    return result

def convert_ship_skin(data: Dict) -> Dict:
    result = {}
    for key, item in data.items():
        if isinstance(item, dict):
            result[key] = {
                "name": item.get("name", ""),
                "desc": item.get("desc", ""),
                "painting": item.get("painting", "")
            }
    return result

def convert_gametip(data: Dict) -> Dict:
    result = {}
    for key, item in data.items():
        if isinstance(item, dict):
            tip = item.get("tip", "")
            if isinstance(tip, list):
                tip = "\n".join([i.get("info", "") if isinstance(i, dict) else str(i) for i in tip])
            result[key] = str(tip)
    return result

def process_additional_files(code_mapping: Dict) -> Dict:
    print("[INFO] 开始处理额外配置...")
    config = {
        "chat_language": {},
        "skill_display": {},
        "activity_ship_group": {},
        "skill_data": {},
        "ship_skin": {},
        "gametip": {}
    }
    additional_files = {
        "chat_language": "activity_ins_chat_language.json",
        "skill_display": "skill_data_display.json",
        "ship_skin": "ship_skin_template.json",
        "activity_ship_group": "activity_ins_ship_group_template.json",
        "skill_data": "skill_data_template.json",
        "gametip": "gametip.json"
    }
    for config_key, filename in additional_files.items():
        file_path = find_data_file(filename)
        if file_path:
            print(f"[DEBUG] 加载额外文件: {filename}")
            data = load_json_file(file_path)
            converter = globals()[f"convert_{config_key}"]
            config[config_key] = converter(data)
            config[config_key] = replace_namecodes(config[config_key], code_mapping)
        else:
            print(f"[WARNING] 未找到额外文件: {filename}")
    print("[SUCCESS] 额外配置处理完成")
    return config

def split_main_lines(value):
    if not value:
        return []
    lines = [line.strip() for line in value.split("|") if line.strip()]
    return lines

def generate_skin_voice_mapping():
    print("[INFO] 开始生成 skin_voice_mapping_optimized.json")
    template_path = find_data_file("ship_skin_template.json")
    words_path = find_data_file("ship_skin_words.json")
   
    if not template_path:
        print("[ERROR] 未找到 ship_skin_template.json，跳过语音映射生成")
        return
    if not words_path:
        print("[ERROR] 未找到 ship_skin_words.json，跳过语音映射生成")
        return
   
    template = load_json_file(template_path)
    words = load_json_file(words_path)
    skins_by_group = defaultdict(list)
    for skin_id_str, info in template.items():
        ship_group = info.get("ship_group")
        if ship_group is None:
            continue
        group_index = info.get("group_index", 0)
        name = info.get("name", "未知皮肤")
        skins_by_group[str(ship_group)].append({
            "skin_id": str(skin_id_str),
            "group_index": group_index,
            "name": name
        })
    for group in skins_by_group:
        skins_by_group[group].sort(key=lambda x: x["group_index"])
    mapping = {}
    for ship_group, skin_list in skins_by_group.items():
        group_map = {}
        for skin in skin_list:
            skin_id = skin["skin_id"]
            group_index = skin["group_index"]
            name = skin["name"]
            if skin_id not in words:
                continue
            word_dict = words[skin_id]
            suffix = "" if group_index == 0 else f"_{group_index}"
            for key, value in word_dict.items():
                if not isinstance(value, str) or not value.strip():
                    continue
                if key.startswith("main"):
                    lines = split_main_lines(value)
                    for i, line in enumerate(lines, start=1):
                        full_key = f"main_{i}{suffix}"
                        group_map[full_key] = name
                    continue
                if key == "drop_descrip":
                    full_key_base = "get"
                elif key == "touch":
                    full_key_base = "touch_1"
                elif key == "touch2":
                    full_key_base = "touch_2"
                else:
                    full_key_base = key
                full_key = full_key_base + suffix
                group_map[full_key] = name
        mapping[ship_group] = group_map
    with open("skin_voice_mapping_optimized.json", "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=4)
    print(f"[SUCCESS] skin_voice_mapping_optimized.json 生成成功，大小约 {len(json.dumps(mapping)) // 1024} KB")

def generate_name_json(ships_data: List[Dict], painting_filter_data: Dict = None):
    print("[INFO] 开始生成 name.json")
    painting_filte_map = painting_filter_data or {}
   
    painting_lower_map = {}
    for key, value in painting_filte_map.items():
        painting_lower_map[key.lower()] = value
   
    name_data = {
        "ships": [
            {
                "name": ship["name"],
                "painting": ship["painting"],
                "res_list": painting_lower_map.get(ship["painting"].lower(), {}).get("res_list", [])
            }
            for ship in ships_data
        ]
    }
   
    with open("name.json", 'w', encoding='utf-8') as f:
        json.dump(name_data, f, ensure_ascii=False, indent=2)
    print(f"[SUCCESS] name.json 生成成功，包含 {len(ships_data)} 个舰船数据")

def main():
    print("=" * 70)
    print(f"[START] 脚本启动 | 时间: {datetime.now().isoformat()} | 环境: GitHub Actions")
    print("=" * 70)

    required_files = {
        "ships": "ship_skin_template.json",
        "words": "ship_skin_words.json",
        "namecode": "name_code.json"
    }
  
    loaded_data = {}
    missing_files = []
  
    for key, filename in required_files.items():
        file_path = find_data_file(filename)
        if file_path:
            loaded_data[key] = load_json_file(file_path)
        else:
            missing_files.append(filename)
            loaded_data[key] = {}
  
    if missing_files:
        print("[WARNING] 以下必需文件未找到:")
        for filename in missing_files:
            print(f"  - {filename}")
  
    print("\n[CHECK] 核心数据加载状态:")
    for key in ["ships", "words", "namecode"]:
        data = loaded_data.get(key, {})
        count = len(data)
        status = "OK" if count > 0 else "EMPTY"
        print(f"  {key:8}: {status} ({count} 条)")
  
    if loaded_data.get("ships") and loaded_data.get("words") and loaded_data.get("namecode"):
        print("\n[SUCCESS] 核心数据完整，开始生成主要文件...")
        combined = generate_combined_data(loaded_data["ships"], loaded_data["words"], loaded_data["namecode"])
        with open("al_combined_final.json", 'w', encoding='utf-8') as f:
            json.dump(combined, f, ensure_ascii=False, indent=2)
      
        with open("zuming.json", 'w', encoding='utf-8') as f:
            json.dump({"ships": combined["zuming_data"]["ships"]}, f, ensure_ascii=False, indent=2)
       
        painting_filter_path = find_data_file("painting_filte_map.json")
        painting_filter_data = {}
        if painting_filter_path:
            painting_filter_data = load_json_file(painting_filter_path)
            print(f"[INFO] 已加载 painting_filte_map.json，包含 {len(painting_filter_data)} 个资源映射")
        else:
            print("[WARNING] 未找到 painting_filte_map.json，生成的 name.json 中将不包含 res_list 字段")
       
        generate_name_json(combined["ships"], painting_filter_data)
      
        print(f"[SUMMARY] 生成成功！")
        print(f"  舰船数量: {len(combined['ships'])}")
        print(f"  皮肤数量: {len(combined['skins'])}")
        print(f"  台词数量: {len(combined['words'])}")
        print(f"  zuming.json 包含舰船: {len(combined['zuming_data']['ships'])}")
    else:
        print("\n[ERROR] 缺少必需文件，无法生成主数据文件")
        print("请检查上面 [CHECK] 部分，哪个数据为空？")
  
    if loaded_data.get("namecode"):
        additional_config = process_additional_files(loaded_data["namecode"])
        with open("文本配置.json", 'w', encoding='utf-8') as f:
            json.dump(additional_config, f, ensure_ascii=False, indent=2, sort_keys=True)
      
        print("[SUCCESS] 额外配置处理完成，生成 文本配置.json")
    else:
        print("[WARNING] 缺少name_code.json文件，跳过额外配置处理")

    generate_skin_voice_mapping()

    print("\n" + "=" * 70)
    print("[END] 脚本运行结束")
    print("=" * 70)

if __name__ == "__main__":
    main()
