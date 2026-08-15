import urllib.request
import json
import csv
import io

print("Downloading switch_games.json sample...")
req = urllib.request.Request("https://raw.githubusercontent.com/Langegen/switch-games/main/switch_games.json", headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=60) as resp:
    sg = json.loads(resp.read().decode("utf-8"))

print(f"switch_games total items: {len(sg)}")
print("Sample switch_games[0] keys:", list(sg[0].keys()))

print("\nDownloading RU.ru.json sample...")
req = urllib.request.Request("https://raw.githubusercontent.com/blawar/titledb/master/RU.ru.json", headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=60) as resp:
    ru = json.loads(resp.read().decode("utf-8"))

print(f"RU.ru.json type: {type(ru)}")
if isinstance(ru, dict):
    sample_key = list(ru.keys())[0]
    print(f"Sample key in RU.ru.json: {sample_key}")
    print("Sample RU.ru.json value keys:", list(ru[sample_key].keys()) if isinstance(ru[sample_key], dict) else type(ru[sample_key]))
    print("Sample item:", json.dumps(ru[sample_key], ensure_ascii=False, indent=2)[:500])
elif isinstance(ru, list):
    print("Sample item in RU.ru.json:", json.dumps(ru[0], ensure_ascii=False, indent=2)[:500])

print("\nDownloading Metacritic CSV sample...")
req = urllib.request.Request("https://raw.githubusercontent.com/texboy/switch-games-dasboard/refs/heads/main/nintendolife_switch_games_with_metacritic.csv", headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=60) as resp:
    csv_text = resp.read().decode("utf-8")

reader = csv.DictReader(io.StringIO(csv_text))
rows = list(reader)
print(f"Metacritic CSV rows count: {len(rows)}")
print("Sample CSV row:", rows[0])
