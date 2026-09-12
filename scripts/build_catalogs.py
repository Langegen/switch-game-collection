#!/usr/bin/env python3
import argparse
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

BASE_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = Path(__file__).resolve().parent

RU_CATALOG_FILE = str(BASE_DIR / "RU_catalog.json")
SWITCH_GAMES_FILE = str(BASE_DIR / "switch_games.json")
SWITCH_GAMES_URL = "https://raw.githubusercontent.com/Langegen/switch-games/main/switch_games.json"

LANG_CONFIGS = {
    "en": {
        "output_file": "EN_catalog.json",
        "cache_file": "translations_cache.json",
        "target_lang": "en",
        "titledb_files": ["US.en.json", "GB.en.json"],
        "demo_tag": "(demo version)",
        "homebrew_tag": "(homebrew)",
        "port_tag": "(port",
        "ports_tag": "(ports)",
        "native_port_tag": "(native port ",
        "emulator_word": "emulator",
        "game_word": "game",
        "games_word": "games",
        "months": {
            "января": "January", "январь": "January", "февраля": "February", "февраль": "February",
            "марта": "March", "март": "March", "апреля": "April", "апрель": "April",
            "мая": "May", "май": "May", "июня": "June", "июнь": "June",
            "июля": "July", "июль": "July", "августа": "August", "август": "August",
            "сентября": "September", "сентябрь": "September", "октября": "October", "октябрь": "October",
            "ноября": "November", "ноябрь": "November", "декабря": "December", "декабрь": "December",
            "фeвapль": "February", "aпepль": "April", "фepвaль": "February", "oктбяpь": "October",
        },
        "perf_yes": "Yes",
        "perf_no": "No",
        "perf_not_tested": "Not tested",
        "perf_on": "on",
        "mp_no": "No",
        "mp_yes": "Yes",
        "mp_up_to": "Up to {N} players",
        "mp_exact": "{N} players",
        "voice_none": "No voiceover",
        "voice_empty": "None",
        "text_no_text": "No text",
        "format_compressed": "compressed",
        "format_installed_size": "installed size",
        "format_repack": "repack",
        "format_demo": "demo version",
        "notes": {
            "машинный перевод": "machine translation",
            "опциональный машинный перевод": "optional machine translation",
            "любительский перевод": "fan translation",
            "русификатор": "Russian translation",
            "перевод": "translation",
            "текст": "text",
            "озвучка": "voiceover",
            "порт": "port",
            "шрифты": "fonts",
            "модификация": "mod",
            "мод": "mod",
            "исправления": "fixes",
            "адаптация": "adaptation",
            "правки": "fixes",
            "от": "by",
            "для": "for",
            "версия": "version",
            "включая": "including",
            "без цензуры": "uncensored",
            "плюс": "+",
        },
        "languages": {
            "русский": "Russian", "русская": "Russian", "рус": "Russian",
            "английский": "English", "английская": "English", "англ": "English",
            "японский": "Japanese", "японская": "Japanese", "яп": "Japanese",
            "китайский": "Chinese", "китайская": "Chinese",
            "традиционный китайский": "Traditional Chinese", "упрощенный китайский": "Simplified Chinese",
            "корейский": "Korean", "корейская": "Korean",
            "французский": "French", "французская": "French",
            "немецкий": "German", "немецкая": "German",
            "испанский": "Spanish", "испанская": "Spanish",
            "итальянский": "Italian", "итальянская": "Italian",
            "португальский": "Portuguese", "португальская": "Portuguese",
            "бразильский португальский": "Brazilian Portuguese",
            "польский": "Polish", "польская": "Polish",
            "нидерландский": "Dutch", "голландский": "Dutch",
            "шведский": "Swedish", "норвежский": "Norwegian", "датский": "Danish", "финский": "Finnish",
            "турецкий": "Turkish", "арабский": "Arabic", "тайский": "Thai",
            "чешский": "Czech", "венгерский": "Hungarian", "греческий": "Greek",
            "иврит": "Hebrew", "украинский": "Ukrainian", "выдуманный язык": "Fictional language",
        },
        "genres": {
            "экшн": "Action", "экшен": "Action", "ролевая игра": "Role-Playing", "ролевая": "Role-Playing",
            "приключения": "Adventure", "приключение": "Adventure", "пазл": "Puzzle", "поиск предметов": "Hidden Object",
            "платформер": "Platformer", "шутер от первого лица": "First-Person Shooter", "шутер": "Shooter",
            "вечеринка": "Party", "настольная игра": "Board Game", "настольная": "Board Game",
            "казуальные игры": "Casual", "казуальные": "Casual", "стратегии": "Strategy", "стратегия": "Strategy",
            "пошаговая стратегия": "Turn-Based Strategy", "карточная пошаговая": "Turn-Based Card Game",
            "карточная": "Card Game", "пошаговая": "Turn-Based", "симулятор": "Simulation", "гонки": "Racing",
            "метроидвания": "Metroidvania", "аркада": "Arcade", "хоррор": "Horror", "музыка": "Music",
            "спорт": "Sports", "файтинг": "Fighting", "визуальная новелла": "Visual Novel", "песочница": "Sandbox",
            "выживание": "Survival", "головоломка": "Puzzle", "отдельный режим": "separate mode",
            "ритм-игра": "Rhythm Game", "ш-ш": "Shmup / Shooter",
        }
    },
    "es": {
        "output_file": "ES_catalog.json",
        "cache_file": "translations_cache_es.json",
        "target_lang": "es",
        "titledb_files": ["ES.es.json", "MX.es.json"],
        "demo_tag": "(versión demo)",
        "homebrew_tag": "(homebrew)",
        "port_tag": "(port",
        "ports_tag": "(ports)",
        "native_port_tag": "(port nativo ",
        "emulator_word": "emulador",
        "game_word": "juego",
        "games_word": "juegos",
        "months": {
            "января": "enero", "январь": "enero", "февраля": "febrero", "февраль": "febrero",
            "марта": "marzo", "март": "marzo", "апреля": "abril", "апрель": "abril",
            "мая": "mayo", "май": "mayo", "июня": "junio", "июнь": "junio",
            "июля": "julio", "июль": "julio", "августа": "agosto", "август": "agosto",
            "сентября": "septiembre", "сентябрь": "septiembre", "октября": "octubre", "октябрь": "octubre",
            "ноября": "noviembre", "ноябрь": "noviembre", "декабря": "diciembre", "декабрь": "diciembre",
            "фeвapль": "febrero", "aпepль": "abril", "фepвaль": "febrero", "oктбяpь": "octubre",
        },
        "perf_yes": "Sí",
        "perf_no": "No",
        "perf_not_tested": "No probado",
        "perf_on": "en",
        "mp_no": "No",
        "mp_yes": "Sí",
        "mp_up_to": "Hasta {N} jugadores",
        "mp_exact": "{N} jugadores",
        "voice_none": "Sin voces",
        "voice_empty": "Ninguno",
        "text_no_text": "Sin texto",
        "format_compressed": "comprimido",
        "format_installed_size": "tamaño instalado",
        "format_repack": "repack",
        "format_demo": "versión demo",
        "notes": {
            "машинный перевод": "traducción automática",
            "опциональный машинный перевод": "traducción automática opcional",
            "любительский перевод": "traducción fan",
            "русификатор": "traducción al ruso",
            "перевод": "traducción",
            "текст": "texto",
            "озвучка": "voces",
            "порт": "port",
            "шрифты": "fuentes",
            "модификация": "mod",
            "мод": "mod",
            "исправления": "correcciones",
            "адаптация": "adaptación",
            "правки": "arreglos",
            "от": "de",
            "для": "para",
            "версия": "versión",
            "включая": "incluyendo",
            "без цензуры": "sin censura",
            "плюс": "+",
        },
        "languages": {
            "русский": "Ruso", "русская": "Ruso", "рус": "Ruso",
            "английский": "Inglés", "английская": "Inglés", "англ": "Inglés",
            "японский": "Japonés", "японская": "Japonés", "яп": "Japonés",
            "китайский": "Chino", "китайская": "Chino",
            "традиционный китайский": "Chino tradicional", "упрощенный китайский": "Chino simplificado",
            "корейский": "Coreano", "корейская": "Coreano",
            "французский": "Francés", "французская": "Francés",
            "немецкий": "Alemán", "немецкая": "Alemán",
            "испанский": "Español", "испанская": "Español",
            "итальянский": "Italiano", "итальянская": "Italiano",
            "португальский": "Portugués", "португальская": "Portugués",
            "бразильский португальский": "Portugués brasileño",
            "польский": "Polaco", "польская": "Polaco",
            "нидерландский": "Holandés", "голландский": "Holandés",
            "шведский": "Sueco", "норвежский": "Noruego", "датский": "Danés", "финский": "Finlandés",
            "турецкий": "Turco", "арабский": "Árabe", "тайский": "Tailandés",
            "чешский": "Checo", "венгерский": "Húngaro", "греческий": "Griego",
            "иврит": "Hebreo", "украинский": "Ucraniano", "выдуманный язык": "Idioma ficticio",
        },
        "genres": {
            "экшн": "Acción", "экшен": "Acción", "ролевая игра": "Rol (RPG)", "ролевая": "Rol (RPG)",
            "приключения": "Aventura", "приключение": "Aventura", "пазл": "Puzle", "поиск предметов": "Objetos ocultos",
            "платформер": "Plataformas", "шутер от первого лица": "Shooter en primera persona", "шутер": "Shooter / Disparos",
            "вечеринка": "Party / Fiesta", "настольная игра": "Juego de mesa", "настольная": "Juego de mesa",
            "казуальные игры": "Casual", "казуальные": "Casual", "стратегии": "Estrategia", "стратегия": "Estrategia",
            "пошаговая стратегия": "Estrategia por turnos", "карточная пошаговая": "Juego de cartas por turnos",
            "карточная": "Cartas", "пошаговая": "Por turnos", "симулятор": "Simulación", "гонки": "Carreras",
            "метроидвания": "Metroidvania", "аркада": "Arcade", "хоррор": "Terror", "музыка": "Música",
            "спорт": "Deportes", "файтинг": "Lucha", "визуальная новелла": "Novela visual", "песочница": "Sandbox",
            "выживание": "Supervivencia", "головоломка": "Puzle", "отдельный режим": "modo separado",
            "ритм-игра": "Juego de ritmo", "ш-ш": "Shmup / Disparos",
        }
    },
    "fr": {
        "output_file": "FR_catalog.json",
        "cache_file": "translations_cache_fr.json",
        "target_lang": "fr",
        "titledb_files": ["FR.fr.json", "CA.fr.json"],
        "demo_tag": "(version démo)",
        "homebrew_tag": "(homebrew)",
        "port_tag": "(portage",
        "ports_tag": "(portages)",
        "native_port_tag": "(portage natif ",
        "emulator_word": "émulateur",
        "game_word": "jeu",
        "games_word": "jeux",
        "months": {
            "января": "janvier", "январь": "janvier", "февраля": "février", "февраль": "février",
            "марта": "mars", "март": "mars", "апреля": "avril", "апрель": "avril",
            "мая": "mai", "май": "mai", "июня": "juin", "июнь": "juin",
            "июля": "juillet", "июль": "juillet", "августа": "août", "август": "août",
            "сентября": "septembre", "сентябрь": "septembre", "октября": "octobre", "октябрь": "octobre",
            "ноября": "novembre", "ноябрь": "novembre", "декабря": "décembre", "декабрь": "décembre",
            "фeвapль": "février", "aпepль": "avril", "фepвaль": "février", "oктбяpь": "octobre",
        },
        "perf_yes": "Oui",
        "perf_no": "Non",
        "perf_not_tested": "Non testé",
        "perf_on": "sur",
        "mp_no": "Non",
        "mp_yes": "Oui",
        "mp_up_to": "Jusqu'à {N} joueurs",
        "mp_exact": "{N} joueurs",
        "voice_none": "Sans voix",
        "voice_empty": "Aucun",
        "text_no_text": "Sans texte",
        "format_compressed": "compressé",
        "format_installed_size": "taille installée",
        "format_repack": "repack",
        "format_demo": "version démo",
        "notes": {
            "машинный перевод": "traduction automatique",
            "опциональный машинный перевод": "traduction automatique optionnelle",
            "любительский перевод": "traduction fan",
            "русификатор": "traduction russe",
            "перевод": "traduction",
            "текст": "texte",
            "озвучка": "doublage",
            "порт": "portage",
            "шрифты": "polices",
            "модификация": "mod",
            "мод": "mod",
            "исправления": "corrections",
            "адаптация": "adaptation",
            "правки": "correctifs",
            "от": "par",
            "для": "pour",
            "версия": "version",
            "включая": "incluant",
            "без цензуры": "non censuré",
            "плюс": "+",
        },
        "languages": {
            "русский": "Russe", "русская": "Russe", "рус": "Russe",
            "английский": "Anglais", "английская": "Anglais", "англ": "Anglais",
            "японский": "Japonais", "японская": "Japonais", "яп": "Japonais",
            "китайский": "Chinois", "китайская": "Chinois",
            "традиционный китайский": "Chinois traditionnel", "упрощенный китайский": "Chinois simplifié",
            "корейский": "Coréen", "корейская": "Coréen",
            "французский": "Français", "французская": "Français",
            "немецкий": "Allemand", "немецкая": "Allemand",
            "испанский": "Espagnol", "испанская": "Espagnol",
            "итальянский": "Italien", "итальянская": "Italien",
            "португальский": "Portugais", "португальская": "Portugais",
            "бразильский португальский": "Portugais brésilien",
            "польский": "Polonais", "польская": "Polonais",
            "нидерландский": "Néerlandais", "голландский": "Néerlandais",
            "шведский": "Suédois", "норвежский": "Norvégien", "датский": "Danois", "финский": "Finnois",
            "турецкий": "Turc", "арабский": "Arabe", "тайский": "Thaï",
            "чешский": "Tchèque", "венгерский": "Hongrois", "греческий": "Grec",
            "иврит": "Hébreu", "украинский": "Ukrainien", "выдуманный язык": "Langue fictive",
        },
        "genres": {
            "экшн": "Action", "экшен": "Action", "ролевая игра": "Jeu de rôle (RPG)", "ролевая": "Jeu de rôle (RPG)",
            "приключения": "Aventure", "приключение": "Aventure", "пазл": "Puzzle", "поиск предметов": "Objets cachés",
            "платформер": "Plates-formes", "шутер от первого лица": "FPS / Tir subjectif", "шутер": "Jeu de tir",
            "вечеринка": "Party game", "настольная игра": "Jeu de plateau", "настольная": "Jeu de plateau",
            "казуальные игры": "Casual", "казуальные": "Casual", "стратегии": "Stratégie", "стратегия": "Stratégie",
            "пошаговая стратегия": "Stratégie au tour par tour", "карточная пошаговая": "Jeu de cartes tour par tour",
            "карточная": "Cartes", "пошаговая": "Tour par tour", "симулятор": "Simulation", "гонки": "Course",
            "метроидвания": "Metroidvania", "аркада": "Arcade", "хоррор": "Horreur", "музыка": "Musique",
            "спорт": "Sport", "файтинг": "Combat", "визуальная новелла": "Visual Novel", "песочница": "Sandbox / Bac à sable",
            "выживание": "Survie", "головоломка": "Casse-tête", "отдельный режим": "mode séparé",
            "ритм-игра": "Jeu de rythme", "ш-ш": "Shmup / Tir",
        }
    },
    "de": {
        "output_file": "DE_catalog.json",
        "cache_file": "translations_cache_de.json",
        "target_lang": "de",
        "titledb_files": ["DE.de.json", "AT.de.json"],
        "demo_tag": "(Demo-Version)",
        "homebrew_tag": "(Homebrew)",
        "port_tag": "(Port",
        "ports_tag": "(Ports)",
        "native_port_tag": "(Nativer Port ",
        "emulator_word": "Emulator",
        "game_word": "Spiel",
        "games_word": "Spiele",
        "months": {
            "января": "Januar", "январь": "Januar", "февраля": "Februar", "февраль": "Februar",
            "марта": "März", "март": "März", "апреля": "April", "апрель": "April",
            "мая": "Mai", "май": "Mai", "июня": "Juni", "июнь": "Juni",
            "июля": "Juli", "июль": "Juli", "августа": "August", "август": "August",
            "сентября": "September", "сентябрь": "September", "октября": "Oktober", "октябрь": "Oktober",
            "ноября": "November", "ноябрь": "November", "декабря": "Dezember", "декабрь": "Dezember",
            "фeвapль": "Februar", "aпepль": "April", "фepвaль": "Februar", "oктбяpь": "Oktober",
        },
        "perf_yes": "Ja",
        "perf_no": "Nein",
        "perf_not_tested": "Nicht getestet",
        "perf_on": "auf",
        "mp_no": "Nein",
        "mp_yes": "Ja",
        "mp_up_to": "Bis zu {N} Spieler",
        "mp_exact": "{N} Spieler",
        "voice_none": "Keine Sprachausgabe",
        "voice_empty": "Keine",
        "text_no_text": "Kein Text",
        "format_compressed": "komprimiert",
        "format_installed_size": "installierte Größe",
        "format_repack": "Repack",
        "format_demo": "Demo-Version",
        "notes": {
            "машинный перевод": "maschinelle Übersetzung",
            "опциональный машинный перевод": "optionale maschinelle Übersetzung",
            "любительский перевод": "Fan-Übersetzung",
            "русификатор": "russische Übersetzung",
            "перевод": "Übersetzung",
            "текст": "Text",
            "озвучка": "Sprachausgabe",
            "порт": "Port",
            "шрифты": "Schriftarten",
            "модификация": "Mod",
            "мод": "Mod",
            "исправления": "Korrekturen",
            "адаптация": "Anpassung",
            "правки": "Fixes",
            "от": "von",
            "для": "für",
            "версия": "Version",
            "включая": "inklusive",
            "без цензуры": "ungeschnitten",
            "плюс": "+",
        },
        "languages": {
            "русский": "Russisch", "русская": "Russisch", "рус": "Russisch",
            "английский": "Englisch", "английская": "Englisch", "англ": "Englisch",
            "японский": "Japanisch", "японская": "Japanisch", "яп": "Japanisch",
            "китайский": "Chinesisch", "китайская": "Chinesisch",
            "традиционный китайский": "Traditionelles Chinesisch", "упрощенный китайский": "Vereinfachtes Chinesisch",
            "корейский": "Koreanisch", "корейская": "Koreanisch",
            "французский": "Französisch", "французская": "Französisch",
            "немецкий": "Deutsch", "немецкая": "Deutsch",
            "испанский": "Spanisch", "испанская": "Spanisch",
            "итальянский": "Italienisch", "итальянская": "Italienisch",
            "португальский": "Portugiesisch", "португальская": "Portugiesisch",
            "бразильский португальский": "Brasilianisches Portugiesisch",
            "польский": "Polnisch", "польская": "Polnisch",
            "нидерландский": "Niederländisch", "голландский": "Niederländisch",
            "шведский": "Schwedisch", "норвежский": "Norwegisch", "датский": "Dänisch", "финский": "Finnisch",
            "турецкий": "Türkisch", "арабский": "Arabisch", "тайский": "Thailändisch",
            "чешский": "Tschechisch", "венгерский": "Ungarisch", "греческий": "Griechisch",
            "иврит": "Hebräisch", "украинский": "Ukrainisch", "выдуманный язык": "Fiktive Sprache",
        },
        "genres": {
            "экшн": "Action", "экшен": "Action", "ролевая игра": "Rollenspiel (RPG)", "ролевая": "Rollenspiel (RPG)",
            "приключения": "Abenteuer", "приключение": "Abenteuer", "пазл": "Puzzle", "поиск предметов": "Wimmelbild",
            "платформер": "Plattformer", "шутер от первого лица": "Ego-Shooter", "шутер": "Shooter",
            "вечеринка": "Party-Spiel", "настольная игра": "Brettspiel", "настольная": "Brettspiel",
            "казуальные игры": "Gelegenheitsspiel", "казуальные": "Casual", "стратегии": "Strategie", "стратегия": "Strategie",
            "пошаговая стратегия": "Rundenbasierte Strategie", "карточная пошаговая": "Rundenbasiertes Kartenspiel",
            "карточная": "Kartenspiel", "пошаговая": "Rundenbasiert", "симулятор": "Simulation", "гонки": "Rennspiel",
            "метроидвания": "Metroidvania", "аркада": "Arcade", "хоррор": "Horror", "музыка": "Musik",
            "спорт": "Sport", "файтинг": "Kampfspiel", "визуальная новелла": "Visual Novel", "песочница": "Sandbox",
            "выживание": "Überleben / Survival", "головоломка": "Denkspiel", "отдельный режим": "separater Modus",
            "ритм-игра": "Rhythmusspiel", "ш-ш": "Shmup / Shooter",
        }
    },
    "it": {
        "output_file": "IT_catalog.json",
        "cache_file": "translations_cache_it.json",
        "target_lang": "it",
        "titledb_files": ["IT.it.json"],
        "demo_tag": "(versione demo)",
        "homebrew_tag": "(homebrew)",
        "port_tag": "(port",
        "ports_tag": "(port)",
        "native_port_tag": "(port nativo ",
        "emulator_word": "emulatore",
        "game_word": "gioco",
        "games_word": "giochi",
        "months": {
            "января": "gennaio", "январь": "gennaio", "февраля": "febbraio", "февраль": "febbraio",
            "марта": "marzo", "март": "marzo", "апреля": "aprile", "апрель": "aprile",
            "мая": "maggio", "май": "maggio", "июня": "giugno", "июнь": "giugno",
            "июля": "luglio", "июль": "luglio", "августа": "agosto", "август": "agosto",
            "сентября": "settembre", "сентябрь": "settembre", "октября": "ottobre", "октябрь": "ottobre",
            "ноября": "novembre", "ноябрь": "novembre", "декабря": "dicembre", "декабрь": "dicembre",
            "фeвapль": "febbraio", "aпepль": "aprile", "фepвaль": "febbraio", "oктбяpь": "ottobre",
        },
        "perf_yes": "Sì",
        "perf_no": "No",
        "perf_not_tested": "Non testato",
        "perf_on": "su",
        "mp_no": "No",
        "mp_yes": "Sì",
        "mp_up_to": "Fino a {N} giocatori",
        "mp_exact": "{N} giocatori",
        "voice_none": "Senza doppiaggio",
        "voice_empty": "Nessuno",
        "text_no_text": "Senza testo",
        "format_compressed": "compresso",
        "format_installed_size": "dimensione installata",
        "format_repack": "repack",
        "format_demo": "versione demo",
        "notes": {
            "машинный перевод": "traduzione automatica",
            "опциональный машинный перевод": "traduzione automatica opzionale",
            "любительский перевод": "traduzione amatoriale",
            "русификатор": "traduzione in russo",
            "перевод": "traduzione",
            "текст": "testo",
            "озвучка": "doppiaggio",
            "порт": "port",
            "шрифты": "font",
            "модификация": "mod",
            "мод": "mod",
            "исправления": "correzioni",
            "адаптация": "adattamento",
            "правки": "modifiche",
            "от": "di",
            "для": "per",
            "версия": "versione",
            "включая": "compreso",
            "без цензуры": "senza censura",
            "плюс": "+",
        },
        "languages": {
            "русский": "Russo", "русская": "Russo", "рус": "Russo",
            "английский": "Inglese", "английская": "Inglese", "англ": "Inglese",
            "японский": "Giapponese", "японская": "Giapponese", "яп": "Giapponese",
            "китайский": "Cinese", "китайская": "Cinese",
            "традиционный китайский": "Cinese tradizionale", "упрощенный китайский": "Cinese semplificato",
            "корейский": "Coreano", "корейская": "Coreano",
            "французский": "Francese", "французская": "Francese",
            "немецкий": "Tedesco", "немецкая": "Tedesco",
            "испанский": "Spagnolo", "испанская": "Spagnolo",
            "итальянский": "Italiano", "итальянская": "Italiano",
            "португальский": "Portoghese", "португальская": "Portoghese",
            "бразильский португальский": "Portoghese brasiliano",
            "польский": "Polacco", "польская": "Polacco",
            "нидерландский": "Olandese", "голландский": "Olandese",
            "шведский": "Svedese", "норвежский": "Norvegese", "датский": "Danese", "финский": "Finlandese",
            "турецкий": "Turco", "арабский": "Arabo", "тайский": "Tailandese",
            "чешский": "Ceco", "венгерский": "Ungherese", "греческий": "Greco",
            "иврит": "Ebraico", "украинский": "Ucraino", "выдуманный язык": "Lingua fittizia",
        },
        "genres": {
            "экшн": "Azione", "экшен": "Azione", "ролевая игра": "Gioco di ruolo (RPG)", "ролевая": "Gioco di ruolo (RPG)",
            "приключения": "Avventura", "приключение": "Avventura", "пазл": "Rompicapo", "поиск предметов": "Oggetti nascosti",
            "платформер": "Platform", "шутер от первого лица": "Sparatutto in prima persona", "шутер": "Sparatutto",
            "вечеринка": "Party game", "настольная игра": "Gioco da tavolo", "настольная": "Gioco da tavolo",
            "казуальные игры": "Casual", "казуальные": "Casual", "стратегии": "Strategia", "стратегия": "Strategia",
            "пошаговая стратегия": "Strategia a turni", "карточная пошаговая": "Gioco di carte a turni",
            "карточная": "Carte", "пошаговая": "A turni", "симулятор": "Simulazione", "гонки": "Corse",
            "метроидвания": "Metroidvania", "аркада": "Arcade", "хоррор": "Horror", "музыка": "Musica",
            "спорт": "Sport", "файтинг": "Picchiaduro", "визуальная новелла": "Visual Novel", "песочница": "Sandbox",
            "выживание": "Sopravvivenza", "головоломка": "Enigma", "отдельный режим": "modalità separata",
            "ритм-игра": "Gioco ritmico", "ш-ш": "Shmup / Sparatutto",
        }
    },
    "pt-br": {
        "output_file": "PT_BR_catalog.json",
        "cache_file": "translations_cache_pt_br.json",
        "target_lang": "pt",
        "titledb_files": ["BR.pt.json", "PT.pt.json"],
        "demo_tag": "(versão demo)",
        "homebrew_tag": "(homebrew)",
        "port_tag": "(port",
        "ports_tag": "(ports)",
        "native_port_tag": "(port nativo ",
        "emulator_word": "emulador",
        "game_word": "jogo",
        "games_word": "jogos",
        "months": {
            "января": "janeiro", "январь": "janeiro", "февраля": "fevereiro", "февраль": "fevereiro",
            "марта": "março", "март": "março", "апреля": "abril", "апрель": "abril",
            "мая": "maio", "май": "maio", "июня": "junho", "июнь": "junho",
            "июля": "julho", "июль": "julho", "августа": "agosto", "август": "agosto",
            "сентября": "setembro", "сентябрь": "setembro", "октября": "outubro", "октябрь": "outubro",
            "ноября": "novembro", "ноябрь": "novembro", "декабря": "dezembro", "декабрь": "dezembro",
            "фeвapль": "fevereiro", "aпepль": "abril", "фepвaль": "fevereiro", "oктбяpь": "outubro",
        },
        "perf_yes": "Sim",
        "perf_no": "Não",
        "perf_not_tested": "Não testado",
        "perf_on": "no",
        "mp_no": "Não",
        "mp_yes": "Sim",
        "mp_up_to": "Até {N} jogadores",
        "mp_exact": "{N} jogadores",
        "voice_none": "Sem dublagem",
        "voice_empty": "Nenhum",
        "text_no_text": "Sem texto",
        "format_compressed": "compactado",
        "format_installed_size": "tamanho instalado",
        "format_repack": "repack",
        "format_demo": "versão demo",
        "notes": {
            "машинный перевод": "tradução automática",
            "опциональный машинный перевод": "tradução automática opcional",
            "любительский перевод": "tradução de fãs",
            "русификатор": "tradução para russo",
            "перевод": "tradução",
            "текст": "texto",
            "озвучка": "dublagem",
            "порт": "port",
            "шрифты": "fontes",
            "модификация": "mod",
            "мод": "mod",
            "исправления": "correções",
            "адаптация": "adaptação",
            "правки": "ajustes",
            "от": "por",
            "для": "para",
            "версия": "versão",
            "включая": "incluindo",
            "без цензуры": "sem censura",
            "плюс": "+",
        },
        "languages": {
            "русский": "Russo", "русская": "Russo", "рус": "Russo",
            "английский": "Inglês", "английская": "Inglês", "англ": "Inglês",
            "японский": "Japonês", "японская": "Japonês", "яп": "Japonês",
            "китайский": "Chinês", "китайская": "Chinês",
            "традиционный китайский": "Chinês tradicional", "упрощенный китайский": "Chinês simplificado",
            "корейский": "Coreano", "корейская": "Coreano",
            "французский": "Francês", "французская": "Francês",
            "немецкий": "Alemão", "немецкая": "Alemão",
            "испанский": "Espanhol", "испанская": "Espanhol",
            "итальянский": "Italiano", "итальянская": "Italiano",
            "португальский": "Português", "португальская": "Português",
            "бразильский португальский": "Português do Brasil",
            "польский": "Polonês", "польская": "Polonês",
            "нидерландский": "Holandês", "голландский": "Holandês",
            "шведский": "Sueco", "норвежский": "Norueguês", "датский": "Dinamarquês", "финский": "Finlandês",
            "турецкий": "Turco", "арабский": "Árabe", "тайский": "Tailandês",
            "чешский": "Tcheco", "венгерский": "Húngaro", "греческий": "Grego",
            "иврит": "Hebraico", "украинский": "Ucraniano", "выдуманный язык": "Língua fictícia",
        },
        "genres": {
            "экшн": "Ação", "экшен": "Ação", "ролевая игра": "RPG", "ролевая": "RPG",
            "приключения": "Aventura", "приключение": "Aventura", "пазл": "Quebra-cabeça", "поиск предметов": "Objetos ocultos",
            "платформер": "Plataforma", "шутер от первого лица": "FPS / Tiro em primeira pessoa", "шутер": "Tiro / Shooter",
            "вечеринка": "Festa / Party", "настольная игра": "Jogo de tabuleiro", "настольная": "Jogo de tabuleiro",
            "казуальные игры": "Casual", "казуальные": "Casual", "стратегии": "Estratégia", "стратегия": "Estratégia",
            "пошаговая стратегия": "Estratégia por turnos", "карточная пошаговая": "Jogo de cartas por turnos",
            "карточная": "Cartas", "пошаговая": "Por turnos", "симулятор": "Simulação", "гонки": "Corrida",
            "метроидвания": "Metroidvania", "аркада": "Arcade", "хоррор": "Terror", "музыка": "Música",
            "спорт": "Esportes", "файтинг": "Luta", "визуальная новелла": "Visual Novel", "песочница": "Sandbox",
            "выживание": "Sobrevivência", "головоломка": "Enigma", "отдельный режим": "modo separado",
            "ритм-игра": "Jogo de ritmo", "ш-ш": "Shmup / Tiro",
        }
    },
    "zh-hans": {
        "output_file": "ZH_Hans_catalog.json",
        "cache_file": "translations_cache_zh_hans.json",
        "target_lang": "zh-CN",
        "titledb_files": ["CN.zh.json", "HK.zh.json"],
        "demo_tag": "(试玩版)",
        "homebrew_tag": "(自制程序)",
        "port_tag": "(移植版",
        "ports_tag": "(移植合集)",
        "native_port_tag": "(原生移植版 ",
        "emulator_word": "模拟器",
        "game_word": "游戏",
        "games_word": "款游戏",
        "months": {
            "января": "1月", "январь": "1月", "февраля": "2月", "февраль": "2月",
            "марта": "3月", "март": "3月", "апреля": "4月", "апрель": "4月",
            "мая": "5月", "май": "5月", "июня": "6月", "июнь": "6月",
            "июля": "7月", "июль": "7月", "августа": "8月", "август": "8月",
            "сентября": "9月", "сентябрь": "9月", "октября": "10月", "октябрь": "10月",
            "ноября": "11月", "ноябрь": "11月", "декабря": "12月", "декабрь": "12月",
            "фeвapль": "2月", "aпepль": "4月", "фepвaль": "2月", "oктбяpь": "10月",
        },
        "perf_yes": "是",
        "perf_no": "否",
        "perf_not_tested": "未测试",
        "perf_on": "在",
        "mp_no": "无",
        "mp_yes": "支持",
        "mp_up_to": "最多 {N} 人",
        "mp_exact": "{N} 人",
        "voice_none": "无语音",
        "voice_empty": "无",
        "text_no_text": "无文本",
        "format_compressed": "已压缩",
        "format_installed_size": "安装大小",
        "format_repack": "整合版",
        "format_demo": "试玩版",
        "notes": {
            "машинный перевод": "机器翻译",
            "опциональный машинный перевод": "可选机翻",
            "любительский перевод": "民间汉化",
            "русификатор": "俄化补丁",
            "перевод": "翻译",
            "текст": "文本",
            "озвучка": "语音",
            "порт": "移植版",
            "шрифты": "字体",
            "модификация": "MOD",
            "мод": "MOD",
            "исправления": "修复",
            "адаптация": "适配",
            "правки": "修正",
            "от": "来自",
            "для": "用于",
            "версия": "版本",
            "включая": "包含",
            "без цензуры": "去码无修",
            "плюс": "+",
        },
        "languages": {
            "русский": "俄语", "русская": "俄语", "рус": "俄语",
            "английский": "英语", "английская": "英语", "англ": "英语",
            "японский": "日语", "японская": "日语", "яп": "日语",
            "китайский": "中文", "китайская": "中文",
            "традиционный китайский": "繁体中文", "упрощенный китайский": "简体中文",
            "корейский": "韩语", "корейская": "韩语",
            "французский": "法语", "французская": "法语",
            "немецкий": "德语", "немецкая": "德语",
            "испанский": "西班牙语", "испанская": "西班牙语",
            "итальянский": "意大利语", "итальянская": "意大利语",
            "португальский": "葡萄牙语", "португальская": "葡萄牙语",
            "бразильский португальский": "巴西葡萄牙语",
            "польский": "波兰语", "польская": "波兰语",
            "нидерландский": "荷兰语", "голландский": "荷兰语",
            "шведский": "瑞典语", "норвежский": "挪威语", "датский": "丹麦语", "финский": "芬兰语",
            "турецкий": "土耳其语", "арабский": "阿拉伯语", "тайский": "泰语",
            "чешский": "捷克语", "венгерский": "匈牙利语", "греческий": "希腊语",
            "иврит": "希伯来语", "украинский": "乌克兰语", "выдуманный язык": "虚构语言",
        },
        "genres": {
            "экшн": "动作", "экшен": "动作", "ролевая игра": "角色扮演 (RPG)", "ролевая": "角色扮演 (RPG)",
            "приключения": "冒险", "приключение": "冒险", "пазл": "解谜", "поиск предметов": "寻物解谜",
            "платформер": "平台跳跃", "шутер от первого лица": "第一人称射击 (FPS)", "шутер": "射击",
            "вечеринка": "派对聚会", "настольная игра": "桌面棋牌", "настольная": "桌面棋牌",
            "казуальные игры": "休闲", "казуальные": "休闲", "стратегии": "策略", "стратегия": "策略",
            "пошаговая стратегия": "回合制策略", "карточная пошаговая": "回合制卡牌",
            "карточная": "卡牌", "пошаговая": "回合制", "симулятор": "模拟经营", "гонки": "竞速赛车",
            "метроидвания": "类银河恶魔城", "аркада": "街机", "хоррор": "恐怖惊悚", "музыка": "音乐节奏",
            "спорт": "体育竞技", "файтинг": "格斗对战", "визуальная новелла": "视觉小说", "песочница": "沙盒建造",
            "выживание": "生存探索", "головоломка": "益智解谜", "отдельный режим": "独立模式",
            "ритм-игра": "音游", "ш-ш": "弹幕射击",
        }
    }
}

HOMOGLYPH_MAP = {
    "А": "A", "В": "B", "Е": "E", "К": "K", "М": "M", "Н": "H", "О": "O", "Р": "P", "С": "C", "Т": "T", "У": "Y", "Х": "X",
    "а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "у": "y", "х": "x", "і": "i", "І": "I"
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


def transliterate(text):
    return "".join(CYR_TO_LAT.get(ch, ch) for ch in text)


def clean_homoglyphs(text):
    if not text:
        return ""
    return "".join(HOMOGLYPH_MAP.get(ch, ch) for ch in text)


def load_json_file(filename, fallback_url):
    local_path = BASE_DIR / filename
    if local_path.exists() and local_path.stat().st_size > 1000:
        print(f"Loading {filename} from disk ({local_path.stat().st_size / 1024 / 1024:.2f} MB)...", flush=True)
        with open(local_path, "r", encoding="utf-8") as f:
            return json.load(f)
    print(f"Fetching JSON from {fallback_url}...", flush=True)
    req = urllib.request.Request(fallback_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        content = resp.read().decode("utf-8")
        with open(local_path, "w", encoding="utf-8") as f:
            f.write(content)
        return json.loads(content)


def load_cache(cache_file):
    path = SCRIPTS_DIR / cache_file
    if path.exists() and path.stat().st_size > 2:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_cache(cache, cache_file):
    path = SCRIPTS_DIR / cache_file
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def fetch_translation_single(text, target_lang):
    if not text:
        return text, text
    for attempt in range(3):
        try:
            url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target_lang}&dt=t"
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


def batch_preload_translations(texts, cache, cache_file, target_lang, max_workers=20):
    to_fetch = [t for t in set(texts) if t and t not in cache and (re.search(r"[\u0400-\u04FF]", t) or target_lang in ["zh-CN", "ja", "ko"])]
    if not to_fetch:
        return
    print(f"Pre-translating {len(to_fetch)} unique texts into '{target_lang}' with {max_workers} threads...", flush=True)
    start = time.time()
    done = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_translation_single, t, target_lang): t for t in to_fetch}
        for future in concurrent.futures.as_completed(futures):
            orig_text, translated_text = future.result()
            cache[orig_text] = translated_text
            done += 1
            if done % 50 == 0 or done == len(to_fetch):
                print(f"  Progress: {done}/{len(to_fetch)} translated ({time.time() - start:.1f}s)", flush=True)
                save_cache(cache, cache_file)
    save_cache(cache, cache_file)
    print(f"Pre-translation for '{target_lang}' completed in {time.time() - start:.2f}s!", flush=True)


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


def translate_year(val, cfg, cache):
    if not val:
        return ""
    t = str(val)
    for ru, loc in cfg["months"].items():
        t = re.sub(r"\b" + re.escape(ru) + r"\b", loc, t, flags=re.IGNORECASE)
    t = re.sub(r"\bверсия для Nintendo Switch\b", f"Nintendo Switch {cfg['perf_on']}", t, flags=re.IGNORECASE)
    t = re.sub(r"\bверсия для Switch\b", f"Switch {cfg['perf_on']}", t, flags=re.IGNORECASE)
    t = re.sub(r"\bверсия для\b", f"version {cfg['perf_on']}", t, flags=re.IGNORECASE)
    t = re.sub(r"\bдля\b", cfg["perf_on"], t, flags=re.IGNORECASE)
    t = re.sub(r"\bна\b", cfg["perf_on"], t, flags=re.IGNORECASE)
    t = re.sub(r"\bоригинал\b", "original", t, flags=re.IGNORECASE)
    t = re.sub(r"\bоригинальная игра\b", "original", t, flags=re.IGNORECASE)
    t = re.sub(r"\bрелиз\b", "release", t, flags=re.IGNORECASE)
    t = re.sub(r"\bпорт\b", "port", t, flags=re.IGNORECASE)
    t = re.sub(r"\bгода?\b", "", t, flags=re.IGNORECASE)
    if re.search(r"[\u0400-\u04FF]", t):
        t = cache.get(t, transliterate(t))
    return clean_homoglyphs(t.strip())


def translate_genre(val, cfg, cache):
    if not val:
        return ""
    t = str(val)
    # Translate to target language genres
    for ru, loc in sorted(cfg["genres"].items(), key=lambda x: len(x[0]), reverse=True):
        t = re.sub(r"\b" + re.escape(ru) + r"\b", loc, t, flags=re.IGNORECASE)
    t = re.sub(r"Action[еeь]", "Action", t)
    t = re.sub(r"\bAventure\b", "Adventure", t)
    t = re.sub(r"Ш-Ш", cfg["genres"].get("ш-ш", "Shmup / Shooter"), t)
    if re.search(r"[\u0400-\u04FF]", t):
        t = cache.get(t, transliterate(t))
    return clean_homoglyphs(t)


def translate_image_format(val, cfg, cache):
    if not val:
        return ""
    t = str(val)
    t = re.sub(r"\bсжато\b", cfg["format_compressed"], t, flags=re.IGNORECASE)
    t = re.sub(r"\bустановленный объём\b", cfg["format_installed_size"], t, flags=re.IGNORECASE)
    t = re.sub(r"\bустановленный размер\b", cfg["format_installed_size"], t, flags=re.IGNORECASE)
    t = re.sub(r"\bстановленный\b", "installed", t, flags=re.IGNORECASE)
    t = re.sub(r"\bустановленная\b", "installed", t, flags=re.IGNORECASE)
    t = re.sub(r"\bразмер\b", "size", t, flags=re.IGNORECASE)
    t = re.sub(r"\bобъём\b", "size", t, flags=re.IGNORECASE)
    t = re.sub(r"\bрепак\b", cfg["format_repack"], t, flags=re.IGNORECASE)
    t = re.sub(r"\bдемонстрационная версия\b", cfg["format_demo"], t, flags=re.IGNORECASE)
    t = re.sub(r"\bкастомный\b", "custom", t, flags=re.IGNORECASE)
    t = re.sub(r"\bкастомного\b", "custom", t, flags=re.IGNORECASE)
    t = re.sub(r"\bкастомное\b", "custom", t, flags=re.IGNORECASE)
    t = re.sub(r"\bсохранение\b", "save", t, flags=re.IGNORECASE)
    t = re.sub(r"\bкэш песен\b", "song cache", t, flags=re.IGNORECASE)
    t = re.sub(r"\bкэш\b", "cache", t, flags=re.IGNORECASE)
    t = re.sub(r"\bпесен\b", "songs", t, flags=re.IGNORECASE)
    t = re.sub(r"\bоффлайн\b", "offline", t, flags=re.IGNORECASE)
    t = re.sub(r"\bонлайн\b", "online", t, flags=re.IGNORECASE)
    t = re.sub(r"\bмод-пак\b", "mod pack", t, flags=re.IGNORECASE)
    t = re.sub(r"\bмода?\b", "mod", t, flags=re.IGNORECASE)
    t = re.sub(r"\bмоды\b", "mods", t, flags=re.IGNORECASE)
    t = re.sub(r"\bбез цензуры\b", cfg["notes"].get("без цензуры", "uncensored"), t, flags=re.IGNORECASE)
    t = re.sub(r"\bГБ\b", "GB", t)
    t = re.sub(r"\bМБ\b", "MB", t)
    t = re.sub(r"\bКБ\b", "KB", t)
    t = re.sub(r"\bГб\b", "GB", t)
    t = re.sub(r"(\d+)ГБ", r"\1 GB", t)
    t = re.sub(r"(\d+)МБ", r"\1 MB", t)
    t = re.sub(r"(\d+)КБ", r"\1 KB", t)
    t = re.sub(r"\bбайт\b", "bytes", t, flags=re.IGNORECASE)
    t = re.sub(r"\bплюс\b", "+", t, flags=re.IGNORECASE)
    if re.search(r"[\u0400-\u04FF]", t):
        t = cache.get(t, transliterate(t))
    return clean_homoglyphs(t)


def translate_interface_lang(val, cfg, cache):
    if not val:
        return ""
    t = str(val).strip()
    if t.lower() == "без слов":
        return cfg["text_no_text"]

    for ru_note, loc_note in sorted(cfg["notes"].items(), key=lambda x: len(x[0]), reverse=True):
        t = re.sub(r"\b" + re.escape(ru_note) + r"\b", loc_note, t, flags=re.IGNORECASE)

    for ru_lang, loc_lang in sorted(cfg["languages"].items(), key=lambda x: len(x[0]), reverse=True):
        t = re.sub(r"\b" + re.escape(ru_lang) + r"\b", loc_lang, t, flags=re.IGNORECASE)

    if re.search(r"[\u0400-\u04FF]", t):
        t = cache.get(t, transliterate(t))

    return clean_homoglyphs(t)


def translate_voice_lang(val, cfg, cache):
    if not val:
        return ""
    t = str(val).strip()
    if re.match(r"^(не озвучивается|без озвучивания|без озвучания|нет озвучки)$", t, re.I):
        return cfg["voice_none"]
    if re.match(r"^(нет|отсутствует)$", t, re.I):
        return cfg["voice_empty"]

    for ru_note, loc_note in sorted(cfg["notes"].items(), key=lambda x: len(x[0]), reverse=True):
        t = re.sub(r"\b" + re.escape(ru_note) + r"\b", loc_note, t, flags=re.IGNORECASE)

    for ru_lang, loc_lang in sorted(cfg["languages"].items(), key=lambda x: len(x[0]), reverse=True):
        t = re.sub(r"\b" + re.escape(ru_lang) + r"\b", loc_lang, t, flags=re.IGNORECASE)

    if re.search(r"[\u0400-\u04FF]", t):
        t = cache.get(t, transliterate(t))

    return clean_homoglyphs(t)


def translate_performance(val, cfg, cache):
    if not val:
        return ""
    t = str(val).strip()
    if t.lower() == "не проверено":
        return cfg["perf_not_tested"]
    if t.lower() == "да":
        return cfg["perf_yes"]
    if t.lower() == "нет":
        return cfg["perf_no"]

    t = re.sub(r"^Да\b", cfg["perf_yes"], t)
    t = re.sub(r"^Нет\b", cfg["perf_no"], t)
    t = re.sub(r"\b(на|версия|версии)\b", cfg["perf_on"], t, flags=re.I)
    t = re.sub(r"\bНе проверено\b", cfg["perf_not_tested"], t, flags=re.I)
    t = re.sub(r"\bРаботает\b", "Works", t, flags=re.I)
    if re.search(r"[\u0400-\u04FF]", t):
        t = cache.get(t, transliterate(t))
    return clean_homoglyphs(t)


def translate_multiplayer(val, cfg, cache):
    if not val:
        return ""
    t = str(val).strip()
    if re.match(r"^(нет|отсутствует)$", t, re.I):
        return cfg["mp_no"]
    if re.match(r"^(да|есть)$", t, re.I):
        return cfg["mp_yes"]

    # Match "до X игроков"
    m_up_to = re.search(r"\b(?:до|До)\s*(\d+)(?:-?х)?\s*(?:игроков|игрока|человек|человека)\b", t, re.I)
    if m_up_to:
        return cfg["mp_up_to"].format(N=m_up_to.group(1))

    m_exact = re.search(r"\b(\d+)\s*(?:-?х)?\s*(?:игроков|игрока|человек|человека)\b", t, re.I)
    if m_exact:
        return cfg["mp_exact"].format(N=m_exact.group(1))

    if t in cache:
        return cache[t]
    if re.search(r"[\u0400-\u04FF]", t):
        t = cache.get(t, transliterate(t))
    return clean_homoglyphs(t)


def translate_title(val, titledb_entry, cfg, cache):
    if not val:
        return ""
    t = str(val)

    # 1. Handle dual names "Russian Title / Foreign Title [TAGS]"
    dual_match = re.match(r"^([\u0400-\u04FF\s\d\W]+?)\s*/\s*([A-Za-z0-9\u4e00-\u9fff].*)$", t)
    if dual_match:
        ru_part = dual_match.group(1).strip()
        non_ru_part = dual_match.group(2).strip()
        if re.search(r"[\u0400-\u04FF]", ru_part) and not re.search(r"[\u0400-\u04FF]", non_ru_part):
            t = non_ru_part

    # 2. Handle dual names "Foreign Title / Russian Title [TAGS]"
    dual_match2 = re.match(r"^([A-Za-z0-9\u4e00-\u9fff][^/]+?)\s*/\s*([\u0400-\u04FF\s\d\W]+?)(\s*\[.*\])?$", t)
    if dual_match2:
        non_ru_part = dual_match2.group(1).strip()
        ru_part = dual_match2.group(2).strip()
        tags = dual_match2.group(3) or ""
        if not re.search(r"[\u0400-\u04FF]", non_ru_part) and re.search(r"[\u0400-\u04FF]", ru_part):
            t = non_ru_part + tags

    # 3. Strip Russian translations inside parentheses like: Title (Русское название) [TAGS]
    paren_ru = re.findall(r"\(([\u0400-\u04FF\s\d\W]+?)\)", t)
    for p in paren_ru:
        if re.match(r"^(демонстрационная версия|хоумбрю|порт|порты|нативный порт.*|тамагочи|\d+\s+игр.*)$", p.strip(), re.I):
            continue
        if re.search(r"[\u0400-\u04FF]", p):
            t = t.replace(f"({p})", "").strip()

    # 4. Standardize release / edition tags in localized language
    t = re.sub(r"\(демонстрационная версия\)", cfg["demo_tag"], t, flags=re.I)
    t = re.sub(r"\(хоумбрю\)", cfg["homebrew_tag"], t, flags=re.I)
    t = re.sub(r"\(хоумбрю-порт\)", f"({cfg['homebrew_tag']} {cfg['port_tag']})", t, flags=re.I)
    t = re.sub(r"\(нативный порт\s*", cfg["native_port_tag"], t, flags=re.I)
    t = re.sub(r"\(порт\s*", cfg["port_tag"] + " ", t, flags=re.I)
    t = re.sub(r"\(порты\)", cfg["ports_tag"], t, flags=re.I)
    t = re.sub(r"\bэмулятор\b", cfg["emulator_word"], t, flags=re.I)
    t = re.sub(r"\bигра\b", cfg["game_word"], t, flags=re.I)
    t = re.sub(r"\((\d+)\s+игр\)", rf"(\1 {cfg['games_word']})", t, flags=re.I)
    t = re.sub(r"(\d+)\s+игр\b", rf"\1 {cfg['games_word']}", t, flags=re.I)
    t = re.sub(r"\+\s*доп\.\s*контент", "+ DLC", t, flags=re.I)
    t = re.sub(r"\+\s*доп\.\s*HD-текстуры", "+ HD textures", t, flags=re.I)
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


def build_catalog_for_lang(lang_code):
    cfg = LANG_CONFIGS.get(lang_code.lower())
    if not cfg:
        raise ValueError(f"Unsupported language code: {lang_code}. Supported: {list(LANG_CONFIGS.keys())}")

    print(f"\n==================================================", flush=True)
    print(f"=== Building Catalog for [{lang_code.upper()}] ({cfg['output_file']}) ===", flush=True)
    print(f"==================================================", flush=True)

    # 1. Load source files
    if os.path.exists(RU_CATALOG_FILE):
        print(f"Loading {RU_CATALOG_FILE}...", flush=True)
        with open(RU_CATALOG_FILE, "r", encoding="utf-8") as f:
            ru_catalog = json.load(f)
    else:
        print(f"Fetching switch_games.json...", flush=True)
        ru_catalog = load_json_file("switch_games.json", SWITCH_GAMES_URL)

    # 2. Load TitleDB files for this language
    titledb_entries_by_tid = {}
    titledb_entries_by_name = {}

    for tdb_name in cfg["titledb_files"]:
        tdb_url = f"https://raw.githubusercontent.com/blawar/titledb/master/{tdb_name}"
        tdb_data = load_json_file(tdb_name, tdb_url)
        entries = list(tdb_data.values()) if isinstance(tdb_data, dict) else list(tdb_data)
        for v in entries:
            if not isinstance(v, dict):
                continue
            tid = str(v.get("id") or "").strip().upper()
            if tid:
                if tid not in titledb_entries_by_tid or entry_score(v) >= entry_score(titledb_entries_by_tid[tid]):
                    titledb_entries_by_tid[tid] = v
            name = normalize_title(v.get("name"))
            if name and not v.get("isDemo"):
                if name not in titledb_entries_by_name or entry_score(v) >= entry_score(titledb_entries_by_name[name]):
                    titledb_entries_by_name[name] = v

    print(f"Indexed {len(titledb_entries_by_tid)} TitleDB entries by ID, {len(titledb_entries_by_name)} by name for [{lang_code.upper()}].", flush=True)

    # 3. Load Translation Cache
    cache = load_cache(cfg["cache_file"])
    print(f"Loaded {len(cache)} cached translations from {cfg['cache_file']}.", flush=True)

    # 4. First-pass rule-based translation to collect only truly remaining uncached strings
    texts_to_translate = set()
    for item in ru_catalog:
        raw_tid = str(item.get("title_id", "")).strip().upper()
        tdb_entry = titledb_entries_by_tid.get(raw_tid)
        if not tdb_entry:
            name = normalize_title(item.get("title", ""))
            tdb_entry = titledb_entries_by_name.get(name)
        tdb_entry = tdb_entry or {}

        # Unmatched descriptions
        if not (tdb_entry and str(tdb_entry.get("description", "")).strip()):
            raw_desc = item.get("description", "")
            if re.search(r"[\u0400-\u04FF]", raw_desc) or cfg["target_lang"] in ["zh-CN", "ja", "ko"]:
                if raw_desc not in cache:
                    texts_to_translate.add(raw_desc)

        # Check other fields after rule-based pass
        t = translate_title(item.get("title", ""), tdb_entry, cfg, {})
        if re.search(r"[\u0400-\u04FF]", t) and t not in cache:
            texts_to_translate.add(t)

        y = translate_year(item.get("year", ""), cfg, {})
        if re.search(r"[\u0400-\u04FF]", y) and y not in cache:
            texts_to_translate.add(y)

        g = translate_genre(item.get("genre", ""), cfg, {})
        if re.search(r"[\u0400-\u04FF]", g) and g not in cache:
            texts_to_translate.add(g)

        img = translate_image_format(item.get("image_format", ""), cfg, {})
        if re.search(r"[\u0400-\u04FF]", img) and img not in cache:
            texts_to_translate.add(img)

        il = translate_interface_lang(item.get("interface_lang", ""), cfg, {})
        if re.search(r"[\u0400-\u04FF]", il) and il not in cache:
            texts_to_translate.add(il)

        vl = translate_voice_lang(item.get("voice_lang", ""), cfg, {})
        if re.search(r"[\u0400-\u04FF]", vl) and vl not in cache:
            texts_to_translate.add(vl)

        pf = translate_performance(item.get("performance", ""), cfg, {})
        if re.search(r"[\u0400-\u04FF]", pf) and pf not in cache:
            texts_to_translate.add(pf)

        mp = translate_multiplayer(item.get("multiplayer", ""), cfg, {})
        if re.search(r"[\u0400-\u04FF]", mp) and mp not in cache:
            texts_to_translate.add(mp)

    untranslated = [t for t in texts_to_translate if t not in cache]
    if untranslated:
        print(f"Found {len(untranslated)} uncached strings requiring online translation into [{lang_code.upper()}].", flush=True)
        batch_preload_translations(untranslated, cache, cfg["cache_file"], cfg["target_lang"], max_workers=20)
    else:
        print(f"All required strings for [{lang_code.upper()}] are already present in translation cache!", flush=True)

    # 5. Assemble Catalog
    catalog = []
    titledb_desc_count = 0
    translated_desc_count = 0
    titledb_ss_count = 0

    print(f"Assembling {len(ru_catalog)} catalog entries for [{lang_code.upper()}]...", flush=True)
    start_time = time.time()

    for idx, item in enumerate(ru_catalog):
        raw_tid = str(item.get("title_id", "")).strip().upper()
        tdb_entry = titledb_entries_by_tid.get(raw_tid)
        if not tdb_entry:
            name = normalize_title(item.get("title", ""))
            tdb_entry = titledb_entries_by_name.get(name)
        tdb_entry = tdb_entry or {}

        # Screenshots
        tdb_screenshots = tdb_entry.get("screenshots")
        if tdb_screenshots and isinstance(tdb_screenshots, list) and len(tdb_screenshots) > 0:
            screenshots = tdb_screenshots
            titledb_ss_count += 1
        else:
            screenshots = item.get("screenshots", [])
            if not isinstance(screenshots, list):
                screenshots = []

        # Description
        tdb_desc = tdb_entry.get("description")
        if tdb_desc and isinstance(tdb_desc, str) and tdb_desc.strip():
            description = clean_homoglyphs(tdb_desc.strip())
            titledb_desc_count += 1
        else:
            raw_desc = item.get("description", "")
            if raw_desc in cache:
                description = clean_homoglyphs(cache[raw_desc])
                translated_desc_count += 1
            elif re.search(r"[\u0400-\u04FF]", raw_desc):
                description = clean_homoglyphs(cache.get(raw_desc, transliterate(raw_desc)))
                translated_desc_count += 1
            else:
                description = clean_homoglyphs(raw_desc)

        # Fields translation
        title = translate_title(item.get("title", ""), tdb_entry, cfg, cache)
        year = translate_year(item.get("year", ""), cfg, cache)
        genre = translate_genre(item.get("genre", ""), cfg, cache)
        developer = translate_entity(item.get("developer", ""), tdb_entry, "developer", cache)
        publisher = translate_entity(item.get("publisher", ""), tdb_entry, "publisher", cache)
        image_format = translate_image_format(item.get("image_format", ""), cfg, cache)
        interface_lang = translate_interface_lang(item.get("interface_lang", ""), cfg, cache)
        voice_lang = translate_voice_lang(item.get("voice_lang", ""), cfg, cache)
        performance = translate_performance(item.get("performance", ""), cfg, cache)
        multiplayer = translate_multiplayer(item.get("multiplayer", ""), cfg, cache)

        catalog.append({
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
    print(f"\nAssembly for [{lang_code.upper()}] Complete in {elapsed:.2f}s!", flush=True)
    print(f"Total entries in [{lang_code.upper()}] catalog: {len(catalog)}", flush=True)
    print(f"Descriptions from TitleDB: {titledb_desc_count} / {len(catalog)}", flush=True)
    print(f"Descriptions translated / cached: {translated_desc_count} / {len(catalog)}", flush=True)
    print(f"Screenshots from TitleDB: {titledb_ss_count} / {len(catalog)}", flush=True)

    # Write output JSON
    output_path = BASE_DIR / cfg["output_file"]
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=4)

    print(f"Successfully saved [{lang_code.upper()}] catalog to {output_path.resolve()}", flush=True)


def main():
    parser = argparse.ArgumentParser(description="Build localized Nintendo Switch catalogs.")
    parser.add_argument("--lang", default="all", help="Language code to build: en, es, fr, de, it, pt-br, zh-hans, or 'all'")
    args = parser.parse_args()

    if args.lang.lower() == "all":
        languages = ["en", "es", "fr", "de", "it", "pt-br", "zh-hans"]
    else:
        languages = [args.lang.lower()]

    print(f"Starting catalog build process for languages: {languages}")
    for lang in languages:
        build_catalog_for_lang(lang)

    print("\nAll requested catalogs built successfully!")


if __name__ == "__main__":
    main()
