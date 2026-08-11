# Nintendo Switch Game Collections

Коллекции и подборки лучших игр для **Nintendo Switch** с указанием их уникального **Title ID** и актуальным рейтингом **Metacritic**.

Все подборки сформированы на основе официальной классификации категорий Nintendo eShop (TitleDB) и отсортированы по оценкам Metacritic. Каждый элемент гарантированно сопоставлен с единым реестром раздач [`switch_games.json`](https://raw.githubusercontent.com/Langegen/switch-games/refs/heads/main/switch_games.json).

---

## 📁 Подборки по жанрам

Каждая подборка содержит **ровно 100 проверенных игр** (за исключением ежедневно автообновляемого файла свежих релизов):

| Файл | Жанр / Описание | Всего игр |
| :--- | :--- | :---: |
| 🏆 [`top_100.json`](./top_100.json) | Абсолютный Топ-100 лучших игр всех времён по версии Metacritic | 100 |
| ⚔️ [`action_adventure.json`](./action_adventure.json) | Приключенческие экшены (Action & Adventure) | 100 |
| 🕹️ [`arcade.json`](./arcade.json) | Классические и современные аркады (Arcade) | 100 |
| 👻 [`horror.json`](./horror.json) | Сурвайвал и психологические хорроры (Survival Horror) | 100 |
| 🗝️ [`metroidvania.json`](./metroidvania.json) | Метроидвании (Metroidvania) | 100 |
| 🥳 [`party_multiplayer.json`](./party_multiplayer.json) | Игры для вечеринок и локальный кооператив (Party / Co-Op) | 100 |
| 🍄 [`platformers.json`](./platformers.json) | 2D и 3D Платформеры (Platformer) | 100 |
| 🧩 [`puzzles.json`](./puzzles.json) | Головоломки и логические игры (Puzzle) | 100 |
| 💀 [`roguelike_roguelite.json`](./roguelike_roguelite.json) | Рогалики, роглайты и колодостроительные игры (Roguelite) | 100 |
| ⚔️ [`rpg_jrpg.json`](./rpg_jrpg.json) | Ролевые игры и JRPG (Role-Playing Game) | 100 |
| 🎯 [`shooters.json`](./shooters.json) | Шутеры от 1-го/3-го лица и Shmup (Shooters / FPS) | 100 |
| 🏡 [`simulation_cozy.json`](./simulation_cozy.json) | Симуляторы и уютные/фермерские игры (Simulation & Cozy) | 100 |
| ♟️ [`strategy_tactics.json`](./strategy_tactics.json) | Пошаговая тактика и стратегии (Strategy & Tactics) | 100 |
| 📖 [`visual_novels.json`](./visual_novels.json) | Визуальные новеллы и сюжетные адвенчуры (Visual Novels) | 100 |
| 🆕 [`new_release.json`](./new_release.json) | Автоматически обновляемые новые релизы | ~40 |

---

## 📋 Формат данных

Все файлы подборок сохранены в стандартном формате JSON (массив объектов, 1 объект на строку, кодировка UTF-8):

```json
[
  {
    "title": "The Legend of Zelda: Tears of the Kingdom",
    "title_id": "0100F2C0115B6000",
    "metacritic": 96.0
  },
  {
    "title": "Super Mario Odyssey",
    "title_id": "0100000000010000",
    "metacritic": 97.0
  }
]
```

### Описание полей:
- `title` (*string*) — Название игры (очищенное от лишних технически тегов релиза).
- `title_id` (*string*) — Уникальный 16-значный HEX-идентификатор приложения Nintendo Switch.
- `metacritic` (*float | null*) — Оценка игры на сайте Metacritic (0.0 — 100.0).

---

## 🤖 Ежедневное автообновление новых релизов

Проект использует **GitHub Actions** ([`.github/workflows/update_new_release.yml`](./.github/workflows/update_new_release.yml)) для автоматического обновления файла [`new_release.json`](./new_release.json):

- **Расписание**: Каждый день в **04:00 UTC**.
- **Источник**: Atom-лента свежих раздач `https://feed.rutracker.cc/atom/f/1605.atom`.
- **Логика**: Скрипт [`update_new_release.py`](./scripts/update_new_release.py) сопоставляет раздачи с базой `switch_games.json`, подтягивает оценки Metacritic и коммитит обновления.

---

## 📊 Источники данных

- **База релизов & Title ID**: [`switch_games.json`](https://raw.githubusercontent.com/Langegen/switch-games/refs/heads/main/switch_games.json)
- **Оценки Metacritic**: [`nintendolife_switch_games_with_metacritic.csv`](https://raw.githubusercontent.com/texboy/switch-games-dasboard/refs/heads/main/nintendolife_switch_games_with_metacritic.csv)
- **Категории eShop**: [`blawar/titledb`](https://github.com/blawar/titledb) (`RU.ru.json` & `US.en.json`)
