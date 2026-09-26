#!/usr/bin/env python3
import argparse
import concurrent.futures
import io
import json
import os
import re
import ssl
import sys
import time
import urllib.parse
from pathlib import Path

import requests
import urllib3
from PIL import Image

# Disable insecure HTTPS warnings if any image host has an invalid certificate
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
COVERS_DIR = BASE_DIR / "covers"
RU_CATALOG_FILE = BASE_DIR / "RU_catalog.json"
SWITCH_GAMES_FILE = BASE_DIR / "switch_games.json"
SWITCH_GAMES_URL = "https://raw.githubusercontent.com/Langegen/switch-games/main/switch_games.json"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
MAX_HEIGHT = 600
JPEG_QUALITY = 85


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


def load_titledb_fallbacks():
    titledb_by_id = {}
    titledb_by_name = {}

    for fpath in BASE_DIR.glob("*.json"):
        fname = fpath.name
        if "." in fname and fname.split(".")[0] in [
            "AT", "BR", "CA", "CN", "DE", "ES", "FR", "GB", "HK", "IT", "MX", "PT", "RU", "US"
        ]:
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                entries = data.values() if isinstance(data, dict) else data
                for entry in entries:
                    if not isinstance(entry, dict):
                        continue
                    tid = str(entry.get("id") or "").strip().upper()
                    art_url = entry.get("iconUrl") or entry.get("bannerUrl")
                    if tid and art_url and tid not in titledb_by_id:
                        titledb_by_id[tid] = art_url
                    name = normalize_title(entry.get("name"))
                    if name and art_url and name not in titledb_by_name:
                        titledb_by_name[name] = art_url
            except Exception as e:
                print(f"Warning loading TitleDB {fname}: {e}", file=sys.stderr)

    return titledb_by_id, titledb_by_name


def fetch_image_bytes(url, session):
    headers = {"User-Agent": USER_AGENT, "Referer": "https://rutracker.org/"}
    resp = session.get(url, headers=headers, timeout=15, verify=False)
    if resp.status_code == 200 and len(resp.content) > 200:
        return resp.content
    return None


def fetch_via_proxy(url, session):
    quoted = urllib.parse.quote(url, safe="")
    proxy_url = f"https://wsrv.nl/?url={quoted}&output=jpg"
    headers = {"User-Agent": USER_AGENT}
    resp = session.get(proxy_url, headers=headers, timeout=20, verify=False)
    if resp.status_code == 200 and len(resp.content) > 200:
        return resp.content
    return None


def process_image_to_jpg(data_bytes, out_path):
    with Image.open(io.BytesIO(data_bytes)) as img:
        # Convert color mode to RGB with white background for transparent images
        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
            img = img.convert("RGBA")
            bg = Image.new("RGB", img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[3])
            img = bg
        else:
            img = img.convert("RGB")

        # Resize keeping aspect ratio if height > MAX_HEIGHT
        w, h = img.size
        if h > MAX_HEIGHT:
            ratio = MAX_HEIGHT / float(h)
            new_w = max(1, int(w * ratio))
            img = img.resize((new_w, MAX_HEIGHT), Image.Resampling.LANCZOS)

        # Save to temporary file first to guarantee atomic write
        tmp_path = out_path.with_suffix(".tmp.jpg")
        img.save(tmp_path, "JPEG", quality=JPEG_QUALITY, optimize=True)
        if tmp_path.exists():
            if out_path.exists():
                out_path.unlink()
            tmp_path.rename(out_path)
            return True
    return False


def download_single_cover(item, titledb_by_id, titledb_by_name, session, force=False):
    topic_id = str(item.get("topic_id", "")).strip()
    if not topic_id:
        return topic_id, "no_topic_id", None

    target_file = COVERS_DIR / f"{topic_id}.jpg"
    if not force and target_file.exists() and target_file.stat().st_size > 500:
        return topic_id, "skipped", target_file

    original_url = item.get("cover", "").strip()
    title_id = str(item.get("title_id", "")).strip().upper()
    title_norm = normalize_title(item.get("title", ""))

    image_bytes = None
    source_used = None

    # Step 1: Direct download
    if original_url and original_url.startswith("http"):
        try:
            image_bytes = fetch_image_bytes(original_url, session)
            if image_bytes:
                source_used = "direct"
        except Exception:
            image_bytes = None

    # Step 2: Proxy fallback (wsrv.nl Cloudflare proxy)
    if not image_bytes and original_url and original_url.startswith("http"):
        try:
            image_bytes = fetch_via_proxy(original_url, session)
            if image_bytes:
                source_used = "proxy"
        except Exception:
            image_bytes = None

    # Step 3: TitleDB fallback by ID or Name
    if not image_bytes:
        tdb_url = titledb_by_id.get(title_id) or titledb_by_name.get(title_norm)
        if tdb_url:
            try:
                image_bytes = fetch_image_bytes(tdb_url, session)
                if image_bytes:
                    source_used = "titledb"
            except Exception:
                image_bytes = None

    # Step 4: Screenshot fallback
    if not image_bytes:
        screenshots = item.get("screenshots", [])
        if isinstance(screenshots, list) and screenshots:
            for ss_url in screenshots[:2]:
                if ss_url and ss_url.startswith("http"):
                    try:
                        image_bytes = fetch_image_bytes(ss_url, session) or fetch_via_proxy(ss_url, session)
                        if image_bytes:
                            source_used = "screenshot"
                            break
                    except Exception:
                        continue

    if not image_bytes:
        return topic_id, "failed", original_url

    try:
        success = process_image_to_jpg(image_bytes, target_file)
        if success:
            return topic_id, f"downloaded_{source_used}", target_file
        else:
            return topic_id, "failed_processing", original_url
    except Exception as e:
        return topic_id, f"failed_convert: {e}", original_url


def main():
    parser = argparse.ArgumentParser(description="Download and optimize Nintendo Switch covers into repo as JPEG.")
    parser.add_argument("--workers", type=int, default=20, help="Number of parallel worker threads (default: 20)")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of covers to process (0 = all)")
    parser.add_argument("--force", action="store_true", help="Force re-download even if cover exists")
    args = parser.parse_args()

    COVERS_DIR.mkdir(parents=True, exist_ok=True)

    # Load catalog source
    items = []
    if RU_CATALOG_FILE.exists():
        with open(RU_CATALOG_FILE, "r", encoding="utf-8") as f:
            items = json.load(f)
    elif SWITCH_GAMES_FILE.exists():
        with open(SWITCH_GAMES_FILE, "r", encoding="utf-8") as f:
            items = json.load(f)
    else:
        print(f"Fetching switch_games.json from {SWITCH_GAMES_URL}...")
        resp = requests.get(SWITCH_GAMES_URL, timeout=60)
        items = resp.json()

    if args.limit > 0:
        items = items[: args.limit]

    print(f"Total items to check: {len(items)}")
    print(f"Target directory: {COVERS_DIR.resolve()}")
    print("Loading global TitleDB fallbacks...")
    titledb_by_id, titledb_by_name = load_titledb_fallbacks()
    print(f"Loaded {len(titledb_by_id)} entries by ID, {len(titledb_by_name)} entries by name.")

    stats = {
        "skipped": 0,
        "downloaded_direct": 0,
        "downloaded_proxy": 0,
        "downloaded_titledb": 0,
        "downloaded_screenshot": 0,
        "failed": 0,
    }

    start_time = time.time()
    completed = 0
    total = len(items)

    print(f"Starting download with {args.workers} workers...\n")

    # Thread-local session
    sessions = {}

    def get_session():
        import threading
        tid = threading.get_ident()
        if tid not in sessions:
            s = requests.Session()
            adapter = requests.adapters.HTTPAdapter(pool_connections=20, pool_maxsize=20, max_retries=1)
            s.mount("http://", adapter)
            s.mount("https://", adapter)
            sessions[tid] = s
        return sessions[tid]

    def worker_task(item):
        s = get_session()
        return download_single_cover(item, titledb_by_id, titledb_by_name, s, force=args.force)

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(worker_task, item): item for item in items}
        for future in concurrent.futures.as_completed(futures):
            completed += 1
            topic_id, status, extra = future.result()
            if status == "skipped":
                stats["skipped"] += 1
            elif status.startswith("downloaded_"):
                stats[status] = stats.get(status, 0) + 1
            else:
                stats["failed"] += 1
                if completed <= 20 or stats["failed"] <= 10:
                    print(f"[{completed}/{total}] Fail on topic {topic_id}: {status} ({extra})")

            if completed % 500 == 0 or completed == total:
                elapsed = time.time() - start_time
                print(
                    f"Progress: {completed}/{total} ({completed/total*100:.1f}%) | "
                    f"Skipped: {stats['skipped']}, "
                    f"Direct: {stats.get('downloaded_direct', 0)}, "
                    f"Proxy: {stats.get('downloaded_proxy', 0)}, "
                    f"TitleDB: {stats.get('downloaded_titledb', 0)}, "
                    f"SS: {stats.get('downloaded_screenshot', 0)}, "
                    f"Failed: {stats['failed']} | "
                    f"Speed: {completed/elapsed:.1f} items/sec"
                )

    elapsed = time.time() - start_time
    print(f"\nDownload completed in {elapsed:.2f} seconds.")
    print("Final Statistics:")
    for k, v in stats.items():
        print(f"  {k}: {v}")

    # Check total size of covers folder
    total_files = len(list(COVERS_DIR.glob("*.jpg")))
    total_bytes = sum(f.stat().st_size for f in COVERS_DIR.glob("*.jpg"))
    print(f"\nCovers folder status:")
    print(f"  Total .jpg files: {total_files} / {total} ({total_files/total*100:.2f}%)")
    print(f"  Total size on disk: {total_bytes / 1024 / 1024:.2f} MB")
    if total_files > 0:
        print(f"  Average file size: {total_bytes / total_files / 1024:.1f} KB")


if __name__ == "__main__":
    main()
