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
    except:
        return {}

def convert_ship_skin_template(content: str) -> Dict:
    result = {}
    pattern = r'_G\.pg\.base\.ship_skin_template\[(\d+)\]\s*=\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}'
    
    for match in re.finditer(pattern, content, re.DOTALL):
        skin_id = match.group(1)
        table_content = match.group(2)
        
        skin_data = {}
        kv_pattern = r'(\w+)\s*=\s*("[^"\\]*(?:\\.[^"\\]*)*"|true|false|\{[^}]*\}|-?\d+(?:\.\d+)?|[\w_]+)'
        
        for kv_match in re.finditer(kv_pattern, table_content):
            key = kv_match.group(1)
            value_str = kv_match.group(2)
            
            if value_str.startswith('"'):
                value = value_str[1:-1].replace('\\"', '"')
            elif value_str == 'true':
                value = True
            elif value_str == 'false':
                value = False
            elif value_str.isdigit():
                value = int(value_str)
            elif value_str.startswith('-') and value_str[1:].isdigit():
                value = int(value_str)
            elif '.' in value_str and value_str.replace('.', '').replace('-', '').isdigit():
                value = float(value_str)
            else:
                value = value_str
            skin_data[key] = value
        
        result[skin_id] = skin_data
    return result

def convert_ship_skin_words(content: str) -> Dict:
    result = {}
    pattern = r'_G\.pg\.base\.ship_skin_words\[(\d+)\]\s*=\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}'
    
    for match in re.finditer(pattern, content, re.DOTALL):
        skin_id = match.group(1)
        table_content = match.group(2)
        
        words_data = {}
        kv_pattern = r'(\w+)\s*=\s*((?:"[^"\\]*(?:\\.[^"\\]*)*")|(?:{[^}]*})|(?:\[[^\]]*\])|(?:true|false)|(?:-?\d+(?:\.\d+)?)|(?:[\w_]+))'
        
        for kv_match in re.finditer(kv_pattern, table_content):
            key = kv_match.group(1)
            value_str = kv_match.group(2).strip()
            
            if value_str.startswith('"'):
                value = value_str[1:-1].replace('\\"', '"').replace('\\n', '\n')
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
            else:
                value = value_str
            words_data[key] = value
        
        result[skin_id] = words_data
    return result

def convert_name_code(content: str) -> Dict:
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

def convert_painting_filte_map(content: str) -> Dict:
    result = {}
    
    pattern1 = r'pg\.base\.painting_filte_map\["([^"]+)"\]\s*=\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}'
    for match in re.finditer(pattern1, content, re.DOTALL):
        key = match.group(1)
        table_content = match.group(2)
        
        item_data = {}
        key_match = re.search(r'key\s*=\s*"([^"]*)"', table_content)
        if key_match:
            item_data["key"] = key_match.group(1)
        
        res_list_match = re.search(r'res_list\s*=\s*\{([^}]+)\}', table_content)
        if res_list_match:
            res_list = re.findall(r'"([^"]*)"', res_list_match.group(1))
            if res_list:
                item_data["res_list"] = res_list
        
        if item_data:
            result[key] = item_data
    
    pattern2 = r'pg\.base\.painting_filte_map\.([a-zA-Z0-9_]+)\s*=\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}'
    for match in re.finditer(pattern2, content, re.DOTALL):
        key = match.group(1)
        table_content = match.group(2)
        
        item_data = {}
        key_match = re.search(r'key\s*=\s*"([^"]*)"', table_content)
        if key_match:
            item_data["key"] = key_match.group(1)
        
        res_list_match = re.search(r'res_list\s*=\s*\{([^}]+)\}', table_content)
        if res_list_match:
            res_list = re.findall(r'"([^"]*)"', res_list_match.group(1))
            if res_list:
                item_data["res_list"] = res_list
        
        if item_data:
            result[key] = item_data
    
    return result

def convert_ship_skin_expression(content: str) -> Dict:
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
                expression_data[field_name] = str_value
            else:
                expression_data[field_name] = int_value
        
        if expression_data:
            result[key] = expression_data
    
    return result

def load_lua_or_json(filename: str) -> Dict:
    lua_filename = filename.replace('.json', '.lua')
    lua_path = find_data_file(lua_filename)
    
    if lua_path and lua_path.exists():
        print(f"从Lua加载: {lua_filename}")
        with open(lua_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'ship_skin_template' in lua_filename:
            return convert_ship_skin_template(content)
        elif 'ship_skin_words' in lua_filename:
            return convert_ship_skin_words(content)
        elif 'name_code' in lua_filename:
            return convert_name_code(content)
        elif 'painting_filte_map' in lua_filename:
            return convert_painting_filte_map(content)
        elif 'ship_skin_expression' in lua_filename:
            return convert_ship_skin_expression(content)
    
    json_path = find_data_file(filename)
    if json_path:
        print(f"从JSON加载: {filename}")
        return load_json_file(json_path)
    
    print(f"警告: {filename} 未找到")
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

def split_main_lines(value):
    if not value:
        return []
    lines = [line.strip() for line in value.split("|") if line.strip()]
    return lines

def generate_skin_voice_mapping():
    template = load_lua_or_json("ship_skin_template.json")
    words = load_lua_or_json("ship_skin_words.json")
    if not template or not words:
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
    namecode = load_lua_or_json("name_code.json")
    if not all([story_path, memory_template_path, memory_group_path, namecode]):
        return
    story = load_json_file(story_path)
    mem_temp = load_json_file(memory_template_path)
    mem_group = load_json_file(memory_group_path)
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
    ship_data = load_lua_or_json("ship_skin_template.json")
    words_data = load_lua_or_json("ship_skin_words.json")
    namecode_data = load_lua_or_json("name_code.json")
    
    if ship_data and namecode_data:
        combined = generate_combined_data(ship_data, words_data, namecode_data)
        with open("al_combined_final.json", 'w', encoding='utf-8') as f:
            json.dump(combined, f, ensure_ascii=False, indent=2)
        with open("zuming.json", 'w', encoding='utf-8') as f:
            json.dump({"ships": combined["zuming_data"]["ships"]}, f, ensure_ascii=False, indent=2)
        
        painting_filter_data = load_lua_or_json("painting_filte_map.json")
        generate_name_json(combined["ships"], painting_filter_data)
    
    generate_skin_voice_mapping()
    generate_story_dialogues()

if __name__ == "__main__":
    main()
