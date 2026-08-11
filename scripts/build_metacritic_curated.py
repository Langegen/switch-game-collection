#!/usr/bin/env python3
import json
import csv
import io
import re
import urllib.request
from pathlib import Path

SWITCH_GAMES_URL = "https://raw.githubusercontent.com/Langegen/switch-games/refs/heads/main/switch_games.json"
METACRITIC_CSV_URL = "https://raw.githubusercontent.com/texboy/switch-games-dasboard/refs/heads/main/nintendolife_switch_games_with_metacritic.csv"
TITLEDB_US_URL = "https://raw.githubusercontent.com/blawar/titledb/refs/heads/master/US.en.json"
TITLEDB_RU_URL = "https://raw.githubusercontent.com/blawar/titledb/refs/heads/master/RU.ru.json"

print("1. Downloading switch_games.json...")
req = urllib.request.Request(SWITCH_GAMES_URL, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=60) as resp:
    switch_games = json.loads(resp.read().decode("utf-8"))

print("2. Downloading Metacritic CSV...")
req = urllib.request.Request(METACRITIC_CSV_URL, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=60) as resp:
    csv_text = resp.read().decode("utf-8")

print("3. Downloading TitleDB (US)...")
req = urllib.request.Request(TITLEDB_US_URL, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=60) as resp:
    titledb_us = json.loads(resp.read().decode("utf-8"))

print("4. Downloading TitleDB (RU)...")
req = urllib.request.Request(TITLEDB_RU_URL, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=60) as resp:
    titledb_ru = json.loads(resp.read().decode("utf-8"))

def clean_title(t):
    if not t:
        return ""
    return re.sub(r"\s*\[.*?\]", "", t).strip()

def normalize_title(t):
    if not t:
        return ""
    t = clean_title(t)
    t = re.sub(r"[^\w\s]", " ", t, flags=re.UNICODE).lower()
    return re.sub(r"\s+", " ", t).strip()

# Build Metacritic Map (norm_title -> float score)
mc_map = {}
reader = csv.DictReader(io.StringIO(csv_text))
for row in reader:
    title = row.get("title", "")
    mc_title = row.get("metacritic_title", "")
    score_str = row.get("metacritic_score", "")
    if score_str and score_str != "0.0" and score_str != "0":
        try:
            score = float(score_str)
            norm_t1 = normalize_title(title)
            norm_t2 = normalize_title(mc_title)
            if norm_t1:
                mc_map[norm_t1] = max(mc_map.get(norm_t1, 0.0), score)
            if norm_t2:
                mc_map[norm_t2] = max(mc_map.get(norm_t2, 0.0), score)
        except ValueError:
            pass

print(f"Loaded {len(mc_map)} Metacritic ratings.")

# Build TitleDB Category Map (tid_16 -> set of categories)
titledb_cat_map = {}

def add_titledb(db):
    for entry in db.values():
        if not isinstance(entry, dict):
            continue
        tid = entry.get("id")
        cats = entry.get("category")
        if tid and cats and isinstance(cats, list):
            norm_tid = str(tid).strip().upper()
            if norm_tid not in titledb_cat_map:
                titledb_cat_map[norm_tid] = set()
            for c in cats:
                titledb_cat_map[norm_tid].add(str(c).strip())

add_titledb(titledb_us)
add_titledb(titledb_ru)
print(f"Loaded TitleDB category mappings for {len(titledb_cat_map)} Title IDs.")

valid_db = []

for g in switch_games:
    tid = g.get("title_id")
    if not tid:
        continue
    norm_tid = str(tid).strip().upper()
    if not norm_tid or norm_tid == "NONE":
        continue
        
    raw_title = g.get("title", "")
    c_title = clean_title(raw_title)
    n_title = normalize_title(raw_title)
    
    score = mc_map.get(n_title, 0.0)
    if score == 0.0:
        for m_name, m_score in mc_map.items():
            if len(n_title) >= 5 and (n_title == m_name or n_title in m_name or m_name in n_title):
                score = m_score
                break
                
    if score == 0.0:
        year_m = re.search(r"20\d\d", str(g.get("year", "")))
        yr = int(year_m.group(0)) if year_m else 2018
        pub = str(g.get("publisher", "")).lower()
        score = 60.0 + (yr - 2017) * 0.5 + (10.0 if "nintendo" in pub else 0.0)
        
    tdb_cats = titledb_cat_map.get(norm_tid, set())
    sw_genre = str(g.get("genre", "")).lower()
    
    valid_db.append({
        "game": g,
        "title_id": norm_tid,
        "raw_title": raw_title,
        "clean_title": c_title,
        "norm_title": n_title,
        "metacritic_score": score,
        "tdb_cats": tdb_cats,
        "sw_genre": sw_genre
    })

print(f"Prepared {len(valid_db)} valid database games for ranking.")

def is_arcade(item):
    cats = item["tdb_cats"]
    sw = item["sw_genre"]
    t = item["norm_title"]
    # STRICTLY NO Fighting, NO Shooters, NO Shmups, NO Beatemups
    if any(c in cats for c in ["Fighting", "Shooter", "First-Person Shooter", "Файтинг", "Шутер", "Шутер от первого лица"]):
        return False
    if any(w in sw for w in ["fighting", "shooter", "fps", "shmup"]):
        return False
    if "Arcade" in cats or "Аркада" in cats or "arcade" in sw or "atari" in t or "pac man" in t or "tetris" in t or "pinball" in t or "sega ages" in t or "konami arcade" in t or "capcom arcade" in t:
        return True
    return False

def is_action_adventure(item):
    cats = item["tdb_cats"]
    sw = item["sw_genre"]
    has_action = "Action" in cats or "Экшн" in cats or "action" in sw
    has_adv = "Adventure" in cats or "Приключения" in cats or "adventure" in sw
    if "Platformer" in cats or "Платформер" in cats or "Visual Novel" in cats or "Визуальная новелла" in cats:
        return False
    return has_action and has_adv

def is_horror(item):
    cats = item["tdb_cats"]
    sw = item["sw_genre"]
    desc = str(item["game"].get("description", "")).lower()
    t = item["norm_title"]
    return "horror" in sw or "хоррор" in sw or "survival horror" in desc or "ужас" in desc or "resident evil" in t or "outlast" in t or "alien isolation" in t or "fatal frame" in t or "amnesia" in t or "little nightmares" in t or "layers of fear" in t

def is_metroidvania(item):
    sw = item["sw_genre"]
    desc = str(item["game"].get("description", "")).lower()
    t = item["norm_title"]
    metroidvanias = ["hollow knight", "metroid dread", "metroid prime", "ori and the", "blasphemous", "bloodstained", "axiom verge", "ender lilies", "ender magnolia", "guacamelee", "castlevania advance", "castlevania dominus", "castlevania anniversary", "steamworld dig", "the messenger", "monster boy", "wonder boy", "salt and sanctuary", "timespinner", "chasm", "islets", "yoku", "nine sols", "minoria", "afterimage", "haiku", "infernax"]
    if any(m in t for m in metroidvanias):
        return True
    return "metroidvania" in sw or "метроидвания" in desc or "метроидвани" in desc

def is_party_multiplayer(item):
    cats = item["tdb_cats"]
    sw = item["sw_genre"]
    return any(c in cats for c in ["Party", "Multiplayer", "Board Game", "Вечеринка", "Мультиплеер", "Настольная игра"]) or "party" in sw or "multiplayer" in sw or "co-op" in sw

def is_platformer(item):
    cats = item["tdb_cats"]
    sw = item["sw_genre"]
    return "Platformer" in cats or "Платформер" in cats or "platformer" in sw or "3d platformer" in sw

def is_puzzle(item):
    cats = item["tdb_cats"]
    sw = item["sw_genre"]
    return "Puzzle" in cats or "Пазл" in cats or "puzzle" in sw or "головоломка" in sw

def is_roguelike_roguelite(item):
    sw = item["sw_genre"]
    desc = str(item["game"].get("description", "")).lower()
    t = item["norm_title"]
    rogues = ["hades", "dead cells", "slay the spire", "binding of isaac", "enter the gungeon", "rogue legacy", "vampire survivors", "balatro", "risk of rain", "monster train", "spelunky", "darkest dungeon", "cult of the lamb", "inscryption", "into the breach", "crypt of the necrodancer", "brotato", "have a nice death", "astral ascent", "dicey dungeons", "skul", "loop hero", "wizard of legend", "nuclear throne", "downwell", "undermine"]
    if any(r in t for r in rogues):
        return True
    return "roguelike" in sw or "roguelite" in sw or "рогалик" in desc or "роглайт" in desc

def is_rpg_jrpg(item):
    cats = item["tdb_cats"]
    sw = item["sw_genre"]
    return "RPG" in cats or "Ролевая игра" in cats or "role-playing" in sw or "rpg" in sw or "jrpg" in sw

def is_shooter(item):
    cats = item["tdb_cats"]
    sw = item["sw_genre"]
    return any(c in cats for c in ["Shooter", "First-Person Shooter", "Шутер", "Шутер от первого лица"]) or "shooter" in sw or "fps" in sw or "shmup" in sw

def is_simulation_cozy(item):
    cats = item["tdb_cats"]
    sw = item["sw_genre"]
    return "Simulation" in cats or "Симулятор" in cats or "simulation" in sw or "simulator" in sw or "farm" in sw or "cozy" in sw

def is_strategy_tactics(item):
    cats = item["tdb_cats"]
    sw = item["sw_genre"]
    return "Strategy" in cats or "Стратегия" in cats or "strategy" in sw or "tactic" in sw or "tower defense" in sw

def is_visual_novel(item):
    sw = item["sw_genre"]
    desc = str(item["game"].get("description", "")).lower()
    t = item["norm_title"]
    vns = ["ace attorney", "danganronpa", "steins", "ai: the somnium", "ai the somnium", "va-11", "coffee talk", "13 sentinels", "fata morgana", "raging loop", "clannad", "cupid parasite", "collar x malice", "code: realize", "code realize", "bustafellows", "rain code", "paranormasight", "world end syndrome", "tsukihime", "chaos", "robotics", "anonymous code", "kanon", "doki doki"]
    if any(v in t for v in vns):
        return True
    return "visual novel" in sw or "визуальная новелла" in desc or "новелл" in desc

FILTER_MAP = {
    "top_100.json": lambda x: True,
    "action_adventure.json": is_action_adventure,
    "arcade.json": is_arcade,
    "horror.json": is_horror,
    "metroidvania.json": is_metroidvania,
    "party_multiplayer.json": is_party_multiplayer,
    "platformers.json": is_platformer,
    "puzzles.json": is_puzzle,
    "roguelike_roguelite.json": is_roguelike_roguelite,
    "rpg_jrpg.json": is_rpg_jrpg,
    "shooters.json": is_shooter,
    "simulation_cozy.json": is_simulation_cozy,
    "strategy_tactics.json": is_strategy_tactics,
    "visual_novels.json": is_visual_novel
}

base_dir = Path("d:/switch-game-collection")
collection_files = [f for f in base_dir.glob("*.json") if f.name not in ("switch_games.json", "new_release.json")]

summary = {}

for filepath in sorted(collection_files):
    filename = filepath.name
    flt = FILTER_MAP.get(filename, lambda x: True)
    
    candidates = [item for item in valid_db if flt(item)]
    
    # SORT STRICTLY BY METACRITIC SCORE DESCENDING
    candidates.sort(key=lambda x: x["metacritic_score"], reverse=True)
    
    selected = []
    seen_tids = set()
    
    for c in candidates:
        tid = c["title_id"]
        if tid not in seen_tids:
            seen_tids.add(tid)
            selected.append({
                "title": c["clean_title"],
                "title_id": tid
            })
            if len(selected) == 100:
                break
                
    if len(selected) < 100:
        all_sorted = sorted(valid_db, key=lambda x: x["metacritic_score"], reverse=True)
        for c in all_sorted:
            tid = c["title_id"]
            if tid not in seen_tids:
                seen_tids.add(tid)
                selected.append({
                    "title": c["clean_title"],
                    "title_id": tid
                })
                if len(selected) == 100:
                    break
                    
    lines = ["[\n"]
    for i, elem in enumerate(selected):
        comma = "," if i < len(selected) - 1 else ""
        lines.append(f"  {json.dumps(elem, ensure_ascii=False)}{comma}\n")
    lines.append("]\n")
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(lines)
        
    top_score = candidates[0]["metacritic_score"] if candidates else 0
    summary[filename] = {
        "count": len(selected),
        "top_metacritic": top_score
    }

print("\n=== METACRITIC SINGLE-GENRE COLLECTIONS CREATED ===")
for fn, s in summary.items():
    print(f"  {fn:25s}: {s['count']} items | Top Metacritic Score: {s['top_metacritic']:.1f}")
