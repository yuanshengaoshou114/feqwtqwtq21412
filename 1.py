import json
from collections import defaultdict
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import re

def convert_name_code(content):
    result = {}
    pattern = r'pg\.base\.name_code\[(\d+)\]\s*=\s*\{([^}]+)\}'
    
    for match in re.finditer(pattern, content):
        code_id = match.group(1)
        table_content = match.group(2)
        
        code_data = {}
        field_pattern = r'(\w+)\s*=\s*("([^"]*)"|(\d+))'
        
        for field_match in re.finditer(field_pattern, table_content):
            key = field_match.group(1)
            str_value = field_match.group(3)
            int_value = field_match.group(4)
            
            if str_value is not None:
                code_data[key] = str_value
            else:
                code_data[key] = int(int_value)
        
        result[code_id] = code_data
    return result

def replace_namecode_in_string(value, namecode_map):
    if not isinstance(value, str):
        return value
    pattern = r'{namecode:(\d+)(?::[^}]*)?}'
    def replace_match(match):
        code = match.group(1)
        if code in namecode_map:
            return namecode_map[code].get('name', match.group(0))
        return match.group(0)
    return re.sub(pattern, replace_match, value)

def convert_ship_skin_template(content, namecode_map=None):
    result = {}
    pattern = r'_G\.pg\.base\.ship_skin_template\[(\d+)\]\s*=\s*(\{(?:[^{}]|\{[^{}]*\})*\})'
    
    for match in re.finditer(pattern, content, re.DOTALL):
        skin_id = match.group(1)
        table_content = match.group(2)
        
        skin_data = {}
        kv_pattern = r'(\w+)\s*=\s*("[^"\\]*(?:\\.[^"\\]*)*"|true|false|\{[^{}]*\}|-?\d+(?:\.\d+)?|[\w_]+)'
        
        for kv_match in re.finditer(kv_pattern, table_content):
            key = kv_match.group(1)
            value_str = kv_match.group(2)
            
            if value_str.startswith('"'):
                value = value_str[1:-1].replace('\\"', '"')
                if namecode_map:
                    value = replace_namecode_in_string(value, namecode_map)
            elif value_str == 'true':
                value = True
            elif value_str == 'false':
                value = False
            elif value_str.isdigit():
                value = int(value_str)
            elif value_str.startswith('-') and value_str[1:].isdigit():
                value = int(value_str)
            elif '.' in value_str and value_str.replace('.', '').isdigit():
                value = float(value_str)
            elif value_str.startswith('{'):
                arr = re.findall(r'"([^"]*)"|(\d+)', value_str)
                value = [item[0] if item[0] else int(item[1]) for item in arr if item[0] or item[1]]
                if namecode_map and isinstance(value, list):
                    value = [replace_namecode_in_string(v, namecode_map) if isinstance(v, str) else v for v in value]
            else:
                value = value_str
                if namecode_map and isinstance(value, str):
                    value = replace_namecode_in_string(value, namecode_map)
            skin_data[key] = value
        
        result[skin_id] = skin_data
    return result

def convert_ship_skin_words(content, namecode_map=None):
    result = {}
    pattern = r'_G\.pg\.base\.ship_skin_words\[(\d+)\]\s*=\s*(\{(?:[^{}]|\{[^{}]*\})*\})'
    
    for match in re.finditer(pattern, content, re.DOTALL):
        skin_id = match.group(1)
        table_content = match.group(2)
        
        words_data = {}
        kv_pattern = r'(\w+)\s*=\s*((?:"[^"\\]*(?:\\.[^"\\]*)*")|(?:{[^{}]*})|(?:\[[^\]]*\])|(?:true|false)|(?:-?\d+(?:\.\d+)?)|(?:[\w_]+))'
        
        for kv_match in re.finditer(kv_pattern, table_content):
            key = kv_match.group(1)
            value_str = kv_match.group(2).strip()
            
            if value_str.startswith('"'):
                value = value_str[1:-1].replace('\\"', '"').replace('\\n', '\n')
                if namecode_map:
                    value = replace_namecode_in_string(value, namecode_map)
            elif value_str == 'true':
                value = True
            elif value_str == 'false':
                value = False
            elif value_str.isdigit():
                value = int(value_str)
            elif value_str.startswith('-') and value_str[1:].isdigit():
                value = int(value_str)
            elif value_str.startswith('{'):
                arr = re.findall(r'"([^"]*)"|(\d+)', value_str)
                value = [item[0] if item[0] else int(item[1]) for item in arr if item[0] or item[1]]
                if namecode_map and isinstance(value, list):
                    value = [replace_namecode_in_string(v, namecode_map) if isinstance(v, str) else v for v in value]
            elif value_str.startswith('['):
                value = value_str
            else:
                value = value_str
                if namecode_map and isinstance(value, str):
                    value = replace_namecode_in_string(value, namecode_map)
            words_data[key] = value
        
        result[skin_id] = words_data
    return result

def convert_painting_filte_map(content, namecode_map=None):
    result = {}
    
    pattern1 = r'pg\.base\.painting_filte_map\["([^"]+)"\]\s*=\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}'
    for match in re.finditer(pattern1, content, re.DOTALL):
        key = match.group(1)
        table_content = match.group(2)
        
        item_data = {}
        key_match = re.search(r'key\s*=\s*"([^"]*)"', table_content)
        if key_match:
            val = key_match.group(1)
            if namecode_map:
                val = replace_namecode_in_string(val, namecode_map)
            item_data["key"] = val
        
        res_list_match = re.search(r'res_list\s*=\s*\{([^}]+)\}', table_content)
        if res_list_match:
            res_list = re.findall(r'"([^"]*)"', res_list_match.group(1))
            if res_list:
                if namecode_map:
                    res_list = [replace_namecode_in_string(r, namecode_map) for r in res_list]
                item_data["res_list"] = res_list
        
        if item_data:
            if namecode_map:
                key = replace_namecode_in_string(key, namecode_map)
            result[key] = item_data
    
    pattern2 = r'pg\.base\.painting_filte_map\.([a-zA-Z0-9_]+)\s*=\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}'
    for match in re.finditer(pattern2, content, re.DOTALL):
        key = match.group(1)
        table_content = match.group(2)
        
        item_data = {}
        key_match = re.search(r'key\s*=\s*"([^"]*)"', table_content)
        if key_match:
            val = key_match.group(1)
            if namecode_map:
                val = replace_namecode_in_string(val, namecode_map)
            item_data["key"] = val
        
        res_list_match = re.search(r'res_list\s*=\s*\{([^}]+)\}', table_content)
        if res_list_match:
            res_list = re.findall(r'"([^"]*)"', res_list_match.group(1))
            if res_list:
                if namecode_map:
                    res_list = [replace_namecode_in_string(r, namecode_map) for r in res_list]
                item_data["res_list"] = res_list
        
        if item_data:
            result[key] = item_data
    
    return result

def convert_ship_skin_expression(content, namecode_map=None):
    result = {}
    pattern = r'pg\.base\.ship_skin_expression\.([a-zA-Z0-9_]+)\s*=\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}'
    
    for match in re.finditer(pattern, content, re.DOTALL):
        key = match.group(1)
        table_content = match.group(2)
        
        expression_data = {}
        field_pattern = r'(\w+)\s*=\s*("([^"]*)"|(\d+))'
        
        for field_match in re.finditer(field_pattern, table_content):
            field_name = field_match.group(1)
            str_value = field_match.group(3)
            int_value = field_match.group(4)
            
            if str_value is not None:
                value = str_value
                if namecode_map:
                    value = replace_namecode_in_string(value, namecode_map)
                expression_data[field_name] = value
            else:
                expression_data[field_name] = int(int_value)
        
        if expression_data:
            result[key] = expression_data
    
    return result

def convert_lua_files_to_json(lua_files_dir: Path = Path(".")):
    namecode_path = lua_files_dir / "name_code.lua"
    if not namecode_path.exists():
        print("错误: name_code.lua 不存在，无法进行名称替换")
        return {}
    
    with open(namecode_path, 'r', encoding='utf-8') as f:
        namecode_content = f.read()
    
    namecode_map = convert_name_code(namecode_content)
    print(f"加载 name_code: {len(namecode_map)} 条数据")
    
    converters = {
        "ship_skin_template.lua": ("ship_skin_template.json", convert_ship_skin_template),
        "ship_skin_words.lua": ("ship_skin_words.json", convert_ship_skin_words),
        "painting_filte_map.lua": ("painting_filte_map.json", convert_painting_filte_map),
        "ship_skin_expression.lua": ("ship_skin_expression.json", convert_ship_skin_expression)
    }
    
    converted_files = {}
    for input_file, (output_file, converter) in converters.items():
        input_path = lua_files_dir / input_file
        if not input_path.exists():
            print(f"跳过: {input_file} 不存在")
            continue
        
        print(f"转换: {input_file} -> {output_file}")
        
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        result = converter(content, namecode_map)
        
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"  ✓ 成功转换 {len(result)} 条数据")
        converted_files[output_file.replace('.json', '')] = output_path
    
    print("\n所有Lua文件转换完成！")
    return converted_files

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
    except:
        return {}

def replace_namecodes(data: Any, code_mapping: Dict) -> Any:
    def replace_match(match):
        code = match.group(1)
        return code_mapping.get(code, {}).get('name', match.group(0))
    pattern = r'{namecode:(\d+)(?::[^}]*)?}'
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
    
    ships_by_name = defaultdict(list)
    for ship in ships:
        ships_by_name[ship["name"]].append(ship)
    
    unique_ships = []
    ship_skin_counts = {}
    for ship in ships:
        skin_count = len([s for s in skins if s["original_id"] == ship["id"]])
        ship_skin_counts[ship["id"]] = skin_count
    
    for name, ship_list in ships_by_name.items():
        if len(ship_list) == 1:
            unique_ships.append(ship_list[0])
        else:
            best_ship = None
            best_skin_count = -1
            for ship in ship_list:
                skin_count = ship_skin_counts.get(ship["id"], 0)
                if skin_count > best_skin_count:
                    best_ship = ship
                    best_skin_count = skin_count
                elif skin_count == best_skin_count:
                    if not ship["painting"].startswith("npc") and best_ship and best_ship["painting"].startswith("npc"):
                        best_ship = ship
            if best_ship:
                unique_ships.append(best_ship)
    
    unique_skin_ids = {ship["id"] for ship in unique_ships}
    unique_skins = [skin for skin in skins if skin["original_id"] in unique_skin_ids]
    
    unique_words = {}
    for word_id, word_data in words.items():
        linked_ship_id = word_data.get("linked_ship_id")
        if linked_ship_id in unique_skin_ids:
            unique_words[word_id] = word_data
    
    id_mapping = {
        "ship": {
            "id_to_id2": {s["id"]: s["id2"] for s in unique_ships},
            "id2_to_id": {s["id2"]: s["id"] for s in unique_ships}
        },
        "skin": {
            "id_to_original": {s["id"]: s["original_id"] for s in unique_skins},
            "original_to_id": {s["original_id"]: s["id"] for s in unique_skins}
        }
    }
    zuming_data = {
        "ships": [
            {
                "id": ship["id"],
                "name": ship["name"],
                "ship_group": ship["ship_group"]
            }
            for ship in unique_ships
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
        "ships": unique_ships,
        "skins": unique_skins,
        "words": unique_words,
        "id_mapping": id_mapping,
        "zuming_data": zuming_data
    }

def generate_skin_voice_mapping():
    template_path = find_data_file("ship_skin_template.json") or Path("ship_skin_template.json")
    words_path = find_data_file("ship_skin_words.json") or Path("ship_skin_words.json")
    
    if not template_path.exists() or not words_path.exists():
        print("跳过 skin_voice_mapping: 文件不存在")
        return
    
    template = load_json_file(template_path)
    words = load_json_file(words_path)
    
    if not template or not words:
        print("跳过 skin_voice_mapping: 数据为空")
        return
    
    ships_by_name = defaultdict(list)
    for skin_id_str, info in template.items():
        name = info.get("name", "未知皮肤")
        ships_by_name[name].append((skin_id_str, info))
    
    ship_groups_to_keep = set()
    for name, ship_list in ships_by_name.items():
        if len(ship_list) == 1:
            for skin_id_str, info in ship_list:
                ship_groups_to_keep.add(str(info.get("ship_group")))
        else:
            best_info = None
            best_skin_count = -1
            for skin_id_str, info in ship_list:
                skin_count = len([s for s in template.values() if s.get("ship_group") == info.get("ship_group")])
                if skin_count > best_skin_count:
                    best_info = info
                    best_skin_count = skin_count
                elif skin_count == best_skin_count:
                    if best_info and best_info.get("painting", "").startswith("npc") and not info.get("painting", "").startswith("npc"):
                        best_info = info
            if best_info:
                ship_groups_to_keep.add(str(best_info.get("ship_group")))
    
    skins_by_group = defaultdict(list)
    for skin_id_str, info in template.items():
        ship_group = info.get("ship_group")
        if ship_group is None:
            continue
        if str(ship_group) not in ship_groups_to_keep:
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
    
    ships_by_name = defaultdict(list)
    for ship in ships_data:
        ships_by_name[ship["name"]].append(ship)
    
    unique_ships = []
    for name, ship_list in ships_by_name.items():
        if len(ship_list) == 1:
            unique_ships.append(ship_list[0])
        else:
            ship_with_skins = None
            for ship in ship_list:
                painting = ship["painting"]
                skin_count = len(painting_lower_map.get(painting.lower(), {}).get("res_list", []))
                if ship_with_skins is None:
                    ship_with_skins = (ship, skin_count)
                else:
                    if skin_count > ship_with_skins[1]:
                        ship_with_skins = (ship, skin_count)
                    elif skin_count == ship_with_skins[1]:
                        if not ship["painting"].startswith("npc") and ship_with_skins[0]["painting"].startswith("npc"):
                            ship_with_skins = (ship, skin_count)
            unique_ships.append(ship_with_skins[0])
    
    name_data = {
        "ships": [
            {
                "name": ship["name"],
                "painting": ship["painting"],
                "ship_group": ship.get("ship_group", ""),
                "res_list": painting_lower_map.get(ship["painting"].lower(), {}).get("res_list", [])
            }
            for ship in unique_ships
        ]
    }
    with open("name.json", 'w', encoding='utf-8') as f:
        json.dump(name_data, f, ensure_ascii=False, indent=2)

def generate_story_dialogues():
    story_path = find_data_file("story.json")
    memory_template_path = find_data_file("memory_template.json")
    memory_group_path = find_data_file("memory_group.json")
    name_code_path = find_data_file("name_code.json") or Path("name_code.json")
    
    if not name_code_path.exists():
        print("跳过 story_dialogues: name_code.json 不存在")
        return
    
    namecode = load_json_file(name_code_path)
    
    if story_path and story_path.exists():
        story = load_json_file(story_path)
    else:
        story = {}
    
    if memory_template_path and memory_template_path.exists():
        mem_temp = load_json_file(memory_template_path)
    else:
        mem_temp = {}
    
    if memory_group_path and memory_group_path.exists():
        mem_group = load_json_file(memory_group_path)
    else:
        mem_group = {}
    
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
            except:
                pass
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
        group_title = replace_namecodes(group_title, namecode)
        title = replace_namecodes(title, namecode)
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

def main():
    print("=" * 50)
    print("步骤1: 转换Lua文件为JSON（同时替换namecode）")
    print("=" * 50)
    convert_lua_files_to_json(Path("."))
    
    print("\n" + "=" * 50)
    print("步骤2: 处理JSON数据")
    print("=" * 50)
    
    required_files = {
        "ships": "ship_skin_template.json",
        "words": "ship_skin_words.json",
        "namecode": "name_code.json"
    }
    
    loaded_data = {}
    for key, filename in required_files.items():
        file_path = Path(filename)
        if not file_path.exists():
            file_path = find_data_file(filename)
        if file_path and file_path.exists():
            data = load_json_file(file_path)
            loaded_data[key] = data
            print(f"加载 {filename}: {len(data)} 条数据")
        else:
            print(f"警告: {filename} 未找到")
            loaded_data[key] = {}
    
    if loaded_data["ships"] and loaded_data["namecode"]:
        combined = generate_combined_data(loaded_data["ships"], loaded_data["words"], loaded_data["namecode"])
        with open("al_combined_final.json", 'w', encoding='utf-8') as f:
            json.dump(combined, f, ensure_ascii=False, indent=2)
        print("生成 al_combined_final.json 完成")
        
        with open("zuming.json", 'w', encoding='utf-8') as f:
            json.dump({"ships": combined["zuming_data"]["ships"]}, f, ensure_ascii=False, indent=2)
        print("生成 zuming.json 完成")
        
        painting_filter_path = find_data_file("painting_filte_map.json") or Path("painting_filte_map.json")
        painting_filter_data = {}
        if painting_filter_path.exists():
            painting_filter_data = load_json_file(painting_filter_path)
            print(f"加载 painting_filte_map.json: {len(painting_filter_data)} 条数据")
        
        generate_name_json(combined["ships"], painting_filter_data)
        print("生成 name.json 完成")
    else:
        print("缺少必要数据，跳过部分处理")
    
    print("\n" + "=" * 50)
    print("步骤3: 生成附加数据")
    print("=" * 50)
    generate_skin_voice_mapping()
    generate_story_dialogues()
    
    print("\n" + "=" * 50)
    print("所有处理完成！")
    print("=" * 50)

if __name__ == "__main__":
    main()
