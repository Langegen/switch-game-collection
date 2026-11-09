#!/usr/bin/env python3
"""Builds homebrew.json for the TorrentShopNX homebrew store.

Sources:
  * Homebrew App Store (switch.cdn.fortheusers.org/repo.json): every package's
    manifest is checked; packages that write to the bootloader, Atmosphere core
    or other forbidden places are hidden, the rest get their kinds
    (app / overlay / sysmodule).
  * homebrew-sources.json: hand-picked GitHub projects (missing or outdated in
    fortheusers). These are approved by being in the list.
  * Discovery (needs GITHUB_TOKEN): GitHub topics and GameBrew. A release with a
    single .nro or .ovl is added automatically ("auto": true). Everything else
    goes to homebrew/candidates.md for manual review.

The console downloads homebrew.json only; it never calls the GitHub API.
Path rules mirror TorrentShopNX source/catalog/homebrew_package.cpp; the shared
table is homebrew/path_rules.txt (run with --selftest).

Usage:
  python scripts/homebrew_indexer.py                 # full run (discovery if GITHUB_TOKEN is set)
  python scripts/homebrew_indexer.py --no-discovery
  python scripts/homebrew_indexer.py --discovery-limit 10
  python scripts/homebrew_indexer.py --selftest
"""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import fnmatch
import hashlib
import io
import json
import os
import re
import struct
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES_FILE = ROOT / "homebrew-sources.json"
OUTPUT_FILE = ROOT / "homebrew.json"
DATA_DIR = ROOT / "homebrew"
STATE_FILE = DATA_DIR / "state.json"
ICONS_DIR = DATA_DIR / "icons"
CANDIDATES_FILE = DATA_DIR / "candidates.md"
PATH_RULES_FILE = DATA_DIR / "path_rules.txt"

FTU_CDN = "https://switch.cdn.fortheusers.org"
RAW_BASE = "https://raw.githubusercontent.com/Langegen/switch-game-collection/main/"
USER_AGENT = "TorrentShopNX-homebrew-indexer (+https://github.com/Langegen/TorrentShopNX)"

MAX_ASSET_BYTES = 200 * 1024 * 1024
DISCOVERY_TOPICS = [
    "nintendo-switch-homebrew", "switch-homebrew", "libnx", "tesla-overlay",
    "ultrahand", "ultrahand-overlay", "switch-overlay", "nx-homebrew",
    "switch-sysmodule", "atmosphere-sysmodule",
]
GAMEBREW_LIST = "https://www.gamebrew.org/wiki/List_of_Switch_homebrew_applications"
GAMEBREW_PAGES_PER_RUN = 40

# Folders that are part of the SD layout (used to find a wrapping folder in zips).
SD_TOP = {
    "switch", "atmosphere", "config", "bootloader", "themes", "roms", "tico",
    "emummc", "retroarch", "payloads", "nintendo", "sxos", "ftpd", "lakka",
}
DOC_RE = re.compile(r"^(readme|license|licence|changelog|copying|notice)(\.[a-z0-9]+)?$|\.(md|txt|pdf|png|jpg)$", re.I)

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()


def log(msg: str) -> None:
    print(msg, flush=True)


# ---------------------------------------------------------------------------
# Paths (mirror of homebrew_package.cpp)

def normalize_rel_path(p: str) -> str:
    s = p.strip().replace("\\", "/")
    if s.lower().startswith("sdmc:"):
        s = s[5:]
    if ":" in s:
        return ""
    out = []
    for seg in s.split("/"):
        if seg in (".", ".."):
            return ""
        if seg:
            out.append(seg)
    return "/".join(out)


HEX16 = re.compile(r"^[0-9a-fA-F]{16}$")


def check_install_path(rel: str) -> tuple[str, str]:
    """Returns (verdict, reason); verdict is allowed / warn / forbidden."""
    p = normalize_rel_path(rel).lower()
    if not p:
        return "forbidden", "unsafe path"
    if "/" not in p:
        if p.endswith((".bin", ".dat", ".ini", ".kip", ".nsp", ".bmp")):
            return "forbidden", "boot file in SD root"
        return "warn", "file in SD root"
    top = p.split("/", 1)[0]
    if top == "bootloader":
        return "forbidden", "bootloader"
    if top in ("emummc", "nintendo"):
        return "forbidden", "system data"
    if top == "payloads":
        return "forbidden", "payloads"
    if p.startswith("switch/torrentshopnx/"):
        return "forbidden", "TorrentShopNX files"
    if p.startswith("switch/appstore/.get/"):
        return "forbidden", "package registry"
    if top == "atmosphere":
        core = ("atmosphere/package3", "atmosphere/stratosphere.romfs", "atmosphere/fusee",
                "atmosphere/hbl.nsp", "atmosphere/kips/", "atmosphere/reboot_payload.bin",
                "atmosphere/exosphere")
        if p.startswith(core):
            return "forbidden", "Atmosphere core"
        if p.startswith("atmosphere/contents/"):
            rest = p[len("atmosphere/contents/"):]
            if "/" not in rest:
                return "warn", "atmosphere/contents"
            tid = rest.split("/", 1)[0]
            if not HEX16.match(tid):
                return "warn", "atmosphere/contents"
            if tid.startswith("01000000000") and int(tid, 16) <= 0x01000000000010FF:
                return "warn", "system title override"
            return "allowed", ""
        return "warn", "atmosphere"
    return "allowed", ""


RANK = {"allowed": 0, "warn": 1, "forbidden": 2}


def analyze_files(paths: list[str]) -> dict:
    kinds: set[str] = set()
    worst, worst_path, worst_reason = "allowed", "", ""
    tids = []
    for path in paths:
        verdict, reason = check_install_path(path)
        if RANK[verdict] > RANK[worst]:
            worst, worst_path, worst_reason = verdict, path, reason
        low = path.lower()
        if low.startswith("switch/.overlays/") and low.endswith(".ovl"):
            kinds.add("overlay")
        elif low.startswith("switch/") and low.endswith(".nro"):
            kinds.add("app")
        elif low.startswith("atmosphere/contents/") and low.endswith("/exefs.nsp"):
            tid = low[20:36]
            if HEX16.match(tid) and len(low) == 20 + 16 + 10:
                kinds.add("sysmodule")
                tids.append(tid.upper())
    simple = len(paths) == 1 and worst == "allowed" and kinds in ({"app"}, {"overlay"})
    return {"kinds": sorted(kinds), "worst": worst, "worst_path": worst_path,
            "worst_reason": worst_reason, "simple": simple, "tids": tids}


def parse_manifest(text: str) -> list[tuple[str, str]] | None:
    """[(op, path)], None when a path is unsafe."""
    out = []
    for line in text.splitlines():
        line = line.strip()
        if len(line) < 3 or line[1] != ":" or line[0] not in "UEGL":
            continue
        path = normalize_rel_path(line[2:])
        if not path:
            return None
        out.append((line[0], path))
    return out


def selftest() -> int:
    fails = rows = 0
    for line in PATH_RULES_FILE.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#") or "\t" not in line:
            continue
        want, path = line.split("\t", 1)
        got, reason = check_install_path(path)
        rows += 1
        if got != want:
            fails += 1
            log(f"FAIL {path}: got {got} ({reason}), expected {want}")
    log(f"path rules: {rows - fails}/{rows} ok")
    return 1 if fails or rows < 40 else 0


# ---------------------------------------------------------------------------
# Network

def http_get(url: str, *, github_api: bool = False, accept: str | None = None,
             retries: int = 3, timeout: int = 60) -> bytes:
    headers = {"User-Agent": USER_AGENT}
    if github_api:
        headers["Accept"] = accept or "application/vnd.github+json"
        headers["X-GitHub-Api-Version"] = "2022-11-28"
        if GITHUB_TOKEN:
            headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    elif accept:
        headers["Accept"] = accept
    last: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            if e.code in (403, 429) and github_api:
                reset = e.headers.get("X-RateLimit-Reset")
                remaining = e.headers.get("X-RateLimit-Remaining")
                if remaining == "0" and reset:
                    wait = max(0, int(reset) - int(time.time())) + 2
                    if wait > 900:
                        raise
                    log(f"  rate limit, waiting {wait}s")
                    time.sleep(wait)
                    continue
            if e.code in (404, 410, 451):
                raise
            last = e
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            last = e
        time.sleep(2 * (attempt + 1))
    raise last if last else RuntimeError(url)


def gh_api(path: str, **kw) -> dict | list:
    return json.loads(http_get("https://api.github.com" + path, github_api=True, **kw))


def latest_release(repo: str, prerelease: bool = False) -> dict | None:
    try:
        if not prerelease:
            return gh_api(f"/repos/{repo}/releases/latest")
        rels = gh_api(f"/repos/{repo}/releases?per_page=10")
        rels = [r for r in rels if not r.get("draft")]
        return rels[0] if rels else None
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


# ---------------------------------------------------------------------------
# NRO / NACP

def parse_nro(data: bytes) -> dict | None:
    """Icon and NACP of an NRO (or .ovl, same format). None if not an NRO."""
    if len(data) < 0x80 or data[0x10:0x14] != b"NRO0":
        return None
    size = struct.unpack_from("<I", data, 0x18)[0]
    info: dict = {}
    if len(data) >= size + 0x38 and data[size:size + 4] == b"ASET":
        icon_off, icon_size, nacp_off, nacp_size = struct.unpack_from("<QQQQ", data, size + 8)
        if icon_size and size + icon_off + icon_size <= len(data):
            info["icon"] = data[size + icon_off:size + icon_off + icon_size]
        if nacp_size >= 0x4000 and size + nacp_off + nacp_size <= len(data):
            nacp = data[size + nacp_off:size + nacp_off + nacp_size]
            for i in (0, 1) + tuple(range(2, 16)):
                name = _cstr(nacp[i * 0x300:i * 0x300 + 0x200])
                if name:
                    info["title"] = name
                    info["author"] = _cstr(nacp[i * 0x300 + 0x200:i * 0x300 + 0x300])
                    break
            info["version"] = _cstr(nacp[0x3060:0x3070])
    return info


def _cstr(b: bytes) -> str:
    s = b.split(b"\0", 1)[0].decode("utf-8", errors="ignore").strip()
    return s if s.isprintable() else ""


def save_icon(name: str, icon: bytes | None) -> str:
    if not icon:
        return ""
    ext = ".jpg" if icon[:2] == b"\xff\xd8" else ".png" if icon[:4] == b"\x89PNG" else ""
    if not ext:
        return ""
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", name)
    ICONS_DIR.mkdir(parents=True, exist_ok=True)
    path = ICONS_DIR / (safe + ext)
    if not path.exists() or path.read_bytes() != icon:
        path.write_bytes(icon)
    return RAW_BASE + "homebrew/icons/" + urllib.parse.quote(safe + ext)


# ---------------------------------------------------------------------------
# Release assets -> package

def clean_version(tag: str) -> str:
    t = tag.strip()
    return t[1:] if len(t) > 1 and t[0] in "vV" and t[1].isdigit() else t


def pick_asset(release: dict, pattern: str | None) -> tuple[dict | None, str]:
    assets = [a for a in release.get("assets", []) if a.get("state", "uploaded") == "uploaded"]
    if pattern:
        hits = [a for a in assets if fnmatch.fnmatch(a["name"].lower(), pattern.lower())]
        return (hits[0], "") if len(hits) == 1 else (None, f"{len(hits)} assets match {pattern}")
    usable = [a for a in assets if a["name"].lower().endswith((".nro", ".ovl", ".zip"))]
    if len(usable) == 1:
        return usable[0], ""
    single = [a for a in usable if a["name"].lower().endswith((".nro", ".ovl"))]
    if len(single) == 1 and not any(a["name"].lower().endswith(".zip") for a in usable):
        return single[0], ""
    return None, "assets: " + ", ".join(a["name"] for a in assets) if assets else "no assets"


def zip_layout(zf: zipfile.ZipFile) -> tuple[str, list[str]]:
    """(zip_root, file paths on SD) for an SD-layout zip."""
    names = [n.replace("\\", "/") for n in zf.namelist() if not n.endswith("/")]
    names = [n for n in names if not n.startswith("__MACOSX/")]
    root = ""
    for _ in range(2):
        rel = [n[len(root):] for n in names]
        firsts = {r.split("/", 1)[0] for r in rel}
        if len(firsts) == 1 and all("/" in r for r in rel) and next(iter(firsts)).lower() not in SD_TOP:
            root += next(iter(firsts)) + "/"
        else:
            break
    files = []
    for n in names:
        rel = n[len(root):]
        if "/" not in rel and DOC_RE.search(rel):
            continue  # README, LICENSE... next to the SD folders: not installed
        files.append(rel)
    return root, files


def single_file_dest(asset_name: str, cfg: dict, repo: str, ftu_binary: str | None) -> str:
    """Path for a release that is one .nro/.ovl. Named after the repo, not the
    asset: assets often carry the version ("tool-v1.2.nro"), and the path must
    stay the same between versions."""
    if cfg.get("dest"):
        return normalize_rel_path(cfg["dest"])
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", (cfg.get("repo") or repo).split("/", 1)[1])
    if asset_name.lower().endswith(".ovl"):
        return f"switch/.overlays/{stem}.ovl"
    if ftu_binary and ftu_binary.lower().endswith(".nro"):
        return normalize_rel_path(ftu_binary)  # same place as the fortheusers build
    return f"switch/{stem}/{stem}.nro"


def build_package(name: str, repo: str, release: dict, asset: dict, cfg: dict,
                  cache: dict, ftu_binary: str | None) -> tuple[dict | None, str]:
    """Downloads (or reuses cached) asset data. Returns (package, problem)."""
    key = f"{asset['id']}:{asset.get('updated_at', '')}"
    entry = cache.get(repo)
    if not entry or entry.get("asset_key") != key:
        if asset.get("size", 0) > MAX_ASSET_BYTES:
            return None, f"asset too big ({asset['size'] // (1024 * 1024)} MB)"
        data = http_get(asset["browser_download_url"], timeout=300)
        entry = {"asset_key": key, "sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}
        lname = asset["name"].lower()
        nro_bytes = None
        if lname.endswith(".zip"):
            try:
                zf = zipfile.ZipFile(io.BytesIO(data))
            except zipfile.BadZipFile:
                return None, "broken zip"
            root, files = zip_layout(zf)
            if cfg.get("zip_root") is not None:
                root = normalize_rel_path(cfg["zip_root"])
                root = root + "/" if root else ""
                files = [n.replace("\\", "/")[len(root):] for n in zf.namelist()
                         if not n.endswith("/") and n.replace("\\", "/").startswith(root)]
            entry.update(type="zip", zip_root=root, files=files,
                         extracted=sum(i.file_size for i in zf.infolist()))
            main = next((f for f in files if f.lower().startswith("switch/") and f.lower().endswith(".nro")), None)
            main = main or next((f for f in files if f.lower().endswith((".nro", ".ovl"))), None)
            if main:
                nro_bytes = zf.read(root + main)
        elif lname.endswith((".nro", ".ovl")):
            # Where it goes is decided below (not cached): see single_file_dest.
            entry.update(type="file", zip_root="", files=[], extracted=len(data))
            nro_bytes = data
        else:
            return None, f"unsupported asset {asset['name']}"
        nro = parse_nro(nro_bytes) if nro_bytes else None
        if nro_bytes and nro is None:
            return None, "not an NRO"
        entry["nacp"] = {k: v for k, v in (nro or {}).items() if k != "icon"}
        entry["icon_url"] = save_icon(name, (nro or {}).get("icon"))
        cache[repo] = entry

    files = entry.get("files") or []
    if entry["type"] == "file":
        files = [single_file_dest(asset["name"], cfg, repo, ftu_binary)]
    if not files:
        return None, "nothing to install"
    a = analyze_files(files)
    if a["worst"] == "forbidden":
        return None, f"forbidden path {a['worst_path']} ({a['worst_reason']})"
    nacp = entry.get("nacp", {})
    repo_owner, repo_name = (cfg.get("repo") or repo).split("/", 1)
    # A zip may hold several NROs (Ultrahand ships "Ultrahand Reload"), so its
    # NACP title is not the package title; a single .nro/.ovl names itself.
    nacp_title = nacp.get("title") if entry["type"] == "file" else ""
    nacp_author = nacp.get("author", "")
    if nacp_author.lower() in ("unspecified author", "unknown", "author"):
        nacp_author = ""
    pkg = {
        "name": name,
        "title": cfg.get("title") or cfg.get("ftu_title") or nacp_title or repo_name,
        "author": cfg.get("author") or nacp_author or repo_owner,
        "version": clean_version(release.get("tag_name") or nacp.get("version") or ""),
        "category": cfg.get("category") or guess_category(a, cfg),
        "description": cfg.get("description", ""),
        "changelog": (release.get("body") or "").strip()[:2000],
        "url": f"https://github.com/{repo}",
        "repo": repo.lower(),
        "updated": (release.get("published_at") or "")[:10],
        "download_url": asset["browser_download_url"],
        "download_type": entry["type"],
        "sha256": entry["sha256"],
        "filesize": entry["size"],
        "extracted": entry["extracted"],
        # Settings are written only when missing, so updates keep the user's config.
        "files": [("G: " if f.lower().startswith("config/") else "U: ") + f for f in files],
        "kinds": a["kinds"],
    }
    if entry.get("zip_root"):
        pkg["zip_root"] = entry["zip_root"]
    if entry.get("icon_url"):
        pkg["icon_url"] = entry["icon_url"]
    for k in ("depends", "description_i18n", "license"):
        if cfg.get(k):
            pkg[k] = cfg[k]
    if not pkg["version"]:
        return None, "no version"
    return pkg, ""


def guess_category(a: dict, cfg: dict) -> str:
    topics = {t.lower() for t in cfg.get("topics", [])}
    text = (cfg.get("description", "") + " " + " ".join(topics)).lower()
    if "sysmodule" in a["kinds"] or "overlay" in a["kinds"]:
        return "advanced"
    if "emulator" in text or "emu" in topics:
        return "emu"
    if "game" in text:
        return "game"
    return "tool"


# ---------------------------------------------------------------------------
# fortheusers

def load_fortheusers(state: dict) -> tuple[list[dict], dict, list[str]]:
    """(packages, meta for homebrew.json, hidden names)."""
    repo = json.loads(http_get(FTU_CDN + "/repo.json", timeout=120))
    packages = repo.get("packages", [])
    cache = state.setdefault("fortheusers", {})
    todo = [p for p in packages if cache.get(p["name"], {}).get("version") != p.get("version")]
    log(f"fortheusers: {len(packages)} packages, {len(todo)} manifests to fetch")

    def fetch(p: dict) -> tuple[str, str | None]:
        url = f"{FTU_CDN}/packages/{urllib.parse.quote(p['name'])}/manifest.install"
        try:
            return p["name"], http_get(url, timeout=60).decode("utf-8", errors="replace")
        except Exception as e:  # noqa: BLE001 - one bad package must not stop the run
            log(f"  manifest {p['name']}: {e}")
            return p["name"], None

    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
        for name, text in ex.map(fetch, todo):
            pkg = next(p for p in todo if p["name"] == name)
            if text is None:
                continue
            entries = parse_manifest(text)
            if entries is None:
                cache[name] = {"version": pkg.get("version"), "worst": "forbidden",
                               "reason": "unsafe path", "kinds": []}
                continue
            a = analyze_files([p for _, p in entries])
            cache[name] = {"version": pkg.get("version"), "worst": a["worst"],
                           "reason": f"{a['worst_path']} ({a['worst_reason']})" if a["worst"] != "allowed" else "",
                           "kinds": a["kinds"]}

    meta, hidden = {}, []
    names = {p["name"] for p in packages}
    for name in list(cache):
        if name not in names:
            del cache[name]
    for p in packages:
        c = cache.get(p["name"])
        if not c:
            continue
        if c["worst"] == "forbidden":
            hidden.append(p["name"])
        else:
            meta[p["name"]] = {"kinds": c["kinds"]}
    return packages, meta, hidden


def repo_of(url: str) -> str:
    m = re.search(r"(?:^|//|www\.)github\.com/([^/?#]+)/([^/?#]+)", url or "", re.I)
    if not m:
        return ""
    return f"{m.group(1)}/{re.sub(r'\.git$', '', m.group(2))}".lower()


# ---------------------------------------------------------------------------
# Discovery

def discover_topics(known: set[str], limit_pages: int) -> dict[str, dict]:
    since = (dt.date.today() - dt.timedelta(days=365)).isoformat()
    found: dict[str, dict] = {}
    for topic in DISCOVERY_TOPICS:
        for page in range(1, limit_pages + 1):
            q = urllib.parse.quote(f"topic:{topic} pushed:>={since} fork:false archived:false")
            try:
                res = gh_api(f"/search/repositories?q={q}&sort=updated&per_page=100&page={page}")
            except urllib.error.HTTPError as e:
                log(f"  search {topic}: {e}")
                break
            items = res.get("items", [])
            for it in items:
                full = it["full_name"].lower()
                if full not in known:
                    found.setdefault(full, it)
            time.sleep(2.5 if GITHUB_TOKEN else 6.5)  # search API: 30 (10 without a token) requests a minute
            if len(items) < 100:
                break
    log(f"discovery: {len(found)} new repos from topics")
    return found


def discover_gamebrew(state: dict, known: set[str]) -> set[str]:
    cache = state.setdefault("gamebrew", {})
    try:
        html = http_get(GAMEBREW_LIST, timeout=60).decode("utf-8", errors="ignore")
    except Exception as e:  # noqa: BLE001
        log(f"  gamebrew list: {e}")
        return set()
    pages = sorted(set(re.findall(r'href="(/wiki/[^"#?:]+_Switch)"', html)))
    new_pages = [p for p in pages if p not in cache][:GAMEBREW_PAGES_PER_RUN]
    for page in new_pages:
        try:
            body = http_get("https://www.gamebrew.org" + page, timeout=60).decode("utf-8", errors="ignore")
            repos = {repo_of(u) for u in re.findall(r'https?://github\.com/[^\s"<>]+', body)}
            repos.discard("")
            cache[page] = sorted(repos)[:3]
        except Exception as e:  # noqa: BLE001
            log(f"  gamebrew {page}: {e}")
        time.sleep(1)
    out = {r for rs in cache.values() for r in rs} - known
    log(f"discovery: {len(pages)} GameBrew pages ({len(new_pages)} new), {len(out)} repos not known yet")
    return out


# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--no-discovery", action="store_true")
    ap.add_argument("--discovery-limit", type=int, default=400, help="max new repos to check per run")
    ap.add_argument("--search-pages", type=int, default=3)
    ap.add_argument("--force-discovery", action="store_true",
                    help="run discovery without GITHUB_TOKEN (local tests; keep the limits small)")
    args = ap.parse_args()

    if args.selftest:
        return selftest()
    if selftest():
        return 1

    sources = json.loads(SOURCES_FILE.read_text(encoding="utf-8"))
    state = json.loads(STATE_FILE.read_text(encoding="utf-8")) if STATE_FILE.exists() else {}
    today = dt.date.today().isoformat()
    first_seen = state.setdefault("first_seen", {})
    rejected = state.setdefault("rejected", {})
    asset_cache = state.setdefault("assets", {})

    ftu_packages, ftu_meta, ftu_hidden = load_fortheusers(state)
    ftu_by_repo = {}
    for p in ftu_packages:
        r = repo_of(p.get("url", ""))
        if r:
            ftu_by_repo.setdefault(r, p)

    hidden = {h.lower() for h in sources.get("hidden", [])} | {h.lower() for h in ftu_hidden}
    for name, extra in sources.get("fortheusers", {}).items():
        ftu_meta.setdefault(name, {}).update(extra)

    packages: list[dict] = []
    problems: list[str] = []
    manual_repos = set()

    # Hand-picked projects.
    for cfg in sources.get("packages", []):
        repo = cfg["repo"].lower()
        manual_repos.add(repo)
        ftu = ftu_by_repo.get(repo)
        name = cfg.get("name") or (ftu["name"] if ftu else cfg["repo"].split("/")[1])
        if ftu and not cfg.get("title"):
            cfg = dict(cfg, ftu_title=ftu.get("title", ""))
        try:
            rel = latest_release(cfg["repo"], cfg.get("prerelease", False))
            if not rel:
                problems.append(f"| {cfg['repo']} | нет релизов |")
                continue
            asset, why = pick_asset(rel, cfg.get("asset"))
            if not asset:
                problems.append(f"| {cfg['repo']} | {why} |")
                continue
            pkg, why = build_package(name, repo, rel, asset, cfg, asset_cache,
                                     ftu.get("binary") if ftu else None)
        except Exception as e:  # noqa: BLE001
            pkg, why = None, str(e)
        if not pkg:
            problems.append(f"| {cfg['repo']} | {why} |")
            log(f"  manual {cfg['repo']}: {why}")
            continue
        packages.append(pkg)
        log(f"  manual {cfg['repo']}: {pkg['version']} {pkg['kinds']}")

    # Discovery.
    candidates: list[str] = []
    known = manual_repos | set(ftu_by_repo) | {h for h in hidden if "/" in h}
    known.add("langegen/torrentshopnx")
    discovered: dict[str, dict] = {}
    if not args.no_discovery and (GITHUB_TOKEN or args.force_discovery):
        discovered = discover_topics(known, args.search_pages)
        for r in discover_gamebrew(state, known | set(discovered)):
            discovered.setdefault(r, {"full_name": r})
    elif not args.no_discovery:
        log("discovery skipped: no GITHUB_TOKEN")
    # Packages added automatically stay checked even when search no longer
    # returns them (no push for a year) or discovery is off.
    auto_repos = state.setdefault("auto_repos", {})
    for r, info in auto_repos.items():
        if r not in known:
            discovered.setdefault(r, info)

    min_stars = int(sources.get("discovery", {}).get("min_stars", 2))
    checked = 0
    week_ago = (dt.date.today() - dt.timedelta(days=7)).isoformat()
    # Most starred first, so a run that hits the limit spends it on the likeliest ones.
    order = sorted(discovered.items(), key=lambda kv: (-(kv[1].get("stargazers_count") or 0), kv[0]))
    limit_hit = False
    for repo, info in order:
        prev = rejected.get(repo)
        pushed = info.get("pushed_at", "")
        unchanged = prev and (prev.get("pushed_at") == pushed if pushed
                              else prev.get("checked", "") >= week_ago)  # GameBrew: no push date
        if unchanged:
            if prev.get("candidate"):
                candidates.append(prev["candidate"])
            continue
        if checked >= args.discovery_limit:
            limit_hit = True
            continue
        checked += 1
        try:
            rel = latest_release(info.get("full_name", repo))
        except Exception as e:  # noqa: BLE001
            log(f"  {repo}: {e}")
            continue
        record = {"pushed_at": pushed, "checked": today}
        auto_repos.pop(repo, None)  # re-added below if it is still a simple package
        # Renamed or moved repos (GameBrew keeps old links): GitHub answers with
        # the new address; skip it when that one is already known.
        m = re.search(r"github\.com/([^/]+/[^/]+)/releases", (rel or {}).get("html_url", ""))
        if m and m.group(1).lower() != repo:
            canon = m.group(1).lower()
            if canon in known or canon in discovered or canon in auto_repos:
                rejected[repo] = dict(record, alias=canon)
                continue
            info = dict(info, full_name=m.group(1))
        if not rel or not rel.get("assets"):
            rejected[repo] = record
            continue
        stars = info.get("stargazers_count")
        names = [a["name"] for a in rel["assets"]]
        nro_ovl = [a for a in rel["assets"] if a["name"].lower().endswith((".nro", ".ovl"))]
        zips = [a for a in rel["assets"] if a["name"].lower().endswith(".zip")]
        if not nro_ovl and not zips:
            rejected[repo] = record
            continue
        line = (f"| [{info.get('full_name', repo)}](https://github.com/{info.get('full_name', repo)}) | "
                f"{stars if stars is not None else '?'} | {rel.get('tag_name', '')} | "
                f"{(rel.get('published_at') or '')[:10]} | {', '.join(names)[:120]} |")
        simple = len(nro_ovl) == 1 and not zips and (stars is None or stars >= min_stars)
        if simple:
            full_name = info.get("full_name", repo)
            cfg = {"repo": full_name, "description": info.get("description") or "",
                   "topics": info.get("topics", []),
                   "license": (info.get("license") or {}).get("spdx_id", "")}
            name = full_name.split("/")[1]
            try:
                pkg, why = build_package(name, full_name.lower(), rel, nro_ovl[0], cfg, asset_cache, None)
            except Exception as e:  # noqa: BLE001
                pkg, why = None, str(e)
            if pkg and analyze_files([f[3:] for f in pkg["files"]])["simple"]:
                pkg["auto"] = True
                packages.append(pkg)
                rejected.pop(repo, None)
                auto_repos[repo] = {"full_name": full_name, "stargazers_count": stars,
                                    "description": info.get("description") or "",
                                    "topics": info.get("topics", [])}
                log(f"  auto {repo}: {pkg['version']}")
                continue
            log(f"  {repo}: not simple ({why})")
        record["candidate"] = line
        rejected[repo] = record
        candidates.append(line)
    if limit_hit:
        log(f"discovery limit reached ({args.discovery_limit}); the rest is checked next run")

    # Auto packages keep the date they first appeared ("New" badge on the console).
    for pkg in packages:
        if pkg.get("auto"):
            pkg["first_seen"] = first_seen.setdefault(pkg["repo"], today)

    # Packages must have unique names; manual entries win.
    seen, unique = set(), []
    for pkg in packages:
        if pkg["name"].lower() in seen:
            continue
        seen.add(pkg["name"].lower())
        pkg.pop("kinds", None)
        unique.append(pkg)

    out = {
        "format": 1,
        "generated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "hidden": sorted(hidden),
        "overlay_dependencies": sources.get("overlay_dependencies", []),
        "fortheusers": dict(sorted(ftu_meta.items())),
        "packages": sorted(unique, key=lambda p: p["name"].lower()),
    }
    OUTPUT_FILE.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")

    md = ["# Кандидаты в магазин хоумбрю", "",
          f"Обновлено: {today}. Чтобы добавить проект, впишите его в `homebrew-sources.json` (раздел `packages`).", ""]
    if candidates:
        md += ["## Нужна проверка", "", "| Репозиторий | ★ | Версия | Дата | Файлы |", "|---|---|---|---|---|"]
        md += sorted(set(candidates))
    else:
        md += ["Новых кандидатов нет."]
    if problems:
        md += ["", "## Проблемы с проектами из списка", "", "| Репозиторий | Что не так |", "|---|---|"] + problems
    if ftu_hidden:
        md += ["", "## Скрыты из fortheusers (опасные пути)", ""]
        md += [f"- {n}: {state['fortheusers'][n]['reason']}" for n in sorted(ftu_hidden)]
    CANDIDATES_FILE.write_text("\n".join(md) + "\n", encoding="utf-8")

    auto = sum(1 for p in unique if p.get("auto"))
    log(f"homebrew.json: {len(unique)} packages ({auto} auto), {len(hidden)} hidden, "
        f"{len(candidates)} candidates, {len(problems)} problems")
    return 0


if __name__ == "__main__":
    sys.exit(main())
