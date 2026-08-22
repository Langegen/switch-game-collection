#!/usr/bin/env python3
import concurrent.futures
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

RU_CATALOG_FILE = "RU_catalog.json"
SWITCH_GAMES_FILE = "switch_games.json"
TITLEDB_US_FILE = "US.en.json"
TITLEDB_GB_FILE = "GB.en.json"
CACHE_FILE = Path(__file__).resolve().parent / "translations_cache.json"

SWITCH_GAMES_URL = "https://raw.githubusercontent.com/Langegen/switch-games/main/switch_games.json"
TITLEDB_US_URL = "https://raw.githubusercontent.com/blawar/titledb/master/US.en.json"
TITLEDB_GB_URL = "https://raw.githubusercontent.com/blawar/titledb/master/GB.en.json"

MONTHS_RU_TO_EN = {
    "января": "January", "январь": "January",
    "февраля": "February", "февраль": "February",
    "марта": "March", "март": "March",
    "апреля": "April", "апрель": "April",
    "мая": "May", "май": "May",
    "июня": "June", "июнь": "June",
    "июля": "July", "июль": "July",
    "августа": "August", "август": "August",
    "сентября": "September", "сентябрь": "September",
    "октября": "October", "октябрь": "October",
    "ноября": "November", "ноябрь": "November",
    "декабря": "December", "декабрь": "December",
    "фeвapль": "February", "aпepль": "April",
    "фepвaль": "February", "oктбяpь": "October",
}

GENRE_MAP = {
    "экшн": "Action",
    "экшен": "Action",
    "ролевая игра": "Role-Playing",
    "ролевая": "Role-Playing",
    "приключения": "Adventure",
    "приключение": "Adventure",
    "пазл": "Puzzle",
    "поиск предметов": "Hidden Object",
    "платформер": "Platformer",
    "шутер от первого лица": "First-Person Shooter",
    "шутер": "Shooter",
    "вечеринка": "Party",
    "настольная игра": "Board Game",
    "настольная": "Board Game",
    "казуальные игры": "Casual",
    "казуальные": "Casual",
    "стратегии": "Strategy",
    "стратегия": "Strategy",
    "пошаговая стратегия": "Turn-Based Strategy",
    "карточная пошаговая": "Turn-Based Card Game",
    "карточная": "Card Game",
    "пошаговая": "Turn-Based",
    "симулятор": "Simulation",
    "гонки": "Racing",
    "метроидвания": "Metroidvania",
    "аркада": "Arcade",
    "хоррор": "Horror",
    "музыка": "Music",
    "спорт": "Sports",
    "файтинг": "Fighting",
    "визуальная новелла": "Visual Novel",
    "песочница": "Sandbox",
    "выживание": "Survival",
    "головоломка": "Puzzle",
    "отдельный режим": "separate mode",
    "ритм-игра": "Rhythm Game",
    "ш-ш": "Shmup / Shooter",
}

LANG_MAP = {
    "русский": "Russian",
    "русская": "Russian",
    "рус": "Russian",
    "английский": "English",
    "английская": "English",
    "англ": "English",
    "японский": "Japanese",
    "японская": "Japanese",
    "яп": "Japanese",
    "китайский": "Chinese",
    "китайская": "Chinese",
    "традиционный китайский": "Traditional Chinese",
    "упрощенный китайский": "Simplified Chinese",
    "корейский": "Korean",
    "корейская": "Korean",
    "французский": "French",
    "французская": "French",
    "немецкий": "German",
    "немецкая": "German",
    "испанский": "Spanish",
    "испанская": "Spanish",
    "итальянский": "Italian",
    "итальянская": "Italian",
    "португальский": "Portuguese",
    "португальская": "Portuguese",
    "бразильский португальский": "Brazilian Portuguese",
    "польский": "Polish",
    "польская": "Polish",
    "нидерландский": "Dutch",
    "голландский": "Dutch",
    "шведский": "Swedish",
    "норвежский": "Norwegian",
    "датский": "Danish",
    "финский": "Finnish",
    "турецкий": "Turkish",
    "арабский": "Arabic",
    "тайский": "Thai",
    "чешский": "Czech",
    "венгерский": "Hungarian",
    "греческий": "Greek",
    "иврит": "Hebrew",
    "украинский": "Ukrainian",
}

CYR_TO_LAT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo",
    "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch",
    "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
    "А": "A", "Б": "B", "В": "V", "Г": "G", "Д": "D", "Е": "E", "Ё": "Yo",
    "Ж": "Zh", "З": "Z", "И": "I", "Й": "Y", "К": "K", "Л": "L", "М": "M",
    "Н": "N", "О": "O", "П": "P", "Р": "R", "С": "S", "Т": "T", "У": "U",
    "Ф": "F", "Х": "Kh", "Ц": "Ts", "Ч": "Ch", "Ш": "Sh", "Щ": "Shch",
    "Ъ": "", "Ы": "Y", "Ь": "", "Э": "E", "Ю": "Yu", "Я": "Ya"
}

HOMOGLYPH_MAP = {
    "А": "A", "В": "B", "Е": "E", "К": "K", "М": "M", "Н": "H", "О": "O", "Р": "P", "С": "C", "Т": "T", "У": "Y", "Х": "X",
    "а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "у": "y", "х": "x", "і": "i", "І": "I"
}


def transliterate(text):
    return "".join(CYR_TO_LAT.get(ch, ch) for ch in text)


def clean_homoglyphs(text):
    if not text:
        return ""
    return "".join(HOMOGLYPH_MAP.get(ch, ch) for ch in text)


def load_json_file(filename, fallback_url):
    if os.path.exists(filename) and os.path.getsize(filename) > 1000:
        print(f"Loading {filename} from disk ({os.path.getsize(filename) / 1024 / 1024:.2f} MB)...", flush=True)
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    print(f"Fetching JSON from {fallback_url}...", flush=True)
    req = urllib.request.Request(fallback_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        content = resp.read().decode("utf-8")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        return json.loads(content)


def load_cache():
    if CACHE_FILE.exists() and CACHE_FILE.stat().st_size > 2:
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def fetch_translation_single(text):
    if not text or not re.search(r"[\u0400-\u04FF]", text):
        return text, text
    for attempt in range(3):
        try:
            url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=ru&tl=en&dt=t"
            data = urllib.parse.urlencode({"q": text}).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                res = "".join([chunk[0] for chunk in res_data[0] if chunk and chunk[0]])
                if res:
                    return text, res.strip()
        except Exception:
            if attempt < 2:
                time.sleep(0.5)
    return text, transliterate(text)


def batch_preload_translations(texts, cache, max_workers=20):
    to_fetch = [t for t in set(texts) if t and t not in cache and re.search(r"[\u0400-\u04FF]", t)]
    if not to_fetch:
        return
    print(f"Pre-translating {len(to_fetch)} unique texts with {max_workers} threads...", flush=True)
    start = time.time()
    done = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_translation_single, t): t for t in to_fetch}
        for future in concurrent.futures.as_completed(futures):
            orig_text, translated_text = future.result()
            cache[orig_text] = translated_text
            done += 1
            if done % 50 == 0 or done == len(to_fetch):
                print(f"  Progress: {done}/{len(to_fetch)} translated ({time.time() - start:.1f}s)", flush=True)
                save_cache(cache)
    save_cache(cache)
    print(f"Pre-translation completed in {time.time() - start:.2f}s!", flush=True)


def clean_title(t):
    if not t:
        return ""
    return re.sub(r"\s*\[.*?\]", "", t).strip()


def normalize_title(t):
    if not t:
        return ""
    t = clean_title(t)
    t = re.sub(r"[^\w\s]", " ", t, flags=re.UNICODE).lower()
    return re.sub(r"\s+", " ", t).strip()


def entry_score(entry):
    s = 0
    if entry.get("isDemo"):
        s -= 10
    if isinstance(entry.get("screenshots"), list) and entry.get("screenshots"):
        s += 2
    if str(entry.get("description", "")).strip():
        s += 1
    return s


def translate_year(val, cache):
    if not val:
        return ""
    t = str(val)
    for ru, en in MONTHS_RU_TO_EN.items():
        t = re.sub(r"\b" + re.escape(ru) + r"\b", en, t, flags=re.IGNORECASE)
    t = re.sub(r"\bверсия для Nintendo Switch\b", "Nintendo Switch version", t, flags=re.IGNORECASE)
    t = re.sub(r"\bверсия для Switch\b", "Switch version", t, flags=re.IGNORECASE)
    t = re.sub(r"\bверсия для\b", "version for", t, flags=re.IGNORECASE)
    t = re.sub(r"\bдля\b", "for", t, flags=re.IGNORECASE)
    t = re.sub(r"\bна\b", "on", t, flags=re.IGNORECASE)
    t = re.sub(r"\bоригинал\b", "original", t, flags=re.IGNORECASE)
    t = re.sub(r"\bоригинальная игра\b", "original game", t, flags=re.IGNORECASE)
    t = re.sub(r"\bрелиз\b", "release", t, flags=re.IGNORECASE)
    t = re.sub(r"\bпорт\b", "port", t, flags=re.IGNORECASE)
    t = re.sub(r"\bгода?\b", "", t, flags=re.IGNORECASE)
    if re.search(r"[\u0400-\u04FF]", t):
        t = cache.get(t, transliterate(t))
    return clean_homoglyphs(t.strip())


def translate_genre(val, cache):
    if not val:
        return ""
    t = str(val)
    for ru, en in sorted(GENRE_MAP.items(), key=lambda x: len(x[0]), reverse=True):
        t = re.sub(r"\b" + re.escape(ru) + r"\b", en, t, flags=re.IGNORECASE)
    t = re.sub(r"Action[еeь]", "Action", t)
    t = re.sub(r"\bAventure\b", "Adventure", t)
    t = re.sub(r"Ш-Ш", "Shmup / Shooter", t)
    if re.search(r"[\u0400-\u04FF]", t):
        t = cache.get(t, transliterate(t))
    return clean_homoglyphs(t)


def translate_image_format(val, cache):
    if not val:
        return ""
    t = str(val)
    t = re.sub(r"\bсжато\b", "compressed", t, flags=re.IGNORECASE)
    t = re.sub(r"\bустановленный объём\b", "installed size", t, flags=re.IGNORECASE)
    t = re.sub(r"\bустановленный размер\b", "installed size", t, flags=re.IGNORECASE)
    t = re.sub(r"\bстановленный\b", "installed", t, flags=re.IGNORECASE)
    t = re.sub(r"\bустановленная\b", "installed", t, flags=re.IGNORECASE)
    t = re.sub(r"\bразмер\b", "size", t, flags=re.IGNORECASE)
    t = re.sub(r"\bобъём\b", "size", t, flags=re.IGNORECASE)
    t = re.sub(r"\bрепак\b", "repack", t, flags=re.IGNORECASE)
    t = re.sub(r"\bкастомный\b", "custom", t, flags=re.IGNORECASE)
    t = re.sub(r"\bкастомного\b", "custom", t, flags=re.IGNORECASE)
    t = re.sub(r"\bкастомное\b", "custom", t, flags=re.IGNORECASE)
    t = re.sub(r"\bсохранение\b", "save", t, flags=re.IGNORECASE)
    t = re.sub(r"\bдля разблокировки\b", "to unlock", t, flags=re.IGNORECASE)
    t = re.sub(r"\bразблокировки\b", "unlocking", t, flags=re.IGNORECASE)
    t = re.sub(r"\bкэш песен\b", "song cache", t, flags=re.IGNORECASE)
    t = re.sub(r"\bкэш\b", "cache", t, flags=re.IGNORECASE)
    t = re.sub(r"\bпесен\b", "songs", t, flags=re.IGNORECASE)
    t = re.sub(r"\bоффлайн\b", "offline", t, flags=re.IGNORECASE)
    t = re.sub(r"\bонлайн\b", "online", t, flags=re.IGNORECASE)
    t = re.sub(r"\bбайпасс\b", "bypass", t, flags=re.IGNORECASE)
    t = re.sub(r"\bинтернет-серверов\b", "internet servers", t, flags=re.IGNORECASE)
    t = re.sub(r"\bсо сжатыми видеороликами\b", "with compressed videos", t, flags=re.IGNORECASE)
    t = re.sub(r"\bсжатыми\b", "compressed", t, flags=re.IGNORECASE)
    t = re.sub(r"\bвидеороликами\b", "videos", t, flags=re.IGNORECASE)
    t = re.sub(r"\bвидео\b", "video", t, flags=re.IGNORECASE)
    t = re.sub(r"\bфото\b", "photo", t, flags=re.IGNORECASE)
    t = re.sub(r"\bмод-пак\b", "mod pack", t, flags=re.IGNORECASE)
    t = re.sub(r"\bмода?\b", "mod", t, flags=re.IGNORECASE)
    t = re.sub(r"\bмоды\b", "mods", t, flags=re.IGNORECASE)
    t = re.sub(r"\bрусификатора?\b", "Russian translation", t, flags=re.IGNORECASE)
    t = re.sub(r"\bрусской озвучкой\b", "Russian voiceover", t, flags=re.IGNORECASE)
    t = re.sub(r"\bоригинальной озвучкой\b", "original voiceover", t, flags=re.IGNORECASE)
    t = re.sub(r"\bозвучкой\b", "voiceover", t, flags=re.IGNORECASE)
    t = re.sub(r"\bбез цензуры\b", "uncensored", t, flags=re.IGNORECASE)
    t = re.sub(r"\bанцензор\b", "uncensor", t, flags=re.IGNORECASE)
    t = re.sub(r"\bсо всеми\b", "with all", t, flags=re.IGNORECASE)
    t = re.sub(r"\bс модом\b", "with mod", t, flags=re.IGNORECASE)
    t = re.sub(r"\bвместе с\b", "together with", t, flags=re.IGNORECASE)
    t = re.sub(r"\bвместе\b", "together", t, flags=re.IGNORECASE)
    t = re.sub(r"\bобновление\b", "update", t, flags=re.IGNORECASE)
    t = re.sub(r"\bобязательно для запуска\b", "REQUIRED to launch", t, flags=re.IGNORECASE)
    t = re.sub(r"\bобязательно\b", "REQUIRED", t, flags=re.IGNORECASE)
    t = re.sub(r"\bдля запуска\b", "to launch", t, flags=re.IGNORECASE)
    t = re.sub(r"\bурезанный\b", "trimmed", t, flags=re.IGNORECASE)
    t = re.sub(r"\bопциональный\b", "optional", t, flags=re.IGNORECASE)
    t = re.sub(r"\bбез\b", "without", t, flags=re.IGNORECASE)
    t = re.sub(r"\bлюбой\b", "Any", t, flags=re.IGNORECASE)
    t = re.sub(r"\bориг\.\b", "orig.", t, flags=re.IGNORECASE)
    t = re.sub(r"\bГБ\b", "GB", t)
    t = re.sub(r"\bМБ\b", "MB", t)
    t = re.sub(r"\bКБ\b", "KB", t)
    t = re.sub(r"\bГб\b", "GB", t)
    t = re.sub(r"(\d+)ГБ", r"\1 GB", t)
    t = re.sub(r"(\d+)МБ", r"\1 MB", t)
    t = re.sub(r"(\d+)КБ", r"\1 KB", t)
    t = re.sub(r"\bбайт\b", "bytes", t, flags=re.IGNORECASE)
    t = re.sub(r"\bдемонстрационная версия\b", "demo version", t, flags=re.IGNORECASE)
    t = re.sub(r"\bот\b", "by", t, flags=re.IGNORECASE)
    t = re.sub(r"\bверсия\b", "version", t, flags=re.IGNORECASE)
    t = re.sub(r"\bверсии\b", "version", t, flags=re.IGNORECASE)
    t = re.sub(r"\bвключая\b", "including", t, flags=re.IGNORECASE)
    t = re.sub(r"\bвсе\b", "all", t, flags=re.IGNORECASE)
    t = re.sub(r"\bпатч\b", "patch", t, flags=re.IGNORECASE)
    t = re.sub(r"\bплюс\b", "+", t, flags=re.IGNORECASE)
    if re.search(r"[\u0400-\u04FF]", t):
        t = cache.get(t, transliterate(t))
    return clean_homoglyphs(t)


def translate_interface_lang(val, cache):
    if not val:
        return ""
    t = str(val).strip()
    if t.lower() == "без слов":
        return "No text"

    t = re.sub(r"\bбез слов\b", "No text", t, flags=re.IGNORECASE)
    t = re.sub(r"\bмашинный перевод от\b", "machine translation by", t, flags=re.IGNORECASE)
    t = re.sub(r"\bмашинный перевод\b", "machine translation", t, flags=re.IGNORECASE)
    t = re.sub(r"\bопциональный машинный перевод от\b", "optional machine translation by", t, flags=re.IGNORECASE)
    t = re.sub(r"\bрусский любительский от\b", "Russian fan translation by", t, flags=re.IGNORECASE)
    t = re.sub(r"\bлюбительский перевод от\b", "fan translation by", t, flags=re.IGNORECASE)
    t = re.sub(r"\bлюбительский\b", "fan", t, flags=re.IGNORECASE)
    t = re.sub(r"\bрусификатор от\b", "Russian patch by", t, flags=re.IGNORECASE)
    t = re.sub(r"\bрусификатор\b", "Russian translation", t, flags=re.IGNORECASE)
    t = re.sub(r"\bперевод от\b", "translation by", t, flags=re.IGNORECASE)
    t = re.sub(r"\bперевод\b", "translation", t, flags=re.IGNORECASE)
    t = re.sub(r"\bтекст от\b", "text by", t, flags=re.IGNORECASE)
    t = re.sub(r"\bтекст\b", "text", t, flags=re.IGNORECASE)
    t = re.sub(r"\bозвучка от\b", "voiceover by", t, flags=re.IGNORECASE)
    t = re.sub(r"\bозвучка\b", "voiceover", t, flags=re.IGNORECASE)
    t = re.sub(r"\bпорт от\b", "port by", t, flags=re.IGNORECASE)
    t = re.sub(r"\bпорт\b", "port", t, flags=re.IGNORECASE)
    t = re.sub(r"\bшрифты от\b", "fonts by", t, flags=re.IGNORECASE)
    t = re.sub(r"\bшрифты\b", "fonts", t, flags=re.IGNORECASE)
    t = re.sub(r"\bмодификация от\b", "mod by", t, flags=re.IGNORECASE)
    t = re.sub(r"\bмод от\b", "mod by", t, flags=re.IGNORECASE)
    t = re.sub(r"\bмод\b", "mod", t, flags=re.IGNORECASE)
    t = re.sub(r"\bвключая\b", "including", t, flags=re.IGNORECASE)
    t = re.sub(r"\bдля\b", "for", t, flags=re.IGNORECASE)
    t = re.sub(r"\bверсия\b", "version", t, flags=re.IGNORECASE)
    t = re.sub(r"\bверсии\b", "version", t, flags=re.IGNORECASE)
    t = re.sub(r"\bисправления от\b", "fixes by", t, flags=re.IGNORECASE)
    t = re.sub(r"\bадаптация от\b", "adaptation by", t, flags=re.IGNORECASE)
    t = re.sub(r"\bадаптация\b", "adaptation", t, flags=re.IGNORECASE)
    t = re.sub(r"\bправки\b", "fixes", t, flags=re.IGNORECASE)
    t = re.sub(r"\bплюс\b", "+", t, flags=re.IGNORECASE)

    for ru, en in sorted(LANG_MAP.items(), key=lambda x: len(x[0]), reverse=True):
        t = re.sub(r"\b" + re.escape(ru) + r"\b", en, t, flags=re.IGNORECASE)

    if re.search(r"[\u0400-\u04FF]", t):
        t = cache.get(t, transliterate(t))

    return clean_homoglyphs(t)


def translate_voice_lang(val, cache):
    if not val:
        return ""
    t = str(val).strip()
    if re.match(r"^(не озвучивается|без озвучивания|без озвучания|нет озвучки)$", t, re.I):
        return "No voiceover"
    if re.match(r"^(нет|отсутствует)$", t, re.I):
        return "None"

    t = re.sub(r"\b(не озвучивается|без озвучивания|без озвучания|нет озвучки)\b", "No voiceover", t, flags=re.I)
    t = re.sub(r"\b(отсутствует|нет)\b", "None", t, flags=re.I)
    t = re.sub(r"\bвыдуманный язык\b", "Fictional language", t, flags=re.I)
    t = re.sub(r"\bили\b", "or", t, flags=re.I)
    t = re.sub(r"\bи\b", "and", t, flags=re.I)
    t = re.sub(r"\bна выбор\b", "optional", t, flags=re.I)
    t = re.sub(r"\bозвучка от\b", "voiceover by", t, flags=re.I)
    t = re.sub(r"\bтолько\b", "only", t, flags=re.I)
    t = re.sub(r"\bв некоторых сценах\b", "in some scenes", t, flags=re.I)

    for ru, en in sorted(LANG_MAP.items(), key=lambda x: len(x[0]), reverse=True):
        t = re.sub(r"\b" + re.escape(ru) + r"\b", en, t, flags=re.IGNORECASE)

    if re.search(r"[\u0400-\u04FF]", t):
        t = cache.get(t, transliterate(t))

    return clean_homoglyphs(t)


def translate_performance(val, cache):
    if not val:
        return ""
    t = str(val).strip()
    if t.lower() == "не проверено":
        return "Not tested"
    if t.lower() == "да":
        return "Yes"
    if t.lower() == "нет":
        return "No"

    t = re.sub(r"^Да\b", "Yes", t)
    t = re.sub(r"^Нет\b", "No", t)
    t = re.sub(r"\b(на|версия|версии)\b", "on", t, flags=re.I)
    t = re.sub(r"\bНе проверено\b", "Not tested", t, flags=re.I)
    t = re.sub(r"\bРаботает\b", "Works", t, flags=re.I)
    t = re.sub(r"\bбез проблем\b", "without problems", t, flags=re.I)
    t = re.sub(r"\bс модом\b", "with mod", t, flags=re.I)
    t = re.sub(r"\bс патчем\b", "with patch", t, flags=re.I)
    t = re.sub(r"\bпроверено на\b", "tested on", t, flags=re.I)

    if re.search(r"[\u0400-\u04FF]", t):
        t = cache.get(t, transliterate(t))

    return clean_homoglyphs(t)


def translate_multiplayer(val, cache):
    if not val:
        return ""
    t = str(val).strip()
    if re.match(r"^(нет|отсутствует)$", t, re.I):
        return "No"
    if re.match(r"^(да|есть)$", t, re.I):
        return "Yes"

    t = re.sub(r"\b(нет|отсутствует)\b", "No", t, flags=re.I)
    t = re.sub(r"\b(да|есть)\b", "Yes", t, flags=re.I)
    t = re.sub(r"\b(до|До)\s*(\d+)(?:-?х)?\s*(игроков|игрока|человек|человека)\b", r"Up to \2 players", t, flags=re.I)
    t = re.sub(r"\bот\s*(\d+)\s*до\s*(\d+)\s*(?:-?х)?\s*(игроков|игрока|человек|человека)\b", r"\1 to \2 players", t, flags=re.I)
    t = re.sub(r"\bдля\s*(\d+)(?:-?х)?\s*(игроков|игрока|человек|человека)\b", r"For \1 players", t, flags=re.I)
    t = re.sub(r"\bтолько\s+для\s+(\d+)(?:-?х)?\s*(игроков|игрока|человек|человека)\b", r"\1 players only", t, flags=re.I)
    t = re.sub(r"\b(\d+)\s*(?:-?х)?\s*(игроков|игрока|человек|человека)\b", r"\1 players", t, flags=re.I)
    t = re.sub(r"\b(\d+)х\b", r"\1 players", t, flags=re.I)
    t = re.sub(r"\bодновременно\b", "simultaneously", t, flags=re.I)
    t = re.sub(r"\bлокально\b", "locally", t, flags=re.I)
    t = re.sub(r"\bонлайн\b", "online", t, flags=re.I)
    t = re.sub(r"\bпо\s+сети\b", "online", t, flags=re.I)
    t = re.sub(r"\bигрок[а-я]*\b", "player", t, flags=re.I)
    t = re.sub(r"\bчеловек[а-я]*\b", "players", t, flags=re.I)
    t = re.sub(r"\bв\s+режиме\b", "in mode", t, flags=re.I)
    t = re.sub(r"\b(кооператив|кооп)\b", "co-op", t, flags=re.I)
    t = re.sub(r"\bнесколько\s+игроков\b", "multiplayer", t, flags=re.I)
    t = re.sub(r"\bтолько\b", "only", t, flags=re.I)
    t = re.sub(r"\bили\b", "or", t, flags=re.I)

    if re.search(r"[\u0400-\u04FF]", t):
        t = cache.get(t, transliterate(t))

    return clean_homoglyphs(t)


def translate_title(val, titledb_entry, cache):
    if not val:
        return ""
    t = str(val)

    # 1. Handle dual names "Russian Title / English Title [TAGS]"
    dual_match = re.match(r"^([\u0400-\u04FF\s\d\W]+?)\s*/\s*([A-Za-z0-9].*)$", t)
    if dual_match:
        ru_part = dual_match.group(1).strip()
        en_part = dual_match.group(2).strip()
        if re.search(r"[\u0400-\u04FF]", ru_part) and not re.search(r"[\u0400-\u04FF]", en_part):
            t = en_part

    # 2. Handle dual names "English Title / Russian Title [TAGS]"
    dual_match2 = re.match(r"^([A-Za-z0-9][^/]+?)\s*/\s*([\u0400-\u04FF\s\d\W]+?)(\s*\[.*\])?$", t)
    if dual_match2:
        en_part = dual_match2.group(1).strip()
        ru_part = dual_match2.group(2).strip()
        tags = dual_match2.group(3) or ""
        if not re.search(r"[\u0400-\u04FF]", en_part) and re.search(r"[\u0400-\u04FF]", ru_part):
            t = en_part + tags

    # 3. Strip Russian translations inside parentheses like: English Title (Русское название) [TAGS]
    paren_ru = re.findall(r"\(([\u0400-\u04FF\s\d\W]+?)\)", t)
    for p in paren_ru:
        if re.match(r"^(демонстрационная версия|хоумбрю|порт|порты|нативный порт.*|тамагочи|\d+\s+игр.*)$", p.strip(), re.I):
            continue
        if re.search(r"[\u0400-\u04FF]", p):
            t = t.replace(f"({p})", "").strip()

    # 4. Standardize release / edition tags in Russian
    t = re.sub(r"\(демонстрационная версия\)", "(demo version)", t, flags=re.I)
    t = re.sub(r"\(хоумбрю\)", "(homebrew)", t, flags=re.I)
    t = re.sub(r"\(хоумбрю-порт\)", "(homebrew port)", t, flags=re.I)
    t = re.sub(r"\(тамагочи\)", "(tamagotchi)", t, flags=re.I)
    t = re.sub(r"\(нативный порт\s*", "(native port ", t, flags=re.I)
    t = re.sub(r"\(порт\s*", "(port ", t, flags=re.I)
    t = re.sub(r"\(порты\)", "(ports)", t, flags=re.I)
    t = re.sub(r"\bэмулятор\b", "emulator", t, flags=re.I)
    t = re.sub(r"\bигра\b", "game", t, flags=re.I)
    t = re.sub(r"\((\d+)\s+игр\)", r"(\1 games)", t, flags=re.I)
    t = re.sub(r"(\d+)\s+игр\b", r"\1 games", t, flags=re.I)
    t = re.sub(r"\+\s*доп\.\s*контент", "+ add. content", t, flags=re.I)
    t = re.sub(r"\+\s*доп\.\s*HD-текстуры", "+ add. HD textures", t, flags=re.I)
    t = re.sub(r"\(официальные игры NSO\)", "(official NSO games)", t, flags=re.I)
    t = re.sub(r"\(официальные игры N64 NSO\)", "(official N64 NSO games)", t, flags=re.I)
    t = re.sub(r"\(официальные игры\s*\+\s*LFS-моды\)", "(official games + LFS mods)", t, flags=re.I)
    t = re.sub(r"\(официальные игры NSO\s*\+\s*опциональный мод\)", "(official NSO games + optional mod)", t, flags=re.I)
    t = re.sub(r"\(патченная 18\+\)", "(patched 18+)", t, flags=re.I)
    t = re.sub(r"\(мод без видео и фото\)", "(mod without video and photo)", t, flags=re.I)
    t = re.sub(r"\bволна\s+(\d+)\b", r"wave \1", t, flags=re.I)
    t = re.sub(r"\bэкспедиции\b", "expeditions", t, flags=re.I)
    t = re.sub(r"\bэкспедиций\b", "expeditions", t, flags=re.I)
    t = re.sub(r"\(онлайн с\s+", "(online with ", t, flags=re.I)
    t = re.sub(r"\bвкл\.\b", "incl.", t, flags=re.I)

    t = re.sub(r"\s+", " ", t).strip()

    if re.search(r"[\u0400-\u04FF]", t):
        if titledb_entry and titledb_entry.get("name"):
            tags = re.findall(r"\[.*?\]", t)
            tags_str = "".join(tags)
            t = titledb_entry["name"] + (" " + tags_str if tags_str else "")
        else:
            t = cache.get(t, transliterate(t))

    return clean_homoglyphs(t)


def translate_entity(val, titledb_entry, field_name, cache):
    if not val or val.lower() == "unknown":
        return "Unknown"
    t = str(val).strip()
    if t.lower() == "не издано":
        return "Unpublished"
    if titledb_entry and titledb_entry.get(field_name):
        return titledb_entry[field_name]
    if re.search(r"[\u0400-\u04FF]", t):
        if t in cache:
            return cache[t]
        return transliterate(t)
    return clean_homoglyphs(t)


def main():
    print("=== Building Nintendo Switch EN Catalog ===", flush=True)

    # 1. Load source files
    if os.path.exists(RU_CATALOG_FILE):
        print(f"Loading {RU_CATALOG_FILE}...", flush=True)
        with open(RU_CATALOG_FILE, "r", encoding="utf-8") as f:
            ru_catalog = json.load(f)
    else:
        print(f"{RU_CATALOG_FILE} not found! Building from switch_games.json...", flush=True)
        ru_catalog = load_json_file(SWITCH_GAMES_FILE, SWITCH_GAMES_URL)

    titledb_us = load_json_file(TITLEDB_US_FILE, TITLEDB_US_URL)
    titledb_gb = load_json_file(TITLEDB_GB_FILE, TITLEDB_GB_URL)
    cache = load_cache()
    print(f"Loaded {len(cache)} cached translations.", flush=True)

    # 2. Index English TitleDB entries
    en_by_tid = {}
    en_by_name = {}
    for db in [titledb_gb, titledb_us]:
        entries = list(db.values()) if isinstance(db, dict) else list(db)
        for v in entries:
            if not isinstance(v, dict):
                continue
            tid = str(v.get("id") or "").strip().upper()
            if tid:
                if tid not in en_by_tid or entry_score(v) >= entry_score(en_by_tid[tid]):
                    en_by_tid[tid] = v
            name = normalize_title(v.get("name"))
            if name and not v.get("isDemo"):
                if name not in en_by_name or entry_score(v) >= entry_score(en_by_name[name]):
                    en_by_name[name] = v

    print(f"Indexed {len(en_by_tid)} EN TitleDB entries by ID, {len(en_by_name)} by name.", flush=True)

    # 3. Collect only the truly remaining strings that require online translation
    texts_to_translate = set()
    for item in ru_catalog:
        raw_tid = str(item.get("title_id", "")).strip().upper()
        en_entry = en_by_tid.get(raw_tid)
        if not en_entry:
            name = normalize_title(item.get("title", ""))
            en_entry = en_by_name.get(name)
        en_entry = en_entry or {}

        # Unmatched descriptions
        if not (en_entry and str(en_entry.get("description", "")).strip()):
            raw_desc = item.get("description", "")
            if re.search(r"[\u0400-\u04FF]", raw_desc):
                texts_to_translate.add(raw_desc)

        # Rare remaining Cyrillic in other fields after rule-based pass
        t = translate_title(item.get("title", ""), en_entry, {})
        if re.search(r"[\u0400-\u04FF]", t):
            texts_to_translate.add(t)

        y = translate_year(item.get("year", ""), {})
        if re.search(r"[\u0400-\u04FF]", y):
            texts_to_translate.add(y)

        g = translate_genre(item.get("genre", ""), {})
        if re.search(r"[\u0400-\u04FF]", g):
            texts_to_translate.add(g)

        img = translate_image_format(item.get("image_format", ""), {})
        if re.search(r"[\u0400-\u04FF]", img):
            texts_to_translate.add(img)

        il = translate_interface_lang(item.get("interface_lang", ""), {})
        if re.search(r"[\u0400-\u04FF]", il):
            texts_to_translate.add(il)

        vl = translate_voice_lang(item.get("voice_lang", ""), {})
        if re.search(r"[\u0400-\u04FF]", vl):
            texts_to_translate.add(vl)

        pf = translate_performance(item.get("performance", ""), {})
        if re.search(r"[\u0400-\u04FF]", pf):
            texts_to_translate.add(pf)

        mp = translate_multiplayer(item.get("multiplayer", ""), {})
        if re.search(r"[\u0400-\u04FF]", mp):
            texts_to_translate.add(mp)

    untranslated = [t for t in texts_to_translate if t not in cache]
    if untranslated:
        print(f"Found {len(untranslated)} uncached strings requiring online translation.", flush=True)
        batch_preload_translations(untranslated, cache, max_workers=20)
    else:
        print("All required strings are already present in translation cache!", flush=True)

    # 4. Build EN Catalog
    en_catalog = []
    titledb_desc_count = 0
    translated_desc_count = 0
    titledb_ss_count = 0

    print(f"Assembling {len(ru_catalog)} EN catalog entries...", flush=True)
    start_time = time.time()

    for idx, item in enumerate(ru_catalog):
        raw_tid = str(item.get("title_id", "")).strip().upper()
        en_entry = en_by_tid.get(raw_tid)
        if not en_entry:
            name = normalize_title(item.get("title", ""))
            en_entry = en_by_name.get(name)
        en_entry = en_entry or {}

        # Screenshots
        en_screenshots = en_entry.get("screenshots")
        if en_screenshots and isinstance(en_screenshots, list) and len(en_screenshots) > 0:
            screenshots = en_screenshots
            titledb_ss_count += 1
        else:
            screenshots = item.get("screenshots", [])
            if not isinstance(screenshots, list):
                screenshots = []

        # Description
        en_desc = en_entry.get("description")
        if en_desc and isinstance(en_desc, str) and en_desc.strip():
            description = en_desc.strip()
            titledb_desc_count += 1
        else:
            raw_desc = item.get("description", "")
            if re.search(r"[\u0400-\u04FF]", raw_desc):
                description = cache.get(raw_desc, transliterate(raw_desc))
                translated_desc_count += 1
            else:
                description = raw_desc

        # Fields translation
        title = translate_title(item.get("title", ""), en_entry, cache)
        year = translate_year(item.get("year", ""), cache)
        genre = translate_genre(item.get("genre", ""), cache)
        developer = translate_entity(item.get("developer", ""), en_entry, "developer", cache)
        publisher = translate_entity(item.get("publisher", ""), en_entry, "publisher", cache)
        image_format = translate_image_format(item.get("image_format", ""), cache)
        interface_lang = translate_interface_lang(item.get("interface_lang", ""), cache)
        voice_lang = translate_voice_lang(item.get("voice_lang", ""), cache)
        performance = translate_performance(item.get("performance", ""), cache)
        multiplayer = translate_multiplayer(item.get("multiplayer", ""), cache)

        en_catalog.append({
            "title": title,
            "size": item.get("size", ""),
            "magnet": item.get("magnet", ""),
            "topic_id": item.get("topic_id", ""),
            "url": item.get("url", ""),
            "year": year,
            "genre": genre,
            "developer": developer,
            "publisher": publisher,
            "image_format": image_format,
            "interface_lang": interface_lang,
            "voice_lang": voice_lang,
            "performance": performance,
            "multiplayer": multiplayer,
            "cover": item.get("cover", ""),
            "screenshots": screenshots,
            "description": description,
            "title_id": item.get("title_id", ""),
        })

    elapsed = time.time() - start_time
    print(f"\nAssembly Complete in {elapsed:.2f}s!", flush=True)
    print(f"Total entries in EN catalog: {len(en_catalog)}", flush=True)
    print(f"Descriptions from TitleDB (US/GB): {titledb_desc_count} / {len(en_catalog)}", flush=True)
    print(f"Descriptions translated / cached: {translated_desc_count} / {len(en_catalog)}", flush=True)
    print(f"Screenshots from TitleDB: {titledb_ss_count} / {len(en_catalog)}", flush=True)

    # Write EN_catalog.json
    output_path = Path("EN_catalog.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(en_catalog, f, ensure_ascii=False, indent=4)

    print(f"Successfully saved EN catalog to {output_path.resolve()}", flush=True)


if __name__ == "__main__":
    main()
