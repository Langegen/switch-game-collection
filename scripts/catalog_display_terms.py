"""Apply exact, display-only terminology without changing record identity or canonical genres."""
import re

# Keep "genre" out of DISPLAY_FIELDS so canonical English genres remain intact
# for legacy Switch clients and client-side Homebrew/Port detection.
DISPLAY_FIELDS = ("interface_lang", "voice_lang", "multiplayer", "performance", "description")


def apply_display_terms(record, terms, description_source=None):
    """Mutate only non-genre display fields. Unknown and ambiguous text stays intact."""
    changed = []
    for field in DISPLAY_FIELDS:
        old = record.get(field)
        if not isinstance(old, str):
            continue
        mapping = terms.get(field, {})
        if field == "description":
            # A reviewed exact source translation must not overwrite a good
            # existing target-language description.
            if re.search(r"[\u3400-\u4dbf\u4e00-\u9fff]", old):
                continue
            new = mapping.get(old, mapping.get(description_source, old))
        else:
            new = mapping.get(old.strip().casefold(), old)
        if new != old:
            record[field] = new
            changed.append(field)
    return changed
