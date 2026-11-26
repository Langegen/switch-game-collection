"""Apply exact, display-only terminology without changing record identity."""
import re

DISPLAY_FIELDS = ("genre", "interface_lang", "voice_lang", "multiplayer", "performance", "description")


def translate_genre_terms(value, mapping):
    if not isinstance(value, str):
        return value
    parts = re.split(r"([,/;|、，；])", value)
    for i in range(0, len(parts), 2):
        part = parts[i]
        label = mapping.get(part.strip().casefold())
        if label:
            left = len(part) - len(part.lstrip())
            right = len(part.rstrip())
            parts[i] = part[:left] + label + part[right:]
    return "".join(parts)


def apply_display_terms(record, terms, description_source=None):
    """Mutate only display fields. Unknown and ambiguous text stays intact."""
    changed = []
    for field in DISPLAY_FIELDS:
        old = record.get(field)
        if not isinstance(old, str):
            continue
        mapping = terms.get(field, {})
        if field == "genre":
            new = translate_genre_terms(old, mapping)
        elif field == "description":
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
