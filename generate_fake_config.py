import json
from pathlib import Path
from typing import Dict

def generate_fake_ship_config(ship_data: Dict) -> None:
    """生成 fake_ship_config.txt
    筛选条件：
    1. 舰船 ID 尾号为 1
    2. skin_id = id - 1
    3. 至少有一个 attrs 属性值大于 0
    """
    print("生成 fake_ship_config.txt...")
    
    config_ids = []
    stats = {"total": 0, "tail1": 0, "skin_id_match": 0, "has_positive": 0}
    
    for ship_id_str, ship_info in ship_data.items():
        try:
            ship_id = int(ship_id_str)
        except (ValueError, TypeError):
            continue
        
        stats["total"] += 1
        
        if ship_id % 10 != 1:
            continue
        stats["tail1"] += 1
        
        skin_id = ship_info.get("skin_id")
        if skin_id is None:
            continue
        
        if int(skin_id) != ship_id - 1:
            continue
        stats["skin_id_match"] += 1
        
        attrs = ship_info.get("attrs")
        if not isinstance(attrs, dict):
            continue
        
        has_positive_attr = False
        for attr_key, attr_value in attrs.items():
            try:
                numeric_value = float(attr_value) if isinstance(attr_value, (int, float, str)) else None
                if numeric_value is not None and numeric_value > 0:
                    has_positive_attr = True
                    break
            except (ValueError, TypeError):
                continue
        
        if has_positive_attr:
            stats["has_positive"] += 1
            config_ids.append(ship_id)
    
    print(f"  统计: 总舰船={stats['total']}, 尾号1={stats['tail1']}, skin_id匹配={stats['skin_id_match']}, 有正属性={stats['has_positive']}")
    
    config_ids.sort()
    
    with open("fake_ship_config.txt", "w", encoding="utf-8") as f:
        for config_id in config_ids:
            f.write(str(config_id) + "\n")
    
    print(f"  找到 {len(config_ids)} 个符合条件的 configId")
    print(f"  已写入 fake_ship_config.txt")

def main():
    # 查找 ship_data_statistics.json
    json_path = Path("ship_data_statistics.json")
    
    if not json_path.exists():
        alt_paths = [
            Path("raw-data/CN/sharecfgdata/ship_data_statistics.json"),
            Path("sharecfgdata/ship_data_statistics.json"),
            Path("lua-scripts/CN/sharecfgdata/ship_data_statistics.json"),
        ]
        for alt_path in alt_paths:
            if alt_path.exists():
                json_path = alt_path
                break
    
    if not json_path.exists():
        print(f"错误: 找不到 ship_data_statistics.json")
        exit(1)
    
    print(f"读取: {json_path}")
    with open(json_path, 'r', encoding='utf-8') as f:
        ship_data = json.load(f)
    
    print(f"加载完成: {len(ship_data)} 条舰船数据")
    generate_fake_ship_config(ship_data)

if __name__ == "__main__":
    main()
