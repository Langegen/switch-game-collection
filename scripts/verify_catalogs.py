import json
import os
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

CATALOG_FILES = [
    ("RU", "RU_catalog.json"),
    ("EN", "EN_catalog.json"),
    ("ES", "ES_catalog.json"),
    ("FR", "FR_catalog.json"),
    ("DE", "DE_catalog.json"),
    ("IT", "IT_catalog.json"),
    ("PT-BR", "PT_BR_catalog.json"),
    ("ZH-Hans", "ZH_Hans_catalog.json"),
]

EXPECTED_KEYS = [
    "title", "size", "magnet", "topic_id", "url", "year", "genre",
    "developer", "publisher", "image_format", "interface_lang",
    "voice_lang", "performance", "multiplayer", "cover",
    "screenshots", "description", "title_id"
]

def main():
    print("=== Verifying All 8 Nintendo Switch Catalogs ===")

    with open("RU_catalog.json", "r", encoding="utf-8") as f:
        ru_catalog = json.load(f)
    base_count = len(ru_catalog)
    print(f"Base RU catalog items: {base_count}")

    for lang, fname in CATALOG_FILES:
        if not os.path.exists(fname):
            print(f"  [MISSING] {lang} ({fname}) does not exist yet.")
            continue

        with open(fname, "r", encoding="utf-8") as f:
            cat = json.load(f)

        print(f"\n--- Checking {lang} ({fname}) ---")
        print(f"  Count: {len(cat)} items")
        assert len(cat) == base_count, f"Count mismatch in {fname}: {len(cat)} != {base_count}"

        # 1:1 check on critical fields
        for i in range(base_count):
            assert list(cat[i].keys()) == EXPECTED_KEYS, f"Keys mismatch at index {i} in {fname}"
            assert cat[i]["title_id"] == ru_catalog[i]["title_id"], f"Title ID mismatch at index {i} in {fname}"
            assert cat[i]["magnet"] == ru_catalog[i]["magnet"], f"Magnet mismatch at index {i} in {fname}"
            assert cat[i]["topic_id"] == ru_catalog[i]["topic_id"], f"Topic ID mismatch at index {i} in {fname}"
            assert cat[i]["url"] == ru_catalog[i]["url"], f"URL mismatch at index {i} in {fname}"
            assert cat[i]["size"] == ru_catalog[i]["size"], f"Size mismatch at index {i} in {fname}"
            assert cat[i]["cover"] == ru_catalog[i]["cover"], f"Cover mismatch at index {i} in {fname}"

        print(f"  ✓ All {base_count} items matched 1:1 in structure, keys, order, and identifiers!")

        # Cyrillic audit on non-RU catalogs
        if lang != "RU":
            cyr_fields = {}
            for field in ["year", "genre", "image_format", "interface_lang", "voice_lang", "performance", "multiplayer"]:
                cyr_items = [cat[i][field] for i in range(base_count) if re.search(r"[\u0400-\u04FF]", str(cat[i][field]))]
                if cyr_items:
                    cyr_fields[field] = len(cyr_items)

            if cyr_fields:
                print(f"  Cyrillic remaining in fields: {cyr_fields}")
            else:
                print(f"  ✓ 0 Cyrillic in all structured fields!")

        # Sample preview
        sample_idx = 0
        print(f"  Sample Item #0:")
        print(f"    Title:       {cat[sample_idx]['title']}")
        print(f"    Year:        {cat[sample_idx]['year']}")
        print(f"    Genre:       {cat[sample_idx]['genre']}")
        print(f"    Format:      {cat[sample_idx]['image_format']}")
        print(f"    Interface:   {cat[sample_idx]['interface_lang']}")
        print(f"    Voice:       {cat[sample_idx]['voice_lang']}")
        print(f"    Performance: {cat[sample_idx]['performance']}")
        print(f"    Multiplayer: {cat[sample_idx]['multiplayer']}")
        print(f"    Desc:        {cat[sample_idx]['description'][:60]}...")

    print("\n✓ Verification finished.")

if __name__ == "__main__":
    main()
