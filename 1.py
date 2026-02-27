import json
from collections import defaultdict
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import re

def find_data_file(filename: str, search_paths: List[Path] = None) -> Path:
    if search_paths is None:
        search_paths = [
            Path("."),
            Path("sharecfgdata"),
            Path("raw-data/CN/sharecfgdata"),
            Path("ShareCfg"),
            Path("raw-data/CN/ShareCfg"),
            Path("GameCfg")
        ]
    found_paths = []
    for path in search_paths:
        file_path = path / filename
        if file_path.exists():
            found_paths.append(file_path)
    if not found_paths:
        return None
    preferred_paths = [p for p in found_paths if "sharecfgdata" in str(p).lower()]
    if preferred_paths:
        return preferred_paths[0]
    return found_paths[0]

def load_json_file(file_path: Path) -> Dict:
    if not file_path:
        return {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            raw = f.read().strip()
            data = json.loads(raw)
            if isinstance(data, dict):
                return data
            if isinstance(data, list):
                converted = {}
                for item in data:
                    if isinstance(item, dict):
                        key = item.get("id") or item.get("skin_id") or item.get("ship_skin_id") or item.get("key")
                        if key is not None:
                            converted[str(key)] = item
                return converted
            return {}
    except Exception as e:
        print(f"加载文件错误 {file_path}: {str(e)}")
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
        result.append({
            "id": ship_id,
            "id2": str(idx),
            "name": processed_data.get("name", ""),
            "ship_group": ship_group,
            "painting": processed_data.get("painting", "")
        })
    return result

def process_skins(original_data: Dict, code_mapping: Dict) -> List[Dict]:
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
    return result

def process_words(words_data: Dict, code_mapping: Dict) -> Dict:
    processed_words = {}
    for word_id, word_data in words_data.items():
        processed_data = replace_namecodes(word_data, code_mapping)
        processed_words[word_id] = {
            **processed_data,
            "linked_ship_id": word_id
        }
    return processed_words

def generate_combined_data(ship_data: Dict, words_data: Dict, code_mapping: Dict) -> Dict:
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
    return {
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

def generate_skin_voice_mapping():
    template_path = find_data_file("ship_skin_template.json")
    words_path = find_data_file("ship_skin_words.json")
    if not template_path:
        print("错误: 未找到 ship_skin_template.json，跳过生成 skin_voice_mapping_optimized.json")
        return
    if not words_path:
        print("错误: 未找到 ship_skin_words.json，跳过生成 skin_voice_mapping_optimized.json")
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
    print("skin_voice_mapping_optimized.json 生成成功")

def split_main_lines(value):
    if not value:
        return []
    lines = [line.strip() for line in value.split("|") if line.strip()]
    return lines

def generate_name_json(ships_data: List[Dict], painting_filter_data: Dict = None):
    painting_filter_map = painting_filter_data or {}
    painting_lower_map = {}
    for key, value in painting_filter_map.items():
        painting_lower_map[key.lower()] = value
    name_data = {
        "ships": [
            {
                "name": ship["name"],
                "painting": ship["painting"],
                "ship_group": ship.get("ship_group", ""),
                "res_list": painting_lower_map.get(ship["painting"].lower(), {}).get("res_list", [])
            }
            for ship in ships_data
        ]
    }
    with open("name.json", 'w', encoding='utf-8') as f:
        json.dump(name_data, f, ensure_ascii=False, indent=2)
    print(f"name.json 生成成功！包含 {len(ships_data)} 个舰船数据")

def generate_story_dialogues():
    story_path = find_data_file("story.json")
    memory_template_path = find_data_file("memory_template.json")
    memory_group_path = find_data_file("memory_group.json")
    name_code_path = find_data_file("name_code.json")

    if not all([story_path, memory_template_path, memory_group_path, name_code_path]):
        print("缺少必要的剧情文件，跳过生成 story_dialogues_structured.json")
        return

    story = load_json_file(story_path)
    mem_temp = load_json_file(memory_template_path)
    mem_group = load_json_file(memory_group_path)
    namecode = load_json_file(name_code_path)

    story_to_title = {}
    for tid, item in mem_temp.items():
        sk = item.get("story")
        if sk:
            story_to_title[sk.upper()] = item.get("title", "未知标题")

    memory_to_group = {}
    for gid, group in mem_group.items():
        title = group.get("title", "未知组")
        memories = group.get("memories", [])
        for mid in memories:
            memory_to_group[str(mid)] = title

    structured_output = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "version": "1.0",
            "description": "碧蓝航线剧情对话 - 已替换namecode，按数字顺序排序，只包含纯对话文本"
        },
        "groups": []
    }

    group_episodes = defaultdict(list)

    for key_lower, content in story.items():
        key_upper = key_lower.upper()

        scripts_raw = content.get("scripts", content) if isinstance(content, dict) else content

        dialogues = []
        if isinstance(scripts_raw, dict):
            try:
                sorted_keys = sorted(scripts_raw.keys(), key=lambda k: int(k) if k.isdigit() else 999999)
                for k in sorted_keys:
                    s = scripts_raw.get(k)
                    if isinstance(s, dict) and "say" in s and s["say"]:
                        say_text = replace_namecodes(s["say"], namecode)
                        dialogues.append(say_text)
            except Exception as e:
                print(f"处理 {key_lower} scripts 失败: {e}")
        elif isinstance(scripts_raw, list):
            for s in scripts_raw:
                if isinstance(s, dict) and "say" in s and s["say"]:
                    say_text = replace_namecodes(s["say"], namecode)
                    dialogues.append(say_text)

        if not dialogues:
            continue

        title = story_to_title.get(key_upper, f"[{key_lower}]")
        memory_id = None
        group_title = "未分组剧情"

        for tid, tmp in mem_temp.items():
            if tmp.get("story", "").upper() == key_upper:
                memory_id = tid
                if title.startswith("["):
                    title = tmp.get("title", title)
                break

        if memory_id and str(memory_id) in memory_to_group:
            group_title = memory_to_group[str(memory_id)]

        group_episodes[group_title].append({
            "story_key": key_lower,
            "episode_title": title,
            "memory_id": memory_id,
            "dialogues": dialogues
        })

    for group_name in sorted(group_episodes.keys()):
        episodes = sorted(group_episodes[group_name], key=lambda x: x["story_key"])
        structured_output["groups"].append({
            "group_title": group_name,
            "episodes": episodes
        })

    output_path = Path("story_dialogues_structured.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(structured_output, f, ensure_ascii=False, indent=2)

    print(f"已生成 {output_path} （分组、标题、数字排序、纯对话已处理完成）")

def main():
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
            data = load_json_file(file_path)
            if key == "words" and "ShareCfg" in str(file_path) and not "sharecfgdata" in str(file_path).lower():
                alt_path = Path("sharecfgdata") / filename
                if alt_path.exists():
                    print(f"检测到 ShareCfg 中的 words，切换到 sharecfgdata: {alt_path}")
                    data = load_json_file(alt_path)
            loaded_data[key] = data
        else:
            missing_files.append(filename)
            loaded_data[key] = {}
    if missing_files:
        print("警告: 以下必需文件未找到:")
        for filename in missing_files:
            print(f"- {filename}")
    if loaded_data["ships"] and loaded_data["namecode"]:
        combined = generate_combined_data(loaded_data["ships"], loaded_data["words"], loaded_data["namecode"])
        with open("al_combined_final.json", 'w', encoding='utf-8') as f:
            json.dump(combined, f, ensure_ascii=False, indent=2)
        with open("zuming.json", 'w', encoding='utf-8') as f:
            json.dump({"ships": combined["zuming_data"]["ships"]}, f, ensure_ascii=False, indent=2)
        painting_filter_path = find_data_file("painting_filte_map.json")
        painting_filter_data = {}
        if painting_filter_path:
            painting_filter_data = load_json_file(painting_filter_path)
            print(f"已加载 painting_filte_map.json，包含 {len(painting_filter_data)} 个资源映射")
        else:
            print("警告: 未找到 painting_filte_map.json，生成的 name.json 中将不包含 res_list 字段")
        generate_name_json(combined["ships"], painting_filter_data)
        print(f"生成成功！包含：{len(combined['ships'])}舰船, {len(combined['skins'])}皮肤, {len(combined['words'])}台词")
        print(f"同时生成了zuming.json，包含{len(combined['zuming_data']['ships'])}舰船数据")
    else:
        print("错误: 缺少 ships 或 namecode，无法生成主数据文件")
    generate_skin_voice_mapping()

    generate_story_dialogues()

if __name__ == "__main__":
    main()
