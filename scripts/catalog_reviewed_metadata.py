"""Reviewed display aliases and summaries; never overwrite identifiers or hide originals."""
import re

SUMMARY_PREFIX = "中文摘要（保留原文）："
HAN = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
CYRILLIC = re.compile(r"[\u0400-\u052f]")
LATIN = re.compile(r"[A-Za-z]")
BRACKETS = re.compile(r"\s*(?:\[[^\[\]]*\]\s*)+$")


def has_chinese_prose(text):
    """Conservative script check, not a claim about semantic translation quality."""
    if not isinstance(text, str) or CYRILLIC.search(text):
        return False
    han = len(HAN.findall(text))
    latin = len(LATIN.findall(text))
    return han > 0 and latin <= max(12, han * 3)


def apply_reviewed_metadata(record, reviewed):
    changed = []
    original = record.get("title")
    if isinstance(original, str):
        base = BRACKETS.sub("", original).strip()
        entry = reviewed.get("titles", {}).get(base.casefold())
        tid = record.get("title_id")
        if entry and isinstance(tid, str) and tid.upper() in entry["title_ids"]:
            if not HAN.search(base):
                record["title"] = entry["display_name"] + " / " + original
                changed.append("title")
            desc = record.get("description")
            if isinstance(desc, str) and desc.strip() and not desc.startswith(SUMMARY_PREFIX) and not has_chinese_prose(desc):
                record["description"] = SUMMARY_PREFIX + "\n" + entry["summary"] + "\n\n原文：\n" + desc
                changed.append("description")
    for field in ("developer", "publisher"):
        old = record.get(field)
        if not isinstance(old, str):
            continue
        alias = reviewed.get("entities", {}).get(old.strip().casefold())
        if alias and not HAN.search(old):
            record[field] = alias + "（" + old + "）"
            changed.append(field)
    return changed
