#!/usr/bin/env python3
"""Build racing.json and sports.json, ranked by Metacritic score.

Same approach as build_perfect_metacritic_collections.py (TitleDB categories
+ catalog genre, sorted by Metacritic), with two differences:
  * only these two collections are written, other files are left alone;
  * no filler from other genres: games with a real Metacritic score come
    first, then genre games without one, up to 100 entries.

Output format matches add_metacritic_field.py ("metacritic": null when the
game has no real score).
"""
import csv
import io
import json
import re
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SWITCH_GAMES_URL = "https://raw.githubusercontent.com/Langegen/switch-games/refs/heads/main/switch_games.json"
METACRITIC_CSV_URL = "https://raw.githubusercontent.com/texboy/switch-games-dasboard/refs/heads/main/nintendolife_switch_games_with_metacritic.csv"
# TitleDB copies are kept in this repo (blawar/titledb US.en / RU.ru).
TITLEDB_FILES = [BASE_DIR / "US.en.json", BASE_DIR / "RU.ru.json"]
LIMIT = 100


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read().decode("utf-8")


def clean_title(t):
    return re.sub(r"\s*\[.*?\]", "", t or "").strip()


def normalize_title(t):
    t = clean_title(t)
    t = re.sub(r"[^\w\s]", " ", t, flags=re.UNICODE).lower()
    return re.sub(r"\s+", " ", t).strip()


print("1. Downloading switch_games.json...")
switch_games = json.loads(fetch(SWITCH_GAMES_URL))

print("2. Downloading Metacritic CSV...")
mc_map = {}
for row in csv.DictReader(io.StringIO(fetch(METACRITIC_CSV_URL))):
    try:
        score = float(row.get("metacritic_score") or 0)
    except ValueError:
        continue
    if score <= 0:
        continue
    for name in (row.get("title", ""), row.get("metacritic_title", "")):
        n = normalize_title(name)
        if len(n) >= 4:
            mc_map[n] = max(mc_map.get(n, 0.0), score)
print(f"   {len(mc_map)} Metacritic ratings")


def metacritic_for(n_title):
    """Exact title, else the longest rated title that one name starts with
    (on a word boundary): "rocket league 24 dlc" -> "rocket league". Plain
    substring matching gave false hits ("fate hollow ataraxia" -> "hollow")."""
    if n_title in mc_map:
        return mc_map[n_title]
    best_len, best = 0, 0.0
    for m_name, m_score in mc_map.items():
        short, long_ = (m_name, n_title) if len(m_name) <= len(n_title) else (n_title, m_name)
        if len(short) < 6 or len(short) <= best_len:
            continue
        if long_.startswith(short + " "):
            best_len, best = len(short), m_score
    return best


print("3. Reading TitleDB categories...")
tdb_cats = {}
for path in TITLEDB_FILES:
    with open(path, encoding="utf-8") as f:
        db = json.load(f)
    for entry in db.values():
        if not isinstance(entry, dict):
            continue
        tid, cats = entry.get("id"), entry.get("category")
        if tid and isinstance(cats, list):
            tdb_cats.setdefault(str(tid).strip().upper(), set()).update(str(c).strip() for c in cats)
print(f"   categories for {len(tdb_cats)} title ids")

items = []
for g in switch_games:
    tid = str(g.get("title_id") or "").strip().upper()
    if not tid or tid == "NONE":
        continue
    raw = g.get("title", "")
    n_title = normalize_title(raw)
    items.append({
        "title_id": tid,
        "clean_title": clean_title(raw),
        "norm_title": n_title,
        "score": metacritic_for(n_title),
        "year": g.get("year", ""),
        "cats": tdb_cats.get(tid, set()),
        "sw_genre": str(g.get("genre", "")).lower(),
    })

def has_any(text, words):
    return any(w in text for w in words)


# Multi-game compilations: one racing/sports game inside does not make the
# whole bundle one.
COMPILATION_WORDS = ["ngolf nblocks", "arcade archives", "sega ages", "arcade collection", "selection vol",
                     "commodore 64", "collection of mana", "kunio kun", "neogeo pocket"]

RACING_TITLE_WORDS = ["mario kart", "kart racing", "rally", "motogp", "nascar", "need for speed",
                      "burnout", "asphalt", "gear club", "mx vs atv", "mxgp", "supercross",
                      "trials rising", "trials fusion", "redout", "fast rmx", "grid autosport",
                      "hot wheels", "horizon chase", "wrc ", "formula legends", "f1 "]
# Catalog genres that mean "this is not a racing game" when the racing
# hint comes only from TitleDB (publishers tag platformers, shooters and
# even visual novels as Racing).
NOT_RACING_GENRES = ["platformer", "shooter", "shootemup", "visual novel", "puzzle", "role-playing",
                     "rpg", "fighting", "board game", "adventure", "simulator", "metroidvania"]

SPORTS_GENRES = ["sport", "fitness"]
NOT_SPORTS_GENRES = ["platformer", "music", "rhythm", "fighting", "puzzle", "visual novel",
                     "role-playing", "shooter", "runner", "beatemup", "adventure", "board game"]
NOT_SPORTS_TITLES = ["let s sing", "just dance", "groove coaster"]


def is_racing(it):
    t, sw = it["norm_title"] + " ", it["sw_genre"]
    if has_any(t, COMPILATION_WORDS):
        return False
    if "racing" in sw or "гонки" in sw or has_any(t, RACING_TITLE_WORDS):
        return True
    # TitleDB tag alone is weak: also require a real Metacritic score.
    tdb = "Racing" in it["cats"] or "Гонки" in it["cats"]
    return tdb and it["score"] > 0 and not has_any(sw, NOT_RACING_GENRES)


def is_sports(it):
    t, sw = it["norm_title"] + " ", it["sw_genre"]
    # Motorsport goes to the racing collection.
    if is_racing(it) or has_any(t, COMPILATION_WORDS) or has_any(t, NOT_SPORTS_TITLES):
        return False
    if has_any(sw, SPORTS_GENRES) or "спорт" in sw:
        return "fighting" not in sw
    tdb = "Sports" in it["cats"] or "Спорт" in it["cats"]
    return tdb and it["score"] > 0 and not has_any(sw, NOT_SPORTS_GENRES)


def build(flt):
    cands = [it for it in items if flt(it)]
    # Real Metacritic first (desc), then the rest by year (newer first).
    cands.sort(key=lambda it: (it["score"] > 0, it["score"], str(it["year"])), reverse=True)
    out, seen = [], set()
    for it in cands:
        if it["title_id"] in seen:
            continue
        seen.add(it["title_id"])
        out.append({
            "title": it["clean_title"],
            "title_id": it["title_id"],
            "metacritic": round(it["score"], 1) if it["score"] > 0 else None,
        })
        if len(out) == LIMIT:
            break
    return out


def write(name, data):
    lines = ["[\n"]
    for i, elem in enumerate(data):
        comma = "," if i < len(data) - 1 else ""
        lines.append(f"  {json.dumps(elem, ensure_ascii=False)}{comma}\n")
    lines.append("]\n")
    with open(BASE_DIR / name, "w", encoding="utf-8", newline="\n") as f:
        f.writelines(lines)
    rated = sum(1 for e in data if e["metacritic"] is not None)
    print(f"   {name}: {len(data)} games, {rated} with Metacritic")


print("4. Writing collections...")
write("racing.json", build(is_racing))
write("sports.json", build(is_sports))
