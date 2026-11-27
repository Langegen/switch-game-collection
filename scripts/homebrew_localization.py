"""Apply reviewed Simplified Chinese descriptions without changing package identity."""


def apply_zh_hans(index, overrides):
    """Only enrich existing entries; preserve other languages and non-text fields."""
    counts = {"packages": 0, "fortheusers": 0}
    for section, entries in (("packages", ((p.get("repo", ""), p) for p in index.get("packages", []))),
                             ("fortheusers", index.get("fortheusers", {}).items())):
        lookup = overrides.get(section, {})
        for key, entry in entries:
            value = lookup.get(key.lower())
            if not isinstance(value, str) or not value.strip():
                continue
            translations = entry.setdefault("description_i18n", {})
            if not isinstance(translations, dict):
                raise ValueError(f"Invalid description_i18n for {key}")
            if not translations.get("zh-Hans", "").strip():
                translations["zh-Hans"] = value
                counts[section] += 1
    return counts
