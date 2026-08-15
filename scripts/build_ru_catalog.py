#!/usr/bin/env python3
import json
import os
import re
import urllib.request
from pathlib import Path

SWITCH_GAMES_FILE = "switch_games.json"
TITLEDB_RU_FILE = "RU.ru.json"

SWITCH_GAMES_URL = "https://raw.githubusercontent.com/Langegen/switch-games/main/switch_games.json"
TITLEDB_RU_URL = "https://raw.githubusercontent.com/blawar/titledb/master/RU.ru.json"


def load_json_file(filename, fallback_url):
    if os.path.exists(filename) and os.path.getsize(filename) > 1000:
        print(f"Loading {filename} from disk ({os.path.getsize(filename) / 1024 / 1024:.2f} MB)...")
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    print(f"Fetching JSON from {fallback_url}...")
    req = urllib.request.Request(fallback_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        content = resp.read().decode("utf-8")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        return json.loads(content)


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


def get_one_paragraph(text):
    if not text:
        return ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text_clean = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text_clean = re.sub(r"</?p\s*>", "\n", text_clean, flags=re.IGNORECASE)
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n+", text_clean) if p.strip()]
    if paragraphs:
        return paragraphs[0]
    return text.strip()


def entry_score(entry):
    s = 0
    if entry.get("isDemo"):
        s -= 10
    if isinstance(entry.get("screenshots"), list) and entry.get("screenshots"):
        s += 2
    if str(entry.get("description", "")).strip():
        s += 1
    return s


def main():
    switch_games = load_json_file(SWITCH_GAMES_FILE, SWITCH_GAMES_URL)
    titledb_ru = load_json_file(TITLEDB_RU_FILE, TITLEDB_RU_URL)

    ru_by_tid = {}
    ru_by_name = {}
    if isinstance(titledb_ru, dict):
        entries = list(titledb_ru.values())
    else:
        entries = list(titledb_ru)
    for v in entries:
        if not isinstance(v, dict):
            continue
        tid = str(v.get("id") or "").strip().upper()
        if tid:
            if tid not in ru_by_tid or entry_score(v) > entry_score(ru_by_tid[tid]):
                ru_by_tid[tid] = v
        name = normalize_title(v.get("name"))
        if name and not v.get("isDemo"):
            if name not in ru_by_name or entry_score(v) > entry_score(ru_by_name[name]):
                ru_by_name[name] = v

    print(f"Loaded {len(ru_by_tid)} TitleDB entries by title_id, {len(ru_by_name)} by name.")

    ru_catalog = []
    ru_desc_count = 0
    ru_ss_count = 0
    tid_matched = 0
    name_matched = 0

    for item in switch_games:
        raw_tid = str(item.get("title_id", "")).strip().upper()
        ru_entry = ru_by_tid.get(raw_tid)
        if ru_entry:
            tid_matched += 1
        else:
            name = normalize_title(item.get("title", ""))
            ru_entry = ru_by_name.get(name)
            if ru_entry:
                name_matched += 1
        ru_entry = ru_entry or {}

        ru_desc = ru_entry.get("description")
        if ru_desc and isinstance(ru_desc, str) and ru_desc.strip():
            description = ru_desc.strip()
            ru_desc_count += 1
        else:
            description = get_one_paragraph(item.get("description", ""))

        ru_screenshots = ru_entry.get("screenshots")
        if ru_screenshots and isinstance(ru_screenshots, list) and len(ru_screenshots) > 0:
            screenshots = ru_screenshots
            ru_ss_count += 1
        else:
            screenshots = item.get("screenshots", [])
            if not isinstance(screenshots, list):
                screenshots = []

        ru_catalog.append({
            "title": item.get("title", ""),
            "size": item.get("size", ""),
            "magnet": item.get("magnet", ""),
            "topic_id": item.get("topic_id", ""),
            "url": item.get("url", ""),
            "year": item.get("year", ""),
            "genre": item.get("genre", ""),
            "developer": item.get("developer", ""),
            "publisher": item.get("publisher", ""),
            "image_format": item.get("image_format", ""),
            "interface_lang": item.get("interface_lang", ""),
            "voice_lang": item.get("voice_lang", ""),
            "performance": item.get("performance", ""),
            "multiplayer": item.get("multiplayer", ""),
            "cover": item.get("cover", ""),
            "screenshots": screenshots,
            "description": description,
            "title_id": item.get("title_id", ""),
        })

    print(f"\nProcessing Complete!")
    print(f"Total entries in catalog: {len(ru_catalog)}")
    print(f"Matched by title_id: {tid_matched}, by name: {name_matched}")
    print(f"Descriptions taken from RU.ru.json: {ru_desc_count} / {len(ru_catalog)}")
    print(f"Screenshots taken from RU.ru.json: {ru_ss_count} / {len(ru_catalog)}")

    output_path = Path("RU_catalog.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(ru_catalog, f, ensure_ascii=False, indent=4)

    print(f"Successfully saved catalog to {output_path.resolve()}")


if __name__ == "__main__":
    main()
