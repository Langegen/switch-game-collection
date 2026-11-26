# Offline Simplified Chinese display regeneration

The existing generated catalog is not a hand-edited source of translations. The reviewed terminology and descriptions live in `scripts/catalog_display_zh_hans.json` and `scripts/catalog_reviewed_zh_hans.json`; the scheduled catalog builder applies both. No new acquisition sources, game files or links are added.

From a checkout containing the existing catalog:

```bash
python -m unittest discover -s scripts -p 'test_*localization.py'
python -m unittest discover -s scripts -p 'test_catalog_*.py'
python -m unittest discover -s scripts -p 'test_regenerate_zh_hans_display.py'
python scripts/regenerate_zh_hans_display.py --catalog ZH_Hans_catalog.json --output ZH_Hans_reviewed.json --report reviewed-report.json
```

The last command writes a separate output and checks field order, identity, non-display field equality and idempotence. It makes no network calls. A Chinese summary is explicitly identified and the original description retained. A Chinese display name does not imply that the game supports Chinese. The recorded in-memory validation is in [zh-hans-display-regeneration.json](zh-hans-display-regeneration.json). The large generated-file upload did not succeed, and full translation and native Switch testing are not yet complete.
