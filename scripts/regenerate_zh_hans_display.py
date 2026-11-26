"""Regenerate reviewed Chinese display metadata from an existing catalog offline."""
import argparse
from collections import Counter
import json
from pathlib import Path

from audit_localization import audit_catalog
from catalog_display_terms import apply_display_terms
from catalog_reviewed_metadata import apply_reviewed_metadata

HERE = Path(__file__).resolve().parent
ALLOWED = {"title", "description", "genre", "interface_lang", "voice_lang",
           "multiplayer", "performance", "developer", "publisher"}


def transform(records, terms, reviewed):
    out = []
    counts = Counter()
    protected = 0
    changed_records = 0
    for original in records:
        record = dict(original)
        apply_display_terms(record, terms)
        apply_reviewed_metadata(record, reviewed)
        if list(record) != list(original):
            raise ValueError("Catalog schema changed")
        changed = {key for key in original if original[key] != record[key]}
        if changed - ALLOWED:
            raise ValueError("Non-display metadata changed")
        protected += len(set(original) - ALLOWED)
        counts.update(changed)
        changed_records += bool(changed)
        second = dict(record)
        apply_display_terms(second, terms)
        apply_reviewed_metadata(second, reviewed)
        if second != record:
            raise ValueError("Display transformation is not idempotent")
        out.append(record)
    return out, {"records": len(records), "changed_records": changed_records,
                 "changed_fields": dict(counts), "unchanged_non_display_field_comparisons": protected,
                 "non_display_field_differences": 0,
                 "idempotence_checked_records": len(records)}


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if args.catalog.resolve() == args.output.resolve():
        parser.error("Use a separate output path; input is never overwritten.")
    records = load(args.catalog)
    if not isinstance(records, list):
        raise ValueError("Expected the existing catalog array")
    out, report = transform(records, load(HERE / "catalog_display_zh_hans.json"),
                            load(HERE / "catalog_reviewed_zh_hans.json"))
    report["before"] = audit_catalog(records, "zh-Hans")
    report["after"] = audit_catalog(out, "zh-Hans")
    args.output.write_text(json.dumps(out, ensure_ascii=False, indent=4), encoding="utf-8")
    if args.report:
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
