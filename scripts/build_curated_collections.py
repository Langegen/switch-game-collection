#!/usr/bin/env python3
import json
import re
import urllib.request
from pathlib import Path

URL = "https://raw.githubusercontent.com/Langegen/switch-games/refs/heads/main/switch_games.json"

print(f"Fetching latest switch_games.json from {URL}...")
req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=60) as resp:
    switch_games = json.loads(resp.read().decode("utf-8"))

def clean_title(t):
    if not t:
        return ""
    return re.sub(r"\s*\[.*?\]", "", t).strip()

def normalize_text(t):
    if not t:
        return ""
    t = clean_title(t)
    t = re.sub(r"[^\w\s]", " ", t, flags=re.UNICODE).lower()
    return re.sub(r"\s+", " ", t).strip()

# Prepare database games
db_games = []
db_by_id = {}

for g in switch_games:
    tid = g.get("title_id")
    if not tid:
        continue
    norm_tid = str(tid).strip().upper()
    if not norm_tid or norm_tid == "NONE":
        continue
        
    raw_t = g.get("title", "")
    c_title = clean_title(raw_t)
    n_title = normalize_text(raw_t)
    genre_str = g.get("genre", "").lower()
    
    entry = {
        "game": g,
        "title_id": norm_tid,
        "raw_title": raw_t,
        "clean_title": c_title,
        "norm_title": n_title,
        "genre": genre_str,
        "year": str(g.get("year", ""))
    }
    
    db_games.append(entry)
    db_by_id[norm_tid] = entry

print(f"Loaded {len(db_games)} valid database games.")

def match_query(query):
    query_norm = normalize_text(query)
    if not query_norm or len(query_norm) < 2:
        return None
        
    # 1. Exact normalized title match
    for dbe in db_games:
        if dbe["norm_title"] == query_norm:
            return dbe
            
    # 2. Strict word-boundary / phrase match
    pattern = r"\b" + re.escape(query_norm) + r"\b"
    best = None
    best_len = 9999
    
    for dbe in db_games:
        if re.search(pattern, dbe["norm_title"]):
            if len(dbe["clean_title"]) < best_len:
                best_len = len(dbe["clean_title"])
                best = dbe
                
    return best

# Curated game lists for each genre
CURATED_LISTS = {
    "top_100.json": [
        "The Legend of Zelda: Tears of the Kingdom", "The Legend of Zelda: Breath of the Wild",
        "Super Mario Odyssey", "Super Mario Bros. Wonder", "Super Smash Bros. Ultimate",
        "Mario Kart 8 Deluxe", "Metroid Dread", "Metroid Prime Remastered", "Hollow Knight",
        "Hades", "Animal Crossing: New Horizons", "Xenoblade Chronicles 3", "Xenoblade Chronicles 2",
        "Xenoblade Chronicles Definitive Edition", "Persona 5 Royal", "Dragon Quest XI S",
        "Fire Emblem: Three Houses", "Fire Emblem Engage", "Celeste", "Stardew Valley",
        "Luigi's Mansion 3", "Super Mario 3D World", "Super Mario Maker 2", "Pikmin 4",
        "Kirby and the Forgotten Land", "Astral Chain", "Bayonetta 3", "Bayonetta 2",
        "Prince of Persia: The Lost Crown", "Paper Mario: The Origami King", "Super Mario RPG",
        "Pokemon Legends: Arceus", "Pokemon Scarlet", "Pokemon Violet", "Pokemon Sword",
        "Pokemon Shield", "Mario + Rabbids Sparks of Hope", "Mario + Rabbids Kingdom Battle",
        "Monster Hunter Rise", "Monster Hunter Generations Ultimate", "Dead Cells", "Slay the Spire",
        "Binding of Isaac", "Balatro", "Vampire Survivors", "Cuphead", "Ori and the Will of the Wisps",
        "Ori and the Blind Forest", "Blasphemous", "Blasphemous 2", "Sea of Stars", "Octopath Traveler II",
        "Octopath Traveler", "Triangle Strategy", "Tactics Ogre: Reborn", "Shin Megami Tensei V",
        "Persona 4 Golden", "NieR:Automata", "The Witcher 3", "Red Dead Redemption", "Skyrim",
        "DOOM Eternal", "BioShock Collection", "Portal Companion Collection", "Splatoon 3",
        "Splatoon 2", "Super Mario Party", "Mario Party Superstars", "It Takes Two", "Overcooked! 2",
        "Captain Toad: Treasure Tracker", "Donkey Kong Country: Tropical Freeze", "Rayman Legends",
        "Crash Bandicoot N. Sane Trilogy", "Spyro Reignited Trilogy", "Sonic Mania", "Dave the Diver",
        "Dredge", "Cult of the Lamb", "Untitled Goose Game", "Tetris 99", "Suika Game", "Among Us",
        "Streets of Rage 4", "TMNT: Shredder's Revenge", "Amnesia Collection", "Alien Isolation",
        "Resident Evil 4", "Little Nightmares", "Little Nightmares II", "Ace Attorney Trilogy",
        "Danganronpa Decadence", "Steins;Gate Elite", "13 Sentinels: Aegis Rim", "VA-11 Hall-A",
        "Coffee Talk", "Baba Is You", "Snipperclips", "Into the Breach"
    ],
    
    "action_adventure.json": [
        "The Legend of Zelda: Tears of the Kingdom", "The Legend of Zelda: Breath of the Wild",
        "The Legend of Zelda: Link's Awakening", "The Legend of Zelda: Skyward Sword HD",
        "Super Mario Odyssey", "Luigi's Mansion 3", "Okami HD", "Bayonetta", "Bayonetta 2",
        "Bayonetta 3", "Bayonetta Origins", "Astral Chain", "Monster Hunter Rise",
        "Monster Hunter Generations Ultimate", "Prince of Persia: The Lost Crown",
        "Red Dead Redemption", "Grand Theft Auto", "L.A. Noire", "Assassin's Creed IV Black Flag",
        "Assassin's Creed Rogue", "Assassin's Creed II", "Assassin's Creed Brotherhood",
        "Assassin's Creed III", "Lego Star Wars: The Skywalker Saga", "Darksiders Warmastered",
        "Darksiders II Deathinitive", "Darksiders Genesis", "No More Heroes", "No More Heroes 2",
        "No More Heroes 3", "Saints Row: The Third", "Saints Row IV", "Star Wars Jedi Knight",
        "Tomb Raider I-III Remastered", "Devil May Cry", "Devil May Cry 3", "Dragon's Dogma: Dark Arisen",
        "Immortal Fenyx Rising", "Subnautica", "Subnautica Below Zero", "Shadow Man Remastered",
        "Control Ultimate Edition", "Kena: Bridge of Spirits", "Hyrule Warriors: Definitive Edition",
        "Hyrule Warriors: Age of Calamity", "Fire Emblem Warriors: Three Hopes", "One Piece Pirate Warriors 4",
        "Fate/EXTELLA LINK", "Demon Slayer", "Attack on Titan 2"
    ],
    
    "arcade.json": [
        "Streets of Rage 4", "Teenage Mutant Ninja Turtles: Shredder's Revenge", "TMNT Cowabunga Collection",
        "Street Fighter 30th Anniversary Collection", "Capcom Fighting Collection",
        "Marvel vs. Capcom Fighting Collection", "Mortal Kombat 11", "Mortal Kombat 1",
        "Ultra Street Fighter II", "Guilty Gear Strive", "BlazBlue Centralfiction",
        "Dragon Ball FighterZ", "SNK Heroines", "King of Fighters XIII", "Metal Slug",
        "Metal Slug 3", "Metal Slug X", "Metal Slug Tactics", "Windjammers", "Windjammers 2",
        "TowerFall", "PAC-MAN MUSEUM+", "Atari 50", "Konami Arcade Classics", "Capcom Arcade Stadium",
        "Sonic Origins", "SEGA AGES Sonic the Hedgehog", "SEGA AGES Out Run", "SEGA AGES Virtua Racing",
        "Cruis'n Blast", "Horizon Chase Turbo", "Hotshot Racing", "Burnout Paradise Remastered",
        "Grid Autosport", "Fast RMX", "Mario Kart 8 Deluxe", "Crash Team Racing Nitro-Fueled",
        "Team Sonic Racing", "Nickelodeon Kart Racers 3", "Fight'N Rage", "Mother Russia Bleeds",
        "River City Girls", "River City Girls 2", "Double Dragon Gaiden", "Scott Pilgrim vs. The World",
        "Castle Crashers Remastered", "Broforce", "Huntdown", "Blazing Chrome", "Fight Crab"
    ],
    
    "horror.json": [
        "Resident Evil 4", "Resident Evil 2", "Resident Evil 3", "Resident Evil Revelations",
        "Resident Evil Revelations 2", "Resident Evil HD Remaster", "Resident Evil 0",
        "Resident Evil 5", "Resident Evil 6", "Outlast", "Outlast 2", "Alien Isolation",
        "Fatal Frame: Maiden of Black Water", "Fatal Frame: Mask of the Lunar Eclipse",
        "Amnesia Collection", "Amnesia: Rebirth", "Layers of Fear", "Layers of Fear 2",
        "Little Nightmares", "Little Nightmares II", "Dead by Daylight", "Signalis",
        "Tormented Souls", "SOMA", "Darkwood", "Dredge", "Inscryption", "World of Horror",
        "MADiSON", "Five Nights at Freddy's", "Five Nights at Freddy's: Security Breach",
        "Slender: The Arrival", "Deadly Premonition", "Deadly Premonition 2", "Call of Cthulhu",
        "The Coma: Recut", "The Coma 2: Vicious Sisters", "White Day: A Labyrinth Named School",
        "Remothered: Tormented Fathers", "Remothered: Broken Porcelain", "Count Lucanor",
        "Yomawari: Night Alone", "Yomawari: Lost in the Dark", "Perception", "Blair Witch",
        "Bendy and the Ink Machine", "Bendy and the Dark Revival", "Do Not Open", "Monstrum", "In Sound Mind"
    ],
    
    "metroidvania.json": [
        "Hollow Knight", "Metroid Dread", "Metroid Prime Remastered", "Ori and the Blind Forest",
        "Ori and the Will of the Wisps", "Blasphemous", "Blasphemous 2", "Bloodstained: Ritual of the Night",
        "Bloodstained: Curse of the Moon", "Prince of Persia: The Lost Crown", "Axiom Verge",
        "Axiom Verge 2", "Ender Lilies: Quietus of the Knights", "Ender Magnolia", "Guacamelee!",
        "Guacamelee! 2", "Castlevania Advance Collection", "Castlevania Dominus Collection",
        "Castlevania Anniversary Collection", "SteamWorld Dig 2", "SteamWorld Dig", "The Messenger",
        "Monster Boy and the Cursed Kingdom", "Wonder Boy: The Dragon's Trap", "Salt and Sanctuary",
        "Salt and Sacrifice", "Timespinner", "Chasm", "Record of Lodoss War: Deedlit in Wonder Labyrinth",
        "Islets", "Yoku's Island Express", "Nine Sols", "Minoria", "Momodora: Reverie Under the Moonlight",
        "Shadow Complex Remastered", "Touhou Luna Nights", "Astalon: Tears of the Earth",
        "Sundered: Eldritch Edition", "Carrion", "Gato Roboto", "La-Mulana", "La-Mulana 2",
        "Shantae and the Seven Sirens", "Shantae: Half-Genie Hero", "Iconoclasts", "Environmental Station Alpha",
        "Infernax", "Haiku, the Robot", "Worldless", "Afterimage"
    ],
    
    "party_multiplayer.json": [
        "Super Mario Party", "Mario Party Superstars", "Jamboree", "Overcooked! All You Can Eat",
        "Overcooked! 2", "Overcooked!", "Moving Out", "Moving Out 2", "It Takes Two",
        "Snipperclips", "Jackbox Party Pack", "Jackbox Party Pack 2", "Jackbox Party Pack 3",
        "Jackbox Party Pack 4", "Jackbox Party Pack 5", "Jackbox Party Pack 6", "Jackbox Party Pack 7",
        "Jackbox Party Pack 8", "Jackbox Party Pack 9", "Jackbox Party Pack 10", "TowerFall",
        "Lovers in a Dangerous Spacetime", "Boomerang Fu", "Ultimate Chicken Horse", "Heave Ho",
        "Gang Beasts", "Rubber Bandits", "Unrailed!", "Taiko no Tatsujin: Drum 'n' Fun!",
        "Taiko no Tatsujin: Rhythm Festival", "Just Dance 2024", "Just Dance 2023", "WarioWare: Get It Together!",
        "WarioWare: Move It!", "Super Smash Bros. Ultimate", "Mario Kart 8 Deluxe", "Nintendo Switch Sports",
        "Clubhouse Games: 51 Worldwide Classics", "Trine 4: The Nightmare Prince", "Trine 5",
        "Puyo Puyo Tetris 2", "Unravel Two", "Kirby Star Allies", "Broforce", "Rayman Legends",
        "Heads Upper", "Keep Talking and Nobody Explodes", "Astroneer", "Stardew Valley", "Minecraft"
    ],
    
    "platformers.json": [
        "Super Mario Odyssey", "Super Mario Bros. Wonder", "Super Mario 3D World", "Super Mario 3D All-Stars",
        "Celeste", "Donkey Kong Country: Tropical Freeze", "Rayman Legends", "Crash Bandicoot N. Sane Trilogy",
        "Crash Bandicoot 4: It's About Time", "Spyro Reignited Trilogy", "Sonic Mania", "Sonic Frontiers",
        "Sonic Superstars", "Super Meat Boy", "Super Meat Boy Forever", "Yooka-Laylee",
        "Yooka-Laylee and the Impossible Lair", "Kirby and the Forgotten Land", "Kirby Return to Dream Land Deluxe",
        "Kirby Star Allies", "Shovel Knight: Treasure Trove", "A Hat in Time", "New Super Mario Bros. U Deluxe",
        "Super Mario Maker 2", "Yoshi's Crafted World", "Mega Man 11", "Mega Man Legacy Collection",
        "Kaze and the Wild Masks", "Pac-Man World Re-PAC", "Klonoa Phantasy Reverie Series",
        "Penny's Big Breakaway", "Pepper Grinder", "Freedom Planet", "Freedom Planet 2",
        "Psychonauts", "Shantae and the Pirate's Curse", "Giana Sisters: Twisted Dreams",
        "Guacamelee!", "Braid Anniversary Edition", "Cuphead", "Hollow Knight", "Ori and the Blind Forest",
        "Ori and the Will of the Wisps", "The Messenger", "GRIS", "N++", "Spelunky 2", "Little Nightmares", "Inside"
    ],
    
    "puzzles.json": [
        "Captain Toad: Treasure Tracker", "Baba Is You", "Portal Companion Collection", "Tetris 99",
        "Puyo Puyo Tetris", "Puyo Puyo Tetris 2", "Lumines Remastered", "Snipperclips",
        "Picross S", "Picross S2", "Picross S3", "Picross S4", "Picross S5", "Catherine: Full Body",
        "Grindstone", "World of Goo", "Human Fall Flat", "Suika Game", "Untitled Goose Game",
        "Patrick's Parabox", "FEZ", "Monument Valley", "Lorelei and the Laser Eyes", "The Talos Principle",
        "Return of the Obra Dinn", "Chants of Sennaar", "Gorogoa", "Unpacking", "Superliminal",
        "Manifold Garden", "A Monster's Expedition", "Dorfromantik", "The Witness", "Turing Test",
        "Good Job!", "LARA CROFT GO", "Hitman GO", "Bridge Constructor Portal", "Poly Bridge",
        "Poly Bridge 2", "Mini Motorways", "Mini Metro", "Donut County", "Carto", "Ibb & Obb",
        "Trine Enchanted Edition", "Trine 2", "There Is No Game: Wrong Dimension", "Slayaway Camp"
    ],
    
    "roguelike_roguelite.json": [
        "Hades", "Hades II", "Dead Cells", "Slay the Spire", "The Binding of Isaac: Repentance",
        "Enter the Gungeon", "Rogue Legacy", "Rogue Legacy 2", "Vampire Survivors", "Balatro",
        "Risk of Rain 2", "Risk of Rain Returns", "Monster Train", "Spelunky", "Spelunky 2",
        "Darkest Dungeon", "Darkest Dungeon II", "Cult of the Lamb", "Inscryption", "Into the Breach",
        "Crypt of the NecroDancer", "Cadence of Hyrule", "Brotato", "Have a Nice Death",
        "Astral Ascent", "Dicey Dungeons", "Warmnow", "Crown Trick", "Moonlighter", "Children of Morta",
        "Warmnow", "One Step From Eden", "Wildfrost", "Peglin", "Skul: The Hero Slayer",
        "Loop Hero", "Wizard of Legend", "Void Bastards", "Nuclear Throne", "Synthetik",
        "Downwell", "Undermine", "Revita", "Star Wars: Hunters", "Tainted Grail: Conquest",
        "Gunfire Reborn", "Risk of Rain", "Backpack Hero", "Warmnow", "Shotgun King"
    ],
    
    "rpg_jrpg.json": [
        "Persona 5 Royal", "Persona 4 Golden", "Persona 3 Portable", "Dragon Quest XI S",
        "Xenoblade Chronicles Definitive Edition", "Xenoblade Chronicles 2", "Xenoblade Chronicles 3",
        "Fire Emblem: Three Houses", "Fire Emblem Engage", "Octopath Traveler", "Octopath Traveler II",
        "Paper Mario: The Thousand-Year Door", "Super Mario RPG", "The Witcher 3: Wild Hunt",
        "The Elder Scrolls V: Skyrim", "Shin Megami Tensei V: Vengeance", "Shin Megami Tensei III Nocturne",
        "Sea of Stars", "Tales of Vesperia: Definitive Edition", "Ni no Kuni: Wrath of the White Witch",
        "Ni no Kuni II: Revenant Kingdom", "Star Ocean The Second Story R", "LIVE A LIVE",
        "Tactics Ogre: Reborn", "Triangle Strategy", "Grandia HD Collection", "Disgaea 5 Complete",
        "Disgaea 6 Complete", "Disgaea 7", "Pokemon Legends: Arceus", "Pokemon Scarlet",
        "Pokemon Violet", "Pokemon Sword", "Pokemon Shield", "Pokemon Brilliant Diamond",
        "Pokemon Shining Pearl", "Chrono Cross: The Radical Dreamers Edition", "Final Fantasy VII",
        "Final Fantasy VIII Remastered", "Final Fantasy IX", "Final Fantasy X/X-2 HD Remaster",
        "Final Fantasy XII The Zodiac Age", "Crisis Core -Final Fantasy VII- Reunion",
        "Dragon Quest III HD-2D Remake", "Ys VIII: Lacrimosa of DANA", "Ys IX: Monstrum NOX",
        "Atelier Ryza", "Atelier Ryza 2", "Unicorn Overlord", "Cat Quest"
    ],
    
    "shooters.json": [
        "Splatoon 3", "Splatoon 2", "DOOM (2016)", "DOOM Eternal", "DOOM 64", "Wolfenstein II: The New Colossus",
        "Wolfenstein: Youngblood", "Metro 2033 Redux", "Metro: Last Light Redux", "Borderlands: Legendary Collection",
        "Borderlands 2", "Borderlands 3", "BioShock Remastered", "BioShock Infinite", "Metroid Prime Remastered",
        "Quake", "Quake II", "Crysis Remastered", "Serious Sam Collection", "Sniper Elite 4",
        "Sniper Elite V2 Remastered", "Bulletstorm: Duke of Switch Edition", "Prodeus", "Ikaruga",
        "Radiant Silvergun", "Mushihimesama", "Raiden IV x MIKADO remix", "Cuphead", "Jamestown+",
        "R-Type Final 2", "Cotton Reboot!", "Dariusburst Chronicle Saviours", "DoDonPachi Resurrection",
        "ESP Ra.De. Psi", "Danmaku Unlimited 3", "Devil Engine", "Sine Mora EX", "Star Wars Battlefront Classic Collection",
        "Apex Legends", "Overwatch 2", "Fortnite", "Rogue Company", "Pikmin 4", "Plants vs. Zombies: Battle for Neighborville",
        "Risk of Rain 2", "Ion Fury", "Dusk", "Warhammer 40,000: Boltgun", "Warframe"
    ],
    
    "simulation_cozy.json": [
        "Animal Crossing: New Horizons", "Stardew Valley", "Story of Seasons: Pioneers of Olive Town",
        "Story of Seasons: Friends of Mineral Town", "Story of Seasons: A Wonderful Life",
        "Rune Factory 4 Special", "Rune Factory 5", "Rune Factory 3 Special", "Spiritfarer",
        "Unpacking", "Dave the Diver", "Slime Rancher: Plortable Edition", "House Flipper",
        "PowerWash Simulator", "Two Point Hospital", "Two Point Campus", "Cozy Grove",
        "A Short Hike", "Lil Gator Game", "Disney Dreamlight Valley", "My Time at Portia",
        "My Time at Sandrock", "Potion Permit", "Bear and Breakfast", "Fashion Dreamer",
        "Hello Kitty Island Adventure", "Paleo Pines", "Fae Farm", "Farm Together",
        "Subnautica", "SimCity", "Cities: Skylines", "Jurrasic World Evolution", "Tropico 6",
        "Farming Simulator 23", "Farming Simulator 20", "Goat Simulator", "Arcade Paradise",
        "Gas Station Simulator", "Car Mechanic Simulator", "Cook, Serve, Delicious! 3?!",
        "Lemon Cake", "Sticky Business", "Alba: A Wildlife Adventure", "Haven", "Wytchwood",
        "Roots of Pacha", "Moonstone Island", "Snacko", "Slime Rancher"
    ],
    
    "strategy_tactics.json": [
        "Fire Emblem: Three Houses", "Fire Emblem Engage", "Into the Breach", "Triangle Strategy",
        "Tactics Ogre: Reborn", "Mario + Rabbids Kingdom Battle", "Mario + Rabbids Sparks of Hope",
        "Sid Meier's Civilization VI", "Advance Wars 1+2: Re-Boot Camp", "Wargroove", "Wargroove 2",
        "Valkyria Chronicles", "Valkyria Chronicles 4", "XCOM 2 Collection", "Unicorn Overlord",
        "Shadow Tactics: Blades of the Shogun", "Desperados III", "SteamWorld Heist",
        "SteamWorld Heist II", "The Banner Saga", "The Banner Saga 2", "The Banner Saga 3",
        "Bad North", "Northgard", "Two Point Hospital", "Loop Hero", "Tactical Breach Wizards",
        "Fell Seal: Arbiter's Mark", "Othercide", "Disgaea 5 Complete", "Disgaea 7",
        "Mercenaries Saga Chronicles", "Digimon Survive", "Marvel's Midnight Suns",
        "Warhammer Age of Sigmar: Realm War", "Stellaris", "Tropico 6", "Frostpunk",
        "Dungeons 3", "Port Royale 4", "Railway Empire", "Subterrain", "Inscryption",
        "Slay the Spire", "Monster Train", "Darkest Dungeon", "Mutant Year Zero: Road to Eden",
        "Empire of Sin", "Iron Harvest"
    ],
    
    "visual_novels.json": [
        "Phoenix Wright: Ace Attorney Trilogy", "The Great Ace Attorney Chronicles", "Apollo Justice: Ace Attorney Trilogy",
        "Danganronpa Decadence", "Danganronpa: Trigger Happy Havoc", "Danganronpa 2: Goodbye Despair",
        "Danganronpa V3: Killing Harmony", "Steins;Gate Elite", "Steins;Gate 0", "Steins;Gate: My Darling's Embrace",
        "AI: The Somnium Files", "AI: The Somnium Files - nirvanA Initiative", "VA-11 Hall-A",
        "Coffee Talk", "Coffee Talk Episode 2: Hibiscus & Butterfly", "13 Sentinels: Aegis Rim",
        "The House in Fata Morgana", "Raging Loop", "Clannad", "Cupid Parasite", "Collar x Malice",
        "Code: Realize ~Guardian of Rebirth~", "Bustafellows", "Master Detective Archives: RAIN CODE",
        "PARANORMASIGHT: The Seven Mysteries of Honjo", "World End Syndrome", "Digimon Survive",
        "Witch on the Holy Night", "TSUKIHIME -A piece of blue glass moon-", "CHAOS;CHILD",
        "ROBOTICS;NOTES ELITE", "ANONYMOUS;CODE", "Kanon", "AIR", "Little Busters! Converted Edition",
        "Buried Stars", "Ib", "Milk inside a bag of milk", "Slay the Princess", "Needy Streamer Overload",
        "Doki Doki Literature Club Plus!", "Over the Alps", "If My Heart Had Wings", "Gakuen Club",
        "Nightshade", "Taisho x Alice", "Piofiore: Fated Memories", "Amnesia: Memories", "Jack Jeanne", "Radiant Tale"
    ]
}

# Process each collection
base_dir = Path("d:/switch-game-collection")
collection_files = [f for f in base_dir.glob("*.json") if f.name not in ("switch_games.json", "new_release.json")]

summary = {}

for filepath in sorted(collection_files):
    filename = filepath.name
    queries = CURATED_LISTS.get(filename, [])
    
    selected_items = []
    seen_tids = set()
    
    # 1. Add curated matches
    for q in queries:
        m = match_query(q)
        if m and m["title_id"] not in seen_tids:
            seen_tids.add(m["title_id"])
            selected_items.append({
                "title": m["clean_title"],
                "title_id": m["title_id"]
            })
            if len(selected_items) == 100:
                break
                
    # 2. If needed < 100, fill using strict genre keyword from database
    if len(selected_items) < 100:
        genre_keywords = {
            "action_adventure.json": ["action", "adventure"],
            "arcade.json": ["arcade", "beatemup", "fighting", "racing"],
            "horror.json": ["horror", "survival"],
            "metroidvania.json": ["metroidvania"],
            "party_multiplayer.json": ["party", "multiplayer", "board game"],
            "platformers.json": ["platformer", "3d platformer", "runner"],
            "puzzles.json": ["puzzle", "hidden objects"],
            "roguelike_roguelite.json": ["roguelite", "roguelike", "tcg"],
            "rpg_jrpg.json": ["role-playing", "rpg", "jrpg"],
            "shooters.json": ["shooter", "first person shooter", "fps"],
            "simulation_cozy.json": ["simulator", "simulation", "farm", "cozy"],
            "strategy_tactics.json": ["strategy", "tactic", "tower defense"],
            "top_100.json": [],
            "visual_novels.json": ["visual novel", "interactive fiction", "otome"]
        }.get(filename, [])
        
        candidates = []
        for dbe in db_games:
            tid = dbe["title_id"]
            if tid in seen_tids:
                continue
            if not genre_keywords:
                candidates.append(dbe)
            else:
                g_lower = dbe["genre"]
                if any(gk in g_lower for gk in genre_keywords):
                    candidates.append(dbe)
                    
        for c in candidates:
            if len(selected_items) >= 100:
                break
            seen_tids.add(c["title_id"])
            selected_items.append({
                "title": c["clean_title"],
                "title_id": c["title_id"]
            })
            
    # Write back clean JSON
    lines = ["[\n"]
    for i, elem in enumerate(selected_items):
        comma = "," if i < len(selected_items) - 1 else ""
        lines.append(f"  {json.dumps(elem, ensure_ascii=False)}{comma}\n")
    lines.append("]\n")
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(lines)
        
    summary[filename] = len(selected_items)

print("\n=== CURATED COLLECTIONS CREATED ===")
for fn, count in summary.items():
    print(f"  {fn:25s}: {count} items")
