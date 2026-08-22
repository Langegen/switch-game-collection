# Nintendo Switch Game Collections & Catalogs

Коллекции, подборки и полные каталоги игр для **Nintendo Switch** с указанием их уникального **Title ID**, актуальным рейтингом **Metacritic**, описаниями, скриншотами и метаданными раздач.

Все подборки сформированы на основе официальной классификации категорий Nintendo eShop (TitleDB) и отсортированы по оценкам Metacritic. Каждый элемент гарантированно сопоставлен с единым реестром раздач [`switch_games.json`](https://raw.githubusercontent.com/Langegen/switch-games/refs/heads/main/switch_games.json).

---

## 🎮 Полные каталоги игр (RU & EN)

Полные реестры всех доступных игр для Nintendo Switch (более 7,000 игр), готовые для интеграции в сторонние приложения, боты и веб-каталоги. Оба файла имеют **100% идентичную структуру и порядок элементов**:

| Файл | Язык | Описание |
| :--- | :---: | :--- |
| 🇷🇺 [`RU_catalog.json`](./RU_catalog.json) | Русский | Полный каталог со всеми характеристиками, описаниями и скриншотами на русском языке |
| 🇬🇧 [`EN_catalog.json`](./EN_catalog.json) | English | Полная англоязычная копия каталога с официальными описаниями eShop, скриншотами и переведёнными метаданными |

### Формат данных каталогов:
```json
[
  {
    "title": "The Legend of Heroes: Trails in the Sky 2nd Chapter Remake (demo version) [NSZ][DEMO][ENG]",
    "size": "3.63 GB",
    "magnet": "magnet:?xt=urn:btih:BDE9FC9AC4884B1759956051405EDC3C02DF05DF...",
    "topic_id": "6897473",
    "url": "https://rutracker.org/forum/viewtopic.php?t=6897473",
    "year": "2026, September",
    "genre": "Role-Playing, Action",
    "developer": "Nihon Falcom",
    "publisher": "GungHo America",
    "image_format": ".NSZ (compressed ~22%, installed size 4.65 GB) [DEMO]",
    "interface_lang": "English [ENG]",
    "voice_lang": "Japanese",
    "performance": "Yes (on 22.5.0, Atmosphere 1.11.2)",
    "multiplayer": "No",
    "cover": "https://i8.imageban.ru/out/2026/08/20/21580fd359b08238c48501f5159cfefe.png",
    "screenshots": [
      "https://i128.fastpic.org/thumb/2026/0820/23/dd26f869597f963b1b8961e591a61923.jpeg"
    ],
    "description": "The plot continues immediately after the events of the first part...",
    "title_id": "0100AD6029730000"
  }
]
```

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

## 🤖 Автообновление (GitHub Actions)

1. **Обновление каталогов (`RU_catalog.json` & `EN_catalog.json`)**:
   - **Workflow**: [`.github/workflows/update_ru_catalog.yml`](./.github/workflows/update_ru_catalog.yml)
   - **Расписание**: Каждый день в **09:00 UTC**.
   - **Скрипты**: [`build_ru_catalog.py`](./scripts/build_ru_catalog.py) и [`build_en_catalog.py`](./scripts/build_en_catalog.py). Оба каталога синхронно обновляются и сопоставляются 1:1.

2. **Обновление новых релизов (`new_release.json`)**:
   - **Workflow**: [`.github/workflows/update_new_release.yml`](./.github/workflows/update_new_release.yml)
   - **Расписание**: Каждый день в **04:00 UTC**.
   - **Скрипт**: [`update_new_release.py`](./scripts/update_new_release.py).

---

## 📊 Источники данных

- **База релизов & Title ID**: [`switch_games.json`](https://raw.githubusercontent.com/Langegen/switch-games/refs/heads/main/switch_games.json)
- **Оценки Metacritic**: [`nintendolife_switch_games_with_metacritic.csv`](https://raw.githubusercontent.com/texboy/switch-games-dasboard/refs/heads/main/nintendolife_switch_games_with_metacritic.csv)
- **Категории eShop & Описания**: [`blawar/titledb`](https://github.com/blawar/titledb) (`RU.ru.json`, `US.en.json`, `GB.en.json`)
