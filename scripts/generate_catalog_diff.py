#!/usr/bin/env python3
import hashlib
import json
import os
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
HISTORY_FILE = BASE_DIR / "diff_history.json"
OUTPUT_DIFF = BASE_DIR / "catalog_diff.json"
WINDOW_SECONDS = 72 * 3600  # 72 hours rolling window

LANG_FILES = {
    "ru": "RU_catalog.json",
    "en": "EN_catalog.json",
    "es": "ES_catalog.json",
    "fr": "FR_catalog.json",
    "de": "DE_catalog.json",
    "it": "IT_catalog.json",
    "pt_br": "PT_BR_catalog.json",
    "zh_hans": "ZH_Hans_catalog.json",
}


def compute_signature(game: dict) -> str:
    """
    Computes a deterministic hash signature of key game fields:
    title, size, magnet, description, and cover.
    Any changes to these fields trigger an update in the diff.
    """
    if not isinstance(game, dict):
        return ""
    size = str(game.get("size", "")).strip()
    magnet = str(game.get("magnet", "")).strip()
    title = str(game.get("title", "")).strip()
    desc = str(game.get("description", "")).strip()
    cover = str(game.get("cover", "")).strip()

    raw = f"{size}|{magnet}|{title}|{desc}|{cover}".encode("utf-8")
    hash_hex = hashlib.md5(raw).hexdigest()[:12]
    return f"{size}_{magnet[:40]}_{hash_hex}"


def load_json_safe(file_path: Path, default_value=None):
    if default_value is None:
        default_value = {}
    if file_path.exists():
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load {file_path.name}: {e}", file=sys.stderr)
            return default_value
    return default_value


def update_catalog_diff() -> dict:
    """
    Updates the 72-hour rolling catalog diff.
    - Tracks changes across 8 language catalogs.
    - Maintains diff_history.json to retain baseline state and 72-hour window.
    - Generates catalog_diff.json with added_or_updated and deleted_topic_ids.
    """
    now = int(time.time())
    cutoff = now - WINDOW_SECONDS

    # 1. Load history state
    raw_history = load_json_safe(HISTORY_FILE, {})
    history = {
        "known_signatures": raw_history.get("known_signatures", {}),
        "topics": raw_history.get("topics", {}),
        "deleted": raw_history.get("deleted", {}),
    }

    # 2. Prune records older than 72 hours
    history["topics"] = {
        tid: data
        for tid, data in history["topics"].items()
        if data.get("time", 0) >= cutoff
    }
    history["deleted"] = {
        tid: del_time
        for tid, del_time in history["deleted"].items()
        if del_time >= cutoff
    }

    # 3. Load current catalogs for all languages
    current_catalogs = {}
    for lang, filename in LANG_FILES.items():
        file_path = BASE_DIR / filename
        if file_path.exists():
            data = load_json_safe(file_path, [])
            current_catalogs[lang] = {
                str(g["topic_id"]).strip(): g
                for g in data
                if isinstance(g, dict) and "topic_id" in g
            }
        else:
            print(f"Notice: Catalog {filename} not found, skipping {lang}.")

    if not current_catalogs:
        print("Error: No catalog files found. Cannot generate catalog diff.", file=sys.stderr)
        return {}

    base_lang = "ru" if "ru" in current_catalogs else next(iter(current_catalogs))
    current_base = current_catalogs[base_lang]
    current_tids = set(current_base.keys())

    is_first_baseline = len(history["known_signatures"]) == 0

    if is_first_baseline:
        print("Initializing diff history baseline for all current games...")
        for tid, game_base in current_base.items():
            history["known_signatures"][tid] = compute_signature(game_base)
    else:
        # 4. Detect deleted topics (was in known_signatures, but missing from current catalog)
        known_tids = set(history["known_signatures"].keys())
        deleted_now = known_tids - current_tids
        for tid in deleted_now:
            print(f"Topic {tid} was deleted from catalog.")
            history["deleted"][tid] = now
            del history["known_signatures"][tid]
            if tid in history["topics"]:
                del history["topics"][tid]

        # 5. Detect additions and modifications
        for tid, game_base in current_base.items():
            sig = compute_signature(game_base)
            prev_sig = history["known_signatures"].get(tid)

            if prev_sig != sig:
                # Topic is new or updated
                is_new = prev_sig is None
                action = "added" if is_new else "updated"
                print(f"Topic {tid} ({game_base.get('title', '')}) {action}.")

                history["known_signatures"][tid] = sig
                per_lang_games = {}
                for lang, cat in current_catalogs.items():
                    if tid in cat:
                        per_lang_games[lang] = cat[tid]

                history["topics"][tid] = {
                    "time": now,
                    "sig": sig,
                    "games": per_lang_games,
                }

                # If it was previously marked deleted, restore it
                if tid in history["deleted"]:
                    del history["deleted"][tid]

    # 6. Build the unified catalog_diff.json structure
    diff_payload = {
        "version": 1,
        "generated_at": now,
        "window_hours": 72,
        "deleted_topic_ids": sorted(list(history["deleted"].keys())),
        "added_or_updated": {lang: [] for lang in LANG_FILES},
    }

    # Sort topics by time desc (most recent first), then topic_id
    sorted_topics = sorted(
        history["topics"].items(),
        key=lambda item: (item[1].get("time", 0), item[0]),
        reverse=True,
    )

    for tid, item in sorted_topics:
        games_dict = item.get("games", {})
        for lang in LANG_FILES:
            if lang in games_dict:
                diff_payload["added_or_updated"][lang].append(games_dict[lang])

    # 7. Write catalog_diff.json (compact, indent=2)
    with open(OUTPUT_DIFF, "w", encoding="utf-8") as f:
        json.dump(diff_payload, f, ensure_ascii=False, indent=2)

    # 8. Write diff_history.json
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False)

    print(
        f"Updated {OUTPUT_DIFF.name}: {len(diff_payload['deleted_topic_ids'])} deleted, "
        f"{len(history['topics'])} added/updated entries in 72h window."
    )
    return diff_payload


if __name__ == "__main__":
    update_catalog_diff()
