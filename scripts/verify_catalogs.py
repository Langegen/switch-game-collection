import json
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def main():
    print("=== Verifying RU_catalog.json vs EN_catalog.json ===")
    with open("RU_catalog.json", "r", encoding="utf-8") as f:
        ru = json.load(f)
    with open("EN_catalog.json", "r", encoding="utf-8") as f:
        en = json.load(f)

    print(f"RU count: {len(ru)}")
    print(f"EN count: {len(en)}")
    assert len(ru) == len(en), "Count mismatch between RU and EN catalogs!"

    expected_keys = [
        "title", "size", "magnet", "topic_id", "url", "year", "genre",
        "developer", "publisher", "image_format", "interface_lang",
        "voice_lang", "performance", "multiplayer", "cover",
        "screenshots", "description", "title_id"
    ]

    for i in range(len(ru)):
        assert list(en[i].keys()) == expected_keys, f"Keys mismatch at index {i}"
        assert en[i]["title_id"] == ru[i]["title_id"], f"Title ID mismatch at index {i}"
        assert en[i]["magnet"] == ru[i]["magnet"], f"Magnet mismatch at index {i}"
        assert en[i]["topic_id"] == ru[i]["topic_id"], f"Topic ID mismatch at index {i}"
        assert en[i]["url"] == ru[i]["url"], f"URL mismatch at index {i}"
        assert en[i]["size"] == ru[i]["size"], f"Size mismatch at index {i}"
        assert en[i]["cover"] == ru[i]["cover"], f"Cover mismatch at index {i}"

    print("✓ All 7,075 items matched 1:1 in structure, keys, order, and identifiers!")

    # Check Cyrillic counts across fields in EN catalog
    print("\nCyrillic character audit in EN_catalog.json:")
    for field in ["year", "genre", "image_format", "interface_lang", "voice_lang", "performance", "multiplayer", "developer", "publisher"]:
        cyr_items = [en[i][field] for i in range(len(en)) if re.search(r"[\u0400-\u04FF]", str(en[i][field]))]
        print(f"  Field '{field}': {len(cyr_items)} items with Cyrillic")

    cyr_titles = [en[i]["title"] for i in range(len(en)) if re.search(r"[\u0400-\u04FF]", str(en[i]["title"]))]
    print(f"  Field 'title': {len(cyr_titles)} items with Cyrillic")

    cyr_descs = [en[i]["description"] for i in range(len(en)) if re.search(r"[\u0400-\u04FF]", str(en[i]["description"]))]
    print(f"  Field 'description': {len(cyr_descs)} items with Cyrillic")

    print("\n=== Sample comparison of item 0 and item 100 ===")
    for idx in [0, 1, 2, 10, 100]:
        print(f"\n--- Game #{idx} ---")
        print(f"RU Title:       {ru[idx]['title']}")
        print(f"EN Title:       {en[idx]['title']}")
        print(f"RU Year:        {ru[idx]['year']}")
        print(f"EN Year:        {en[idx]['year']}")
        print(f"RU Format:      {ru[idx]['image_format']}")
        print(f"EN Format:      {en[idx]['image_format']}")
        print(f"RU Interface:   {ru[idx]['interface_lang']}")
        print(f"EN Interface:   {en[idx]['interface_lang']}")
        print(f"RU Voice:       {ru[idx]['voice_lang']}")
        print(f"EN Voice:       {en[idx]['voice_lang']}")
        print(f"RU Performance: {ru[idx]['performance']}")
        print(f"EN Performance: {en[idx]['performance']}")
        print(f"RU Multiplayer: {ru[idx]['multiplayer']}")
        print(f"EN Multiplayer: {en[idx]['multiplayer']}")
        print(f"RU Desc:        {ru[idx]['description'][:80]}...")
        print(f"EN Desc:        {en[idx]['description'][:80]}...")

if __name__ == "__main__":
    main()
