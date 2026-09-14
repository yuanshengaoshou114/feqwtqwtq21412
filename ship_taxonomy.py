"""舰船三级分类：阵营 / 稀有度 / 舰种。

数据来源（全部来自上游 AzurLaneLuaScripts 的 CN 服脚本）：

  name.json 里的 ship_group
    = ship_skin_template.ship_group           （也就是 ship_data_group 的 group_type）
    → 默认舰船 configId = ship_group * 10 + 1
      依据 CN/model/vo/shipgroup.lua:
          slot0.getDefaultShipConfig = function(slot0)
              return pg.ship_data_statistics[slot0 * 10 + 1]
          end
    → ship_data_statistics[configId] 里的 nationality / rarity / type

中文名来源：
  阵营  CN/model/const/nation.lua 的 Nation2Name + sharecfgdata/gametip.lua 的 word_shipNation_*
  舰种  CN/sharecfg/ship_data_by_type.lua 的 type_name（本模块会在文件存在时实时解析）
  稀有度 CN/model/const/shipindexconst.lua 的 index_rare2..6 → gametip（普通/稀有/精锐/超稀有/海上传奇）

本模块不依赖 UnityPy / PIL，纯标准库，CI 和本地都能跑。
"""
from __future__ import annotations

import json
import re
from pathlib import Path

# ---------------------------------------------------------------------------
# 1. 中文名表（gametip 太大，直接固化；上游改名时按注释里的 key 重新取一次即可）
# ---------------------------------------------------------------------------

# 对应 gametip 的 word_shipNation_*，菜单顺序按国服图鉴的排列
NATION_NAMES = {
    0: '其他',
    1: '白鹰',          # word_shipNation_baiYing
    2: '皇家',          # word_shipNation_huangJia
    3: '重樱',          # word_shipNation_chongYing
    4: '铁血',          # word_shipNation_tieXue
    5: '东煌',          # word_shipNation_dongHuang
    6: '撒丁帝国',      # word_shipNation_saDing
    7: '北方联合',      # word_shipNation_beiLian
    8: '自由鸢尾',      # word_shipNation_ziyou
    9: '维希教廷',      # word_shipNation_weixi
    10: '鸢尾教国',     # word_shipNation_yuanwei
    11: '郁金王国',     # word_shipNation_yujinwangguo
    12: '晶环联盟',     # word_shipNation_jinghuanlianmeng
    96: '飓风',         # word_shipNation_mot
    97: 'META',         # word_shipNation_meta_index
    98: '其他',         # word_shipNation_other（布里 / 测试机）
    101: '海王星',      # word_shipNation_np
    102: '哔哩哔哩',
    103: '传颂之物',
    104: 'KizunaAI',
    105: 'hololive',
    106: '维纳斯假期',
    107: '偶像大师',
    108: 'SSSS',
    109: 'Atelier Ryza',
    110: '闪乱神乐',
    111: 'To LOVE-Ru',
    112: 'BLACK★ROCK SHOOTER',
    113: 'Atelier Yumia',
    114: 'danmachi',
    115: 'Date A Live',
    117: 'NieR Automata',
}

# 稀有度：ship_data_statistics.rarity → 图鉴里的 index_rareN
RARITY_NAMES = {
    2: '普通',
    3: '稀有',
    4: '精锐',
    5: '超稀有',
    6: '海上传奇',
}

# 舰种兜底表：CN/sharecfg/ship_data_by_type.lua 存在时会用文件里的 type_name 覆盖
TYPE_NAMES_FALLBACK = {
    1: '驱逐', 2: '轻巡', 3: '重巡', 4: '战巡', 5: '战列', 6: '轻航', 7: '正航',
    8: '潜艇', 9: '航巡', 10: '航战', 11: '雷巡', 12: '维修', 13: '重炮',
    17: '潜母', 18: '超巡', 19: '运输', 20: '导驱', 21: '导驱', 22: '风帆',
    23: '风帆', 24: '风帆',
}

# 菜单排序用：国服图鉴的阵营顺序，没写进来的排在最后
NATION_ORDER = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 97, 96, 98, 101, 102, 103,
                104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 117, 0]
# 稀有度从高到低排（跟游戏里一致：海上传奇在最前）
RARITY_ORDER = [6, 5, 4, 3, 2]
# 舰种顺序：ShipType.AllShipType 的顺序
TYPE_ORDER = [1, 2, 3, 18, 4, 5, 6, 7, 10, 17, 13, 8, 12, 19, 20, 21, 22, 23, 24]

# 查不到分类时显示的兜底名（NPC、未实装的测试机、联动 Boss 之类）
UNKNOWN = '其他'


# ---------------------------------------------------------------------------
# 2. 轻量解析：ship_data_by_type.lua（有就用文件里的名字，没有就用兜底表）
# ---------------------------------------------------------------------------

def load_type_names(lua_path='ship_data_by_type.lua'):
    """读 CN/sharecfg/ship_data_by_type.lua 的 type_name。读不到返回兜底表。"""
    path = Path(lua_path)
    if not path.exists():
        return dict(TYPE_NAMES_FALLBACK)
    text = path.read_text('utf-8')
    found = {}
    for match in re.finditer(r'pg\.base\.ship_data_by_type\[(\d+)\] = \{(.*?)\n\t\}', text, re.S):
        name = re.search(r'type_name = "([^"]*)"', match.group(2))
        if name:
            found[int(match.group(1))] = name.group(1)
    # 文件里没有的（新舰种）用兜底表补齐
    merged = dict(TYPE_NAMES_FALLBACK)
    merged.update(found)
    return merged


def stats_from_lua(lua_path):
    """快速从 sharecfgdata/ship_data_statistics.lua 抽出 {ship_id: {nationality, rarity, type}}。

    1.py 里那份 ship_data_statistics.json 是整表解析（很慢），这里用正则只取三个字段，
    本地调试 / 只想更新分类时可以直接用。
    """
    # 第一行就是第一条数据，前面补个换行，否则会漏掉 ID 最小的那条（100001 泛用型布里）
    text = '\n' + Path(lua_path).read_text('utf-8')
    result = {}
    for chunk in text.split('\n_G.pg.base.ship_data_statistics[')[1:]:
        head = re.match(r'(\d+)\] = \{', chunk)
        if not head:
            continue
        body = chunk.split('\n}', 1)[0]

        def field(name):
            hit = re.search(r'^\t' + name + r' = "?(-?\d+)"?,', body, re.M)
            return int(hit.group(1)) if hit else None

        result[int(head.group(1))] = {
            'nationality': field('nationality'),
            'rarity': field('rarity'),
            'type': field('type'),
        }
    return result


# ---------------------------------------------------------------------------
# 3. ship_group → 分类
# ---------------------------------------------------------------------------

def build_group_taxonomy(ship_stats, skin_template=None):
    """返回 {'10000': {'nation': 98, 'rarity': 4, 'ship_type': 1}, ...}。

    ship_stats     : {ship_id: {...}} —— 1.py 转出来的 ship_data_statistics.json
    skin_template  : {skin_id: {...}} —— 1.py 转出来的 ship_skin_template.json（可选，做兜底）

    两条链路，先精后粗：
      1) ship_group * 10 + 1 == 默认舰船 id（游戏自己的算法，覆盖绝大多数）
      2) 默认舰船不存在时（NPC、未实装的联动测试机），用 ship_data_statistics.skin_id
         反查 ship_skin_template.ship_group，任何一条船挂到这个组都算
    """
    taxonomy = {}

    def put(group, info):
        if group is None or info is None:
            return
        group = str(group)
        if group in taxonomy:
            return
        nation, rarity, ship_type = info.get('nationality'), info.get('rarity'), info.get('type')
        if nation is None and rarity is None and ship_type is None:
            return
        try:
            taxonomy[group] = {
                'nation': int(nation) if nation is not None else None,
                'rarity': int(rarity) if rarity is not None else None,
                'ship_type': int(ship_type) if ship_type is not None else None,
            }
        except (TypeError, ValueError):
            pass

    # 链路 1：默认舰船 id
    for ship_id, info in ship_stats.items():
        try:
            sid = int(ship_id)
        except (TypeError, ValueError):
            continue
        if sid % 10 != 1:
            continue
        put(sid // 10, info)

    # 链路 2：默认皮肤反查
    if skin_template:
        for ship_id, info in ship_stats.items():
            skin_id = info.get('skin_id')
            if skin_id is None:
                continue
            skin = skin_template.get(str(skin_id))
            if not skin:
                continue
            put(skin.get('ship_group'), info)

    return taxonomy


def decorate(ship_group, taxonomy, type_names=None):
    """给一条记录补上 nation / rarity / ship_type 三个字段（含中文名）。查不到就留空。"""
    type_names = type_names or TYPE_NAMES_FALLBACK
    hit = taxonomy.get(str(ship_group), {})
    nation = hit.get('nation')
    rarity = hit.get('rarity')
    ship_type = hit.get('ship_type')
    return {
        'nation': nation,
        'nation_name': NATION_NAMES.get(nation, UNKNOWN) if nation is not None else UNKNOWN,
        'rarity': rarity,
        'rarity_name': RARITY_NAMES.get(rarity, UNKNOWN) if rarity is not None else UNKNOWN,
        'ship_type': ship_type,
        'ship_type_name': type_names.get(ship_type, UNKNOWN) if ship_type is not None else UNKNOWN,
    }


def taxonomy_meta(type_names=None):
    """给 UI 用的字典表：每个维度有哪些值、按什么顺序显示。"""
    type_names = type_names or TYPE_NAMES_FALLBACK
    return {
        'nation': [{'id': i, 'name': NATION_NAMES.get(i, UNKNOWN)} for i in NATION_ORDER],
        'rarity': [{'id': i, 'name': RARITY_NAMES[i]} for i in RARITY_ORDER],
        'ship_type': [{'id': i, 'name': type_names.get(i, UNKNOWN)} for i in TYPE_ORDER],
    }


def sort_key(row):
    """三级菜单 + 角色 + 皮肤的排序键，直接喂给 sorted()。"""
    def rank(order, value):
        return (order.index(value), '') if value in order else (len(order), str(value))

    return (rank(NATION_ORDER, row.get('nation')),
            rank(RARITY_ORDER, row.get('rarity')),
            rank(TYPE_ORDER, row.get('ship_type')),
            str(row.get('ship_group', '')),
            str(row.get('painting', '')))


if __name__ == '__main__':
    # 本地自检：python ship_taxonomy.py <sharecfgdata目录>
    import sys
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    stats = stats_from_lua(root / 'ship_data_statistics.lua')
    types = load_type_names(root.parent / 'sharecfg' / 'ship_data_by_type.lua')
    tax = build_group_taxonomy(stats)
    print(f'舰船 {len(stats)} 条，分组 {len(tax)} 个，舰种名 {len(types)} 个')
    for group in list(tax)[:5]:
        print(group, tax[group], decorate(group, tax, types))
