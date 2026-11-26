"""Offline metadata coverage audit. Script detection flags review, not translation quality."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re

FIELDS = ("title", "description", "genre", "developer", "publisher", "year",
          "image_format", "interface_lang", "voice_lang", "multiplayer", "performance")
IDENTITY = ("title_id", "topic_id", "url", "magnet", "size", "version", "update_version", "titles")
HAN = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
CYRILLIC = re.compile(r"[\u0400-\u052f]")
LATIN = re.compile(r"[A-Za-z]")
PLACEHOLDERS = {"unknown", "n/a", "-", "?", "未知", "未提供"}
NEUTRAL = re.compile(r"(?:\d{4}(?:[-./]\d{1,2}){0,2}|\d+(?:\.\d+)*|(?:NSP|NSZ|XCI|XCZ|NRO|OVL|DLC)(?:\s*[/,;+]\s*(?:NSP|NSZ|XCI|XCZ|NRO|OVL|DLC))*)", re.I)


def classify(value, locale):
    if value is None or not str(value).strip() or str(value).strip().lower() in PLACEHOLDERS:
        return "missing"
    text = str(value).strip()
    if NEUTRAL.fullmatch(text):
        return "neutral"
    if not locale.lower().startswith("ru") and CYRILLIC.search(text):
        return "cyrillic_review"
    if locale.lower().replace("_", "-").startswith("zh"):
        if HAN.search(text):
            return "han_present"
        if LATIN.search(text):
            return "latin_review"
    return "other"


def catalog_rows(data):
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("games", "entries"):
            if isinstance(data.get(key), list):
                return data[key]
    raise ValueError("Expected an array or a catalog object containing games/entries")


def audit_catalog(data, locale, include_indices=False):
    rows = catalog_rows(data)
    result = {"locale": locale, "entries": len(rows), "fields": {}}
    for field in FIELDS:
        counts = Counter()
        review = []
        for i, row in enumerate(rows):
            if not isinstance(row, dict):
                raise ValueError(f"Invalid catalog entry at index {i}")
            category = classify(row.get(field), locale)
            counts[category] += 1
            if include_indices and (category.endswith("_review") or category == "missing"):
                review.append(i)
        result["fields"][field] = dict(sorted(counts.items()))
        if include_indices:
            result["fields"][field]["review_indices"] = review
    return result


def identity_diff(reference, candidate):
    original, updated = catalog_rows(reference), catalog_rows(candidate)
    if len(original) != len(updated):
        return {"entry_count": {"reference": len(original), "candidate": len(updated)}}
    differences = Counter()
    for a, b in zip(original, updated):
        for key in IDENTITY:
            if a.get(key) != b.get(key):
                differences[key] += 1
    return dict(sorted(differences.items()))


def audit_homebrew(index, locale="zh-Hans"):
    result = {}
    for section, entries in (("packages", index.get("packages", [])),
                             ("fortheusers", index.get("fortheusers", {}).values())):
        rows = list(entries)
        count = sum(bool(str((p.get("description_i18n") or {}).get(locale) or "").strip()) for p in rows)
        result[section] = {"total": len(rows), "localized_description": count,
                           "missing_locale_description": len(rows) - count}
    return result


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path)
    parser.add_argument("--locale", default="zh-Hans")
    parser.add_argument("--reference", type=Path, help="Original catalog for identity verification")
    parser.add_argument("--before", type=Path, help="Previous localized catalog for coverage comparison")
    parser.add_argument("--homebrew", type=Path)
    parser.add_argument("--review-indices", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not args.catalog and not args.homebrew:
        parser.error("Specify --catalog or --homebrew")
    if (args.reference or args.before) and not args.catalog:
        parser.error("--reference and --before require --catalog")
    report = {"note": "Script-based candidates for review; names and technical labels need human judgment."}
    different = False
    if args.catalog:
        catalog = load(args.catalog)
        report["catalog"] = audit_catalog(catalog, args.locale, args.review_indices)
        if args.before:
            report["before"] = audit_catalog(load(args.before), args.locale)
        if args.reference:
            report["identity_differences"] = identity_diff(load(args.reference), catalog)
            different = bool(report["identity_differences"])
    if args.homebrew:
        report["homebrew"] = audit_homebrew(load(args.homebrew), args.locale)
    output = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 1 if different else 0


if __name__ == "__main__":
    raise SystemExit(main())
