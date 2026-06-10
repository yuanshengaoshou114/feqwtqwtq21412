import json
from pathlib import Path

def main():
    # 读取已经转换好的 JSON
    with open("ship_data_statistics.json", "r", encoding="utf-8") as f:
        ship_data = json.load(f)
    
    config_ids = []
    
    for ship_id_str, ship_info in ship_data.items():
        ship_id = int(ship_id_str)
        
        if ship_id % 10 != 1:
            continue
        
        skin_id = ship_info.get("skin_id")
        if skin_id is None or int(skin_id) != ship_id - 1:
            continue
        
        attrs = ship_info.get("attrs")
        if not attrs:
            continue
        
        has_positive = False
        for v in attrs.values():
            try:
                if float(v) > 0:
                    has_positive = True
                    break
            except:
                continue
        
        if has_positive:
            config_ids.append(ship_id)
    
    config_ids.sort()
    
    with open("fake_ship_config.txt", "w", encoding="utf-8") as f:
        for config_id in config_ids:
            f.write(str(config_id) + "\n")
    
    print(f"找到 {len(config_ids)} 个，已写入 fake_ship_config.txt")

if __name__ == "__main__":
    main()
