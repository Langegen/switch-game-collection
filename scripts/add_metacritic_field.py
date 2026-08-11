#!/usr/bin/env python3
import json
import csv
import io
import re
import urllib.request
from pathlib import Path

METACRITIC_CSV_URL = "https://raw.githubusercontent.com/texboy/switch-games-dasboard/refs/heads/main/nintendolife_switch_games_with_metacritic.csv"
SWITCH_GAMES_URL = "https://raw.githubusercontent.com/Langegen/switch-games/refs/heads/main/switch_games.json"

print("1. Fetching Metacritic CSV...")
req = urllib.request.Request(METACRITIC_CSV_URL, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=60) as resp:
    csv_text = resp.read().decode("utf-8")

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
            if norm_t1 and len(norm_t1) >= 4:
                mc_map[norm_t1] = max(mc_map.get(norm_t1, 0.0), score)
            if norm_t2 and len(norm_t2) >= 4:
                mc_map[norm_t2] = max(mc_map.get(norm_t2, 0.0), score)
        except ValueError:
            pass

print(f"Loaded {len(mc_map)} Metacritic ratings.")

def get_metacritic(title):
    n_title = normalize_title(title)
    if n_title in mc_map:
        return mc_map[n_title]
    for m_name, m_score in mc_map.items():
        if len(n_title) >= 5 and len(m_name) >= 5 and (n_title in m_name or m_name in n_title):
            return m_score
    return 0.0

base_dir = Path("d:/switch-game-collection")
collection_files = sorted(list(base_dir.glob("*.json")))
collection_files = [f for f in collection_files if f.name != "switch_games.json"]

for filepath in collection_files:
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    updated_data = []
    for item in data:
        t = item.get("title", "")
        tid = item.get("title_id", "")
        mc_score = get_metacritic(t)
        
        updated_data.append({
            "title": t,
            "title_id": tid,
            "metacritic": round(mc_score, 1) if mc_score > 0 else None
        })
        
    lines = ["[\n"]
    for i, elem in enumerate(updated_data):
        comma = "," if i < len(updated_data) - 1 else ""
        lines.append(f"  {json.dumps(elem, ensure_ascii=False)}{comma}\n")
    lines.append("]\n")
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(lines)
        
    print(f"Updated {filepath.name} with metacritic ratings.")

print("\nAll collection files updated successfully!")
