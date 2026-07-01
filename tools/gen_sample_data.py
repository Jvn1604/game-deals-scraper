import json
import random
from pathlib import Path
from urllib.parse import quote

random.seed(42)
DATA_DIR = Path(__file__).parent.parent / "data"

# Real Steam appids for titles we're confident about -> link straight to the
# store page. Anything else gets a Steam search link instead, so we never
# risk pointing at a wrong/broken app page for a made-up id.
KNOWN_APPIDS = {
    "Cyberpunk 2077": "1091500",
    "Elden Ring": "1245620",
    "The Witcher 3: Wild Hunt": "292030",
    "Baldur's Gate 3": "1086940",
    "Red Dead Redemption 2": "1174180",
    "Grand Theft Auto V": "271590",
    "Stardew Valley": "413150",
    "Portal 2": "620",
    "Titanfall 2": "1237970",
    "Sid Meier's Civilization VI": "289070",
    "Hearts of Iron IV": "394360",
    "Cities: Skylines": "255710",
    "Euro Truck Simulator 2": "227300",
    "Forza Horizon 5": "1245621",
    "Rocket League": "252950",
    "Slay the Spire": "863550",
    "Celeste": "504230",
    "Vampire Survivors": "1794680",
    "Yakuza: Like a Dragon": "1449850",
    "Disco Elysium: The Final Cut": "632470",
    "It Takes Two": "1426210",
    "Subnautica": "264710",
    "Age of Empires II: Definitive Edition": "813780",
    "Battlefield 2042": "1517290",
    "PUBG: Battlegrounds": "578080",
    "Call of Duty: MW III": "1938090",
    "Hades": "1145360",
    "Hollow Knight": "367520",
    "Dead Cells": "588650",
    "Terraria": "105600",
    "Undertale": "391540",
    "Among Us": "945360",
    "DOOM Eternal": "782330",
    "Sekiro: Shadows Die Twice": "814380",
    "Devil May Cry 5": "601150",
    "Resident Evil 4": "2050650",
    "Dying Light 2": "534380",
    "Sifu": "1222730",
    "Divinity: Original Sin 2": "435150",
    "Fallout 4": "377160",
    "The Elder Scrolls V: Skyrim Special Edition": "489830",
    "Kingdom Come: Deliverance": "379430",
    "Diablo IV": "2344520",
    "XCOM 2": "268500",
    "Stellaris": "281990",
    "Crusader Kings III": "1158310",
    "Total War: WARHAMMER III": "1142710",
    "Frostpunk": "323190",
    "They Are Billions": "644930",
    "Into the Breach": "590380",
    "Wargroove": "607050",
    "Microsoft Flight Simulator": "1250410",
    "Farming Simulator 22": "1248130",
    "PC Building Simulator": "621060",
    "House Flipper": "606150",
    "Two Point Hospital": "535930",
    "Planet Zoo": "703080",
    "Kerbal Space Program": "220200",
    "The Sims 4": "1222670",
    "Prison Architect": "233450",
    "FIFA 23": "1811260",
    "NBA 2K24": "2338770",
    "F1 24": "2488620",
    "Football Manager 2024": "2252570",
    "Tony Hawk's Pro Skater 1+2": "1088090",
    "OlliOlli World": "1352950",
    "F1 23": "2108330",
    "Need for Speed Heat": "1222680",
    "Dirt Rally 2.0": "690790",
    "Grid Legends": "1307710",
    "Wreckfest": "228380",
    "Assetto Corsa Competizione": "805550",
    "Trackmania": "2225070",
    "Riders Republic": "1366800",
    "The Crew 2": "646910",
    "Hot Wheels Unleashed": "1707430",
    "Life is Strange: True Colors": "1042420",
    "A Plague Tale: Requiem": "1182900",
    "Firewatch": "383870",
    "Outer Wilds": "753640",
    "Sea of Thieves": "1172620",
    "Journey": "638230",
    "Kentucky Route Zero": "231200",
    "Risk of Rain 2": "632360",
    "Cult of the Lamb": "1313140",
    "Spiritfarer": "972660",
    "What Remains of Edith Finch": "501300",
    "Metal Gear Solid V: The Phantom Pain": "287700",
    "Mass Effect Legendary Edition": "1328670",
    "Dragon Age: Inquisition": "1222690",
    "Uncharted 4: A Thief's End": "1659420",
    "Tomb Raider": "203160",
    "Cities: Skylines II": "949230",
    "Company of Heroes 3": "1677280",
    "Northgard": "466560",
    "Angry Birds Golf Battle": "0",
    "eFootball": "1665460",
    "Madden NFL 24": "0",
    "NHL 24": "0",
    "Golf With Your Friends": "431240",
    "Forza Motorsport": "2440510",
    "WWE 2K24": "0",
}

# (title, genre, original_price, discount_pct)
CATALOG = [
    # ---- Action ----
    ("Red Dead Redemption 2", "Action", 59.99, 60),
    ("Grand Theft Auto V", "Action", 29.99, 75),
    ("Titanfall 2", "Action", 19.99, 80),
    ("Battlefield 2042", "Action", 39.99, 75),
    ("Call of Duty: MW III", "Action", 69.99, 20),
    ("DOOM Eternal", "Action", 39.99, 70),
    ("Sekiro: Shadows Die Twice", "Action", 59.99, 50),
    ("Devil May Cry 5", "Action", 29.99, 75),
    ("Resident Evil 4", "Action", 59.99, 40),
    ("Dying Light 2", "Action", 59.99, 65),
    ("Sifu", "Action", 39.99, 55),
    ("PUBG: Battlegrounds", "Action", 0.00, 0),
    ("Metal Gear Solid V: The Phantom Pain", "Action", 39.99, 80),

    # ---- RPG ----
    ("Cyberpunk 2077", "RPG", 59.99, 70),
    ("Elden Ring", "RPG", 59.99, 30),
    ("The Witcher 3: Wild Hunt", "RPG", 39.99, 80),
    ("Baldur's Gate 3", "RPG", 59.99, 20),
    ("Disco Elysium: The Final Cut", "RPG", 39.99, 75),
    ("Yakuza: Like a Dragon", "RPG", 59.99, 80),
    ("Divinity: Original Sin 2", "RPG", 44.99, 70),
    ("Fallout 4", "RPG", 19.99, 75),
    ("The Elder Scrolls V: Skyrim Special Edition", "RPG", 39.99, 75),
    ("Kingdom Come: Deliverance", "RPG", 29.99, 80),
    ("Diablo IV", "RPG", 69.99, 33),
    ("Mass Effect Legendary Edition", "RPG", 59.99, 75),
    ("Dragon Age: Inquisition", "RPG", 29.99, 80),

    # ---- Strategy ----
    ("Sid Meier's Civilization VI", "Strategy", 59.99, 90),
    ("Hearts of Iron IV", "Strategy", 39.99, 60),
    ("Age of Empires II: Definitive Edition", "Strategy", 19.99, 80),
    ("Total War: WARHAMMER III", "Strategy", 59.99, 70),
    ("Crusader Kings III", "Strategy", 49.99, 50),
    ("XCOM 2", "Strategy", 59.99, 85),
    ("Stellaris", "Strategy", 39.99, 75),
    ("Frostpunk", "Strategy", 29.99, 85),
    ("They Are Billions", "Strategy", 29.99, 60),
    ("Into the Breach", "Strategy", 14.99, 50),
    ("Wargroove", "Strategy", 19.99, 60),
    ("Company of Heroes 3", "Strategy", 49.99, 55),
    ("Northgard", "Strategy", 19.99, 65),

    # ---- Simulation ----
    ("Cities: Skylines", "Simulation", 29.99, 80),
    ("Euro Truck Simulator 2", "Simulation", 19.99, 80),
    ("Microsoft Flight Simulator", "Simulation", 59.99, 40),
    ("Farming Simulator 22", "Simulation", 39.99, 60),
    ("PC Building Simulator", "Simulation", 19.99, 70),
    ("House Flipper", "Simulation", 16.99, 70),
    ("Two Point Hospital", "Simulation", 34.99, 75),
    ("Planet Zoo", "Simulation", 44.99, 60),
    ("Kerbal Space Program", "Simulation", 39.99, 75),
    ("The Sims 4", "Simulation", 0.00, 0),
    ("Prison Architect", "Simulation", 29.99, 85),
    ("American Truck Simulator", "Simulation", 19.99, 80),
    ("Cities: Skylines II", "Simulation", 49.99, 30),

    # ---- Sports ----
    ("FIFA 23", "Sports", 59.99, 75),
    ("NBA 2K24", "Sports", 69.99, 70),
    ("Rocket League", "Sports", 0.00, 0),
    ("PGA Tour 2K23", "Sports", 59.99, 65),
    ("WWE 2K24", "Sports", 69.99, 45),
    ("eFootball", "Sports", 0.00, 0),
    ("Football Manager 2024", "Sports", 54.99, 60),
    ("Tony Hawk's Pro Skater 1+2", "Sports", 39.99, 70),
    ("Madden NFL 24", "Sports", 69.99, 55),
    ("NHL 24", "Sports", 59.99, 50),
    ("Golf With Your Friends", "Sports", 14.99, 60),
    ("OlliOlli World", "Sports", 29.99, 65),
    ("Angry Birds Golf Battle", "Sports", 0.00, 0),

    # ---- Racing ----
    ("Forza Horizon 5", "Racing", 59.99, 50),
    ("F1 24", "Racing", 69.99, 40),
    ("Need for Speed Heat", "Racing", 39.99, 80),
    ("Dirt Rally 2.0", "Racing", 34.99, 75),
    ("Grid Legends", "Racing", 49.99, 75),
    ("Wreckfest", "Racing", 29.99, 75),
    ("Assetto Corsa Competizione", "Racing", 39.99, 60),
    ("Trackmania", "Racing", 0.00, 0),
    ("Riders Republic", "Racing", 59.99, 80),
    ("F1 23", "Racing", 69.99, 55),
    ("The Crew 2", "Racing", 29.99, 80),
    ("Hot Wheels Unleashed", "Racing", 39.99, 70),
    ("Forza Motorsport", "Racing", 59.99, 30),

    # ---- Adventure ----
    ("Portal 2", "Adventure", 9.99, 80),
    ("It Takes Two", "Adventure", 39.99, 60),
    ("Subnautica", "Adventure", 29.99, 80),
    ("Life is Strange: True Colors", "Adventure", 39.99, 75),
    ("A Plague Tale: Requiem", "Adventure", 49.99, 60),
    ("Firewatch", "Adventure", 19.99, 70),
    ("Outer Wilds", "Adventure", 24.99, 50),
    ("Sea of Thieves", "Adventure", 39.99, 50),
    ("Uncharted 4: A Thief's End", "Adventure", 39.99, 65),
    ("Tomb Raider", "Adventure", 19.99, 85),
    ("Journey", "Adventure", 14.99, 40),
    ("Kentucky Route Zero", "Adventure", 24.99, 60),
    ("What Remains of Edith Finch", "Adventure", 19.99, 60),

    # ---- Indie ----
    ("Stardew Valley", "Indie", 14.99, 40),
    ("Celeste", "Indie", 19.99, 80),
    ("Vampire Survivors", "Indie", 4.99, 50),
    ("Slay the Spire", "Indie", 24.99, 75),
    ("Hollow Knight", "Indie", 14.99, 70),
    ("Dead Cells", "Indie", 24.99, 60),
    ("Hades", "Indie", 24.99, 60),
    ("Undertale", "Indie", 9.99, 50),
    ("Terraria", "Indie", 9.99, 50),
    ("Risk of Rain 2", "Indie", 24.99, 60),
    ("Cult of the Lamb", "Indie", 24.99, 50),
    ("Spiritfarer", "Indie", 29.99, 70),
    ("Among Us", "Indie", 4.99, 0),
]


def build_steam_deals():
    seen_titles = set()
    deals = []
    for title, genre, original, discount in CATALOG:
        if title in seen_titles:
            continue
        seen_titles.add(title)

        price = round(original * (1 - discount / 100), 2)
        appid = KNOWN_APPIDS.get(title)
        if appid and appid != "0":
            url = f"https://store.steampowered.com/app/{appid}"
            deal_id = appid
        else:
            url = f"https://store.steampowered.com/search/?term={quote(title)}"
            deal_id = f"s-{abs(hash(title)) % 10_000_000}"

        deals.append({
            "appid": deal_id,
            "title": title,
            "genre": genre,
            "store": "Steam",
            "original_price": original,
            "price": price,
            "discount_pct": discount,
            "url": url,
        })
    return deals


# ---------- Cross-store (CheapShark-style) sample data ----------
CROSS_STORE_CATALOG = [
    ("Persona 5 Royal", "RPG", "Epic Games Store", 59.99, 75),
    ("Mass Effect Legendary Edition", "RPG", "Origin", 59.99, 70),
    ("Divinity: Original Sin 2", "RPG", "GOG", 44.99, 80),
    ("Dragon Age: Inquisition", "RPG", "Origin", 29.99, 80),
    ("Pillars of Eternity II", "RPG", "GOG", 44.99, 85),
    ("Total War: Warhammer III", "Strategy", "Epic Games Store", 59.99, 70),
    ("Frostpunk", "Strategy", "GOG", 29.99, 85),
    ("Age of Wonders 4", "Strategy", "Fanatical", 49.99, 60),
    ("Anno 1800", "Strategy", "Uplay", 49.99, 70),
    ("Endless Space 2", "Strategy", "GreenManGaming", 34.99, 75),
    ("Dishonored 2", "Action", "Fanatical", 29.99, 80),
    ("Dying Light 2", "Action", "GamersGate", 59.99, 70),
    ("DOOM Eternal", "Action", "Fanatical", 39.99, 75),
    ("Metro Exodus", "Action", "Epic Games Store", 39.99, 80),
    ("Wolfenstein II: The New Colossus", "Action", "GreenManGaming", 39.99, 85),
    ("Ori and the Will of the Wisps", "Adventure", "GreenManGaming", 29.99, 70),
    ("It Takes Two", "Adventure", "Origin", 39.99, 60),
    ("A Way Out", "Adventure", "Origin", 29.99, 75),
    ("Firewatch", "Adventure", "Humble Store", 19.99, 70),
    ("Subnautica: Below Zero", "Adventure", "Epic Games Store", 29.99, 55),
    ("Hollow Knight", "Indie", "Humble Store", 14.99, 70),
    ("Shovel Knight: Treasure Trove", "Indie", "Humble Store", 29.99, 70),
    ("Katana ZERO", "Indie", "GOG", 14.99, 60),
    ("Cuphead", "Indie", "GOG", 19.99, 50),
    ("Cassette Beasts", "Indie", "IndieGala", 24.99, 45),
    ("F1 23", "Racing", "Origin", 69.99, 60),
    ("Forza Horizon 4", "Racing", "Uplay", 49.99, 80),
    ("Need for Speed Unbound", "Racing", "Origin", 69.99, 65),
    ("WRC Generations", "Racing", "GamersGate", 39.99, 70),
    ("Trackmania Turbo", "Racing", "GreenManGaming", 29.99, 75),
    ("Football Manager 2024", "Sports", "GreenManGaming", 54.99, 60),
    ("FIFA 23", "Sports", "Origin", 59.99, 75),
    ("Rocket League", "Sports", "Epic Games Store", 0.00, 0),
    ("Tony Hawk's Pro Skater 1+2", "Sports", "Fanatical", 39.99, 70),
    ("PGA Tour 2K23", "Sports", "GamersGate", 59.99, 65),
    ("The Elder Scrolls V: Skyrim", "Other", "GOG", 39.99, 85),
    ("Fallout: New Vegas", "Other", "Humble Store", 19.99, 80),
    ("Cyberpunk 2077", "RPG", "GOG", 59.99, 65),
    ("Baldur's Gate 3", "RPG", "GOG", 59.99, 20),
    ("Two Point Campus", "Simulation", "Epic Games Store", 34.99, 55),
    ("Planet Coaster", "Simulation", "Fanatical", 44.99, 70),
]


def build_cross_store_deals():
    seen = set()
    deals = []
    for idx, (title, genre, store, original, discount) in enumerate(CROSS_STORE_CATALOG, start=1):
        key = (title, store)
        if key in seen:
            continue
        seen.add(key)

        price = round(original * (1 - discount / 100), 2)
        deal_id = f"cs-{idx}"
        deals.append({
            "appid": deal_id,
            "title": title,
            "genre": genre,
            "store": store,
            "original_price": original,
            "price": price,
            "discount_pct": discount,
            "url": f"https://www.cheapshark.com/redirect?dealID={deal_id}",
        })
    return deals


if __name__ == "__main__":
    steam_deals = build_steam_deals()
    cross_store_deals = build_cross_store_deals()

    with open(DATA_DIR / "sample_deals.json", "w", encoding="utf-8") as f:
        json.dump(steam_deals, f, indent=2)

    with open(DATA_DIR / "sample_cheapshark_deals.json", "w", encoding="utf-8") as f:
        json.dump(cross_store_deals, f, indent=2)

    print(f"Wrote {len(steam_deals)} Steam sample deals")
    print(f"Wrote {len(cross_store_deals)} cross-store sample deals")
    print(f"Total: {len(steam_deals) + len(cross_store_deals)}")
