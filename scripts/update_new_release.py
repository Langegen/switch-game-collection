#!/usr/bin/env python3
import json
import csv
import io
import re
import urllib.request
import xml.etree.ElementTree as ET
import sys
from pathlib import Path

ATOM_FEED_URL = "https://feed.rutracker.cc/atom/f/1605.atom"
SWITCH_GAMES_URL = "https://raw.githubusercontent.com/Langegen/switch-games/refs/heads/main/switch_games.json"
METACRITIC_CSV_URL = "https://raw.githubusercontent.com/texboy/switch-games-dasboard/refs/heads/main/nintendolife_switch_games_with_metacritic.csv"
OUTPUT_FILE = Path(__file__).parent.parent / "new_release.json"


def fetch_url(url: str) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def extract_topic_id(text: str) -> str | None:
    if not text:
        return None
    match = re.search(r"t=(\d+)", text)
    if match:
        return match.group(1)
    match = re.search(r"/t/(\d+)", text)
    if match:
        return match.group(1)
    return None


def clean_title(title: str) -> str:
    if not title:
        return ""
    cleaned = re.sub(r"\s*\[.*?\]", "", title).strip()
    return cleaned if cleaned else title.strip()


def normalize_title(t: str) -> str:
    if not t:
        return ""
    t = clean_title(t)
    t = re.sub(r"[^\w\s]", " ", t, flags=re.UNICODE).lower()
    return re.sub(r"\s+", " ", t).strip()


def load_metacritic_map() -> dict:
    mc_map = {}
    try:
        csv_bytes = fetch_url(METACRITIC_CSV_URL)
        csv_text = csv_bytes.decode("utf-8")
        reader = csv.DictReader(io.StringIO(csv_text))
        for row in reader:
            title = row.get("title", "")
            mc_title = row.get("metacritic_title", "")
            score_str = row.get("metacritic_score", "")
            if score_str and score_str != "0.0" and score_str != "0":
                try:
                    score = float(score_str)
                    n1 = normalize_title(title)
                    n2 = normalize_title(mc_title)
                    if n1 and len(n1) >= 4:
                        mc_map[n1] = max(mc_map.get(n1, 0.0), score)
                    if n2 and len(n2) >= 4:
                        mc_map[n2] = max(mc_map.get(n2, 0.0), score)
                except ValueError:
                    pass
    except Exception as e:
        print(f"Warning: Could not fetch Metacritic CSV: {e}", file=sys.stderr)
    return mc_map


def get_metacritic_score(title: str, mc_map: dict) -> float | None:
    n_title = normalize_title(title)
    if n_title in mc_map:
        return round(mc_map[n_title], 1)
    for m_name, m_score in mc_map.items():
        if len(n_title) >= 5 and len(m_name) >= 5 and (n_title in m_name or m_name in n_title):
            return round(m_score, 1)
    return None


def main():
    print(f"Fetching atom feed from {ATOM_FEED_URL}...")
    try:
        atom_bytes = fetch_url(ATOM_FEED_URL)
    except Exception as e:
        print(f"Error fetching atom feed: {e}", file=sys.stderr)
        sys.exit(1)

    print("Fetching Metacritic map...")
    mc_map = load_metacritic_map()

    print(f"Fetching switch_games database from {SWITCH_GAMES_URL}...")
    local_db = Path(__file__).parent.parent / "switch_games.json"
    if local_db.exists():
        print("Using local switch_games.json database...")
        with open(local_db, "r", encoding="utf-8") as f:
            games_data = json.load(f)
    else:
        try:
            games_bytes = fetch_url(SWITCH_GAMES_URL)
            games_data = json.loads(games_bytes.decode("utf-8"))
        except Exception as e:
            print(f"Error fetching switch_games.json: {e}", file=sys.stderr)
            sys.exit(1)

    topic_map = {}
    for game in games_data:
        tid = game.get("topic_id")
        if tid:
            topic_map[str(tid)] = game
        else:
            url = game.get("url", "")
            tid = extract_topic_id(url)
            if tid:
                topic_map[tid] = game

    root = ET.fromstring(atom_bytes)
    ns = {"atom": "http://www.w3.org/2005/Atom"}

    new_releases = []
    seen_title_ids = set()

    for entry in root.findall("atom:entry", ns):
        link_elem = entry.find("atom:link", ns)
        link_href = link_elem.attrib.get("href", "") if link_elem is not None else ""
        topic_id = extract_topic_id(link_href)

        if not topic_id:
            id_elem = entry.find("atom:id", ns)
            id_text = id_elem.text if id_elem is not None else ""
            topic_id = extract_topic_id(id_text)

        if not topic_id or topic_id not in topic_map:
            continue

        game = topic_map[topic_id]
        title_id = game.get("title_id")

        if not title_id:
            continue

        title_id_clean = str(title_id).strip().upper()
        if not title_id_clean or title_id_clean == "NONE":
            continue

        if title_id_clean in seen_title_ids:
            continue
        seen_title_ids.add(title_id_clean)

        raw_title = game.get("title", "")
        formatted_title = clean_title(raw_title)
        mc_score = get_metacritic_score(formatted_title, mc_map)

        new_releases.append(
            {
                "title": formatted_title,
                "title_id": title_id_clean,
                "metacritic": mc_score
            }
        )

    print(f"Generated {len(new_releases)} new release entries.")

    lines = ["[\n"]
    for i, item in enumerate(new_releases):
        comma = "," if i < len(new_releases) - 1 else ""
        lines.append(f"  {json.dumps(item, ensure_ascii=False)}{comma}\n")
    lines.append("]\n")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(f"Successfully updated {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
