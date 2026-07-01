"""
cheapshark.py
-------------
Pulls cross-store deals from the CheapShark API (no key required):
https://www.cheapshark.com/api/1.0/deals

This is a second, independent data source alongside scraper.py's Steam
scrape — CheapShark aggregates ~30 stores (GOG, Epic, Humble, Fanatical,
etc.) so it fills in stores Steam-only scraping can't see.

CheapShark doesn't return genre, so titles are matched against a small
known-genre lookup (reused from the Steam sample set) and anything
unmatched is filed under "Other". Good enough for a filter facet; not
meant to be authoritative.
"""

import json
from pathlib import Path

import requests

API_URL = "https://www.cheapshark.com/api/1.0/deals"
DATA_DIR = Path(__file__).parent / "data"
OUTPUT_FILE = DATA_DIR / "cheapshark_deals.json"
FALLBACK_FILE = DATA_DIR / "sample_cheapshark_deals.json"

PARAMS = {
    "storeID": None,       # None = all stores
    "upperPrice": 60,
    "pageSize": 40,
    "sortBy": "Savings",
    "desc": 1,
}

# CheapShark's numeric store IDs -> readable names (subset covering common stores)
STORE_NAMES = {
    "1": "Steam", "2": "GamersGate", "3": "GreenManGaming", "7": "GOG",
    "8": "Origin", "11": "Humble Store", "13": "Uplay", "15": "Fanatical",
    "21": "WinGameStore", "23": "GameBillet", "25": "Epic Games Store",
    "27": "Gamesplanet", "30": "IndieGala", "31": "Blizzard Shop",
    "33": "Voidu",
}

# Reused so cross-store titles land in a sensible genre bucket when we
# recognize them from the Steam sample data; unknown titles fall back to "Other".
_KNOWN_GENRES = {
    "cyberpunk 2077": "RPG", "elden ring": "RPG", "the witcher 3": "RPG",
    "baldur's gate 3": "RPG", "disco elysium": "RPG", "yakuza": "RPG",
    "red dead redemption 2": "Action", "grand theft auto v": "Action",
    "titanfall 2": "Action", "battlefield": "Action", "call of duty": "Action",
    "stardew valley": "Indie", "hades": "Indie", "celeste": "Indie",
    "slay the spire": "Indie", "vampire survivors": "Indie",
    "portal 2": "Adventure", "it takes two": "Adventure", "subnautica": "Adventure",
    "civilization": "Strategy", "hearts of iron": "Strategy", "age of empires": "Strategy",
    "cities: skylines": "Simulation", "euro truck simulator": "Simulation",
    "forza horizon": "Racing", "f1 ": "Racing",
    "rocket league": "Sports", "fifa": "Sports", "nba 2k": "Sports",
}


def _guess_genre(title):
    lowered = title.lower()
    for key, genre in _KNOWN_GENRES.items():
        if key in lowered:
            return genre
    return "Other"


def fetch_deals():
    resp = requests.get(API_URL, params={k: v for k, v in PARAMS.items() if v is not None}, timeout=15)
    resp.raise_for_status()
    raw = resp.json()

    deals = []
    for item in raw:
        try:
            price = float(item["salePrice"])
            original = float(item["normalPrice"])
            discount = round(float(item["savings"]))
        except (KeyError, ValueError, TypeError):
            continue

        store = STORE_NAMES.get(item.get("storeID"), f"Store {item.get('storeID')}")
        title = item.get("title", "Unknown title")

        deals.append({
            "appid": f"cs-{item.get('dealID', title)}",
            "title": title,
            "genre": _guess_genre(title),
            "store": store,
            "original_price": round(original, 2),
            "price": round(price, 2),
            "discount_pct": discount,
            "url": f"https://www.cheapshark.com/redirect?dealID={item.get('dealID', '')}",
        })

    return deals


def save_deals(deals, path=OUTPUT_FILE):
    DATA_DIR.mkdir(exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(deals, f, indent=2)
    print(f"Saved {len(deals)} CheapShark deals to {path}")


def load_deals():
    for path in (OUTPUT_FILE, FALLBACK_FILE):
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    return []


if __name__ == "__main__":
    print("Fetching CheapShark cross-store deals...")
    try:
        deals = fetch_deals()
        save_deals(deals)
    except Exception as exc:
        print(f"  [!] CheapShark fetch failed: {exc}")
        print("  Dashboard will use sample_cheapshark_deals.json instead.")
