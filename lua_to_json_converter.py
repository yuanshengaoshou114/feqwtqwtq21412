import re
import json
from pathlib import Path

def convert_ship_skin_template(content):
    """转换 ship_skin_template.lua"""
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
            elif '.' in value_str and value_str.replace('.', '').isdigit():
                value = float(value_str)
            else:
                value = value_str
            skin_data[key] = value
        
        result[skin_id] = skin_data
    return result

def convert_ship_skin_words(content):
    """转换 ship_skin_words.lua"""
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

def convert_name_code(content):
    """转换 name_code.lua"""
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

def convert_painting_filte_map(content):
    """转换 painting_filte_map.lua"""
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

def convert_ship_skin_expression(content):
    """转换 ship_skin_expression.lua"""
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

def main():
    lua_root = Path("lua-data")
    json_root = Path(".")
    
    converters = {
        "ship_skin_template.lua": convert_ship_skin_template,
        "ship_skin_words.lua": convert_ship_skin_words,
        "name_code.lua": convert_name_code,
        "painting_filte_map.lua": convert_painting_filte_map,
        "ship_skin_expression.lua": convert_ship_skin_expression,
    }
    
    for lua_file_path in lua_root.rglob("*.lua"):
        if lua_file_path.name in converters:
            rel_path = lua_file_path.relative_to(lua_root)
            json_file_path = json_root / rel_path.with_suffix(".json")
            
            json_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(lua_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            converter = converters[lua_file_path.name]
            result = converter(content)
            
            with open(json_file_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print(f"转换: {lua_file_path} -> {json_file_path}")

if __name__ == "__main__":
    main()
