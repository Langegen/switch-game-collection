#!/usr/bin/env python3
import json
import glob
import os
import re
import urllib.request
from pathlib import Path

URL = "https://raw.githubusercontent.com/Langegen/switch-games/refs/heads/main/switch_games.json"

print(f"Fetching latest switch_games.json from {URL}...")
req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=60) as resp:
    switch_games = json.loads(resp.read().decode("utf-8"))

def clean_title(t):
    if not t:
        return ""
    t = re.sub(r"\s*\[.*?\]", "", t)
    return t.strip()

HIGH_PRIORITY_KEYWORDS = [
    "mario", "zelda", "pokemon", "pokémon", "kirby", "metroid", "fire emblem", "xenoblade",
    "donkey kong", "pikmin", "splatoon", "luigi", "bayonetta", "persona", "monster hunter",
    "final fantasy", "dragon quest", "shin megami tensei", "sonic", "castlevania", "contra",
    "resident evil", "silent hill", "outlast", "amnesia", "doom", "wolfenstein", "quake",
    "bioshock", "borderlands", "metro", "fallout", "elder scrolls", "skyrim", "witcher",
    "gta", "grand theft auto", "red dead", "assassin", "prince of persia", "tomb raider",
    "crash", "spyro", "rayman", "hollow knight", "ori", "blasphemous", "dead cells",
    "hades", "celeste", "cuphead", "shovel knight", "stardew", "animal crossing",
    "overcooked", "it takes two", "moving out", "trine", "snipperclips", "jackbox",
    "worms", "bomberman", "puyo", "tetris", "lumines", "captain toad", "portal",
    "baba is you", "unpacking", "house flipper", "powerwash", "coffee talk", "va-11",
    "danganronpa", "ace attorney", "steins", "clannad", "ai: the somnium", "fate",
    "disgaea", "atelier", "ys", "tales of", "octopath", "triangle strategy", "tactics ogre",
    "valkyria", "advance wars", "harvest moon", "story of seasons", "rune factory",
    "balatro", "vampire survivors", "slay the spire", "monster train", "risk of rain",
    "darkest dungeon", "inscryption", "cult of the lamb", "salt and", "bloodstained",
    "axiom verge", "ender lilies", "guacamelee", "little nightmares", "layers of fear",
    "dead by daylight", "alien isolation", "fatal frame", "street fighter", "tekken",
    "mortal kombat", "guilty gear", "blazblue", "king of fighters", "marvel", "snk",
    "dragon ball", "naruto", "one piece", "fifa", "ea sports", "nba 2k", "tony hawk",
    "diablo", "divinity", "baldur", "pillar", "wasteland", "civ", "civilization"
]

def score_game(g):
    score = 0
    t = g.get("title", "").lower()
    
    for kw in HIGH_PRIORITY_KEYWORDS:
        if kw in t:
            score += 50
            break
            
    year_str = str(g.get("year", ""))
    m = re.search(r"20\d\d", year_str)
    if m:
        yr = int(m.group(0))
        score += (yr - 2017) * 2
        
    pub = str(g.get("publisher", "")).lower()
    dev = str(g.get("developer", "")).lower()
    major_pubs = ["nintendo", "capcom", "square enix", "bandai namco", "sega", "konami", "ubisoft", "devolver", "team17", "atlus", "bethesda", "wb games", "ea", "2k", "raw fury", "annapurna", "chucklefish"]
    for mp in major_pubs:
        if mp in pub or mp in dev:
            score += 15
            break
            
    if g.get("cover"):
        score += 5
    if g.get("screenshots"):
        score += 5
    if g.get("description"):
        score += 5
        
    return score

valid_db = []
for g in switch_games:
    tid = g.get("title_id")
    if not tid:
        continue
    norm_tid = str(tid).strip().upper()
    if not norm_tid or norm_tid == "NONE":
        continue
    valid_db.append({
        "game": g,
        "title_id": norm_tid,
        "clean_title": clean_title(g.get("title", "")),
        "genre": g.get("genre", "").lower(),
        "score": score_game(g)
    })

valid_db.sort(key=lambda x: x["score"], reverse=True)

GENRE_MAP = {
    "action_adventure.json": ["action", "adventure"],
    "arcade.json": ["arcade", "beatemup", "fighting", "racing", "shmup", "action"],
    "horror.json": ["horror", "thriller", "survival"],
    "metroidvania.json": ["metroidvania", "platformer"],
    "party_multiplayer.json": ["party", "multiplayer", "co-op", "board game", "arcade"],
    "platformers.json": ["platformer", "3d platformer", "runner", "action"],
    "puzzles.json": ["puzzle", "hidden objects", "logic", "point & click"],
    "roguelike_roguelite.json": ["roguelite", "roguelike", "tcg", "card"],
    "rpg_jrpg.json": ["role-playing", "rpg", "jrpg", "tactic"],
    "shooters.json": ["shooter", "first person shooter", "fps", "shmup", "action"],
    "simulation_cozy.json": ["simulator", "simulation", "farm", "cozy", "management"],
    "strategy_tactics.json": ["strategy", "tactic", "tower defense", "turn-based"],
    "top_100.json": [],
    "visual_novels.json": ["visual novel", "interactive fiction", "point & click", "anime"]
}

base_dir = Path("d:/switch-game-collection")
collection_files = [f for f in base_dir.glob("*.json") if f.name not in ("switch_games.json", "new_release.json")]

summary = {}

for filepath in sorted(collection_files):
    filename = filepath.name
    with open(filepath, "r", encoding="utf-8") as f:
        existing = json.load(f)
        
    current_tids = {str(item.get("title_id")).strip().upper() for item in existing}
    needed = 100 - len(existing)
    
    allowed_genres = GENRE_MAP.get(filename, [])
    
    candidates = []
    for dbe in valid_db:
        tid = dbe["title_id"]
        if tid in current_tids:
            continue
            
        if not allowed_genres:
            candidates.append(dbe)
        else:
            db_genre = dbe["genre"]
            if any(ag in db_genre for ag in allowed_genres):
                candidates.append(dbe)
                
    added = candidates[:needed]
    
    updated_list = list(existing)
    for a in added:
        updated_list.append({
            "title": a["clean_title"],
            "title_id": a["title_id"]
        })
        current_tids.add(a["title_id"])
        
    lines = ["[\n"]
    for i, elem in enumerate(updated_list):
        comma = "," if i < len(updated_list) - 1 else ""
        lines.append(f"  {json.dumps(elem, ensure_ascii=False)}{comma}\n")
    lines.append("]\n")
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(lines)
        
    summary[filename] = {
        "existing": len(existing),
        "added": len(added),
        "final_count": len(updated_list)
    }

print("\n=== COLLECTION FILL COMPLETED ===")
for fn, s in summary.items():
    print(f"{fn:25s}: Was {s['existing']:2d} + Added {s['added']:2d} = Total {s['final_count']:3d}")
