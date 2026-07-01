"""
scraper.py
----------
Scrapes currently discounted games from the Steam Store "Specials" page
using requests + BeautifulSoup, and saves the results as JSON.

Steam doesn't expose genre in the specials list directly, so this scrapes
the specials page once per genre tag (using Steam's own tag filter) and
labels each game with the genre it was found under. A game that shows up
under more than one tag keeps the first genre it was seen with.

Run directly to refresh data/deals.json:
    python scraper.py

If the site is unreachable (blocked network, layout change, etc.) the
scraper falls back to data/sample_deals.json so the dashboard always has
something to show. Delete data/deals.json to force a fresh scrape.
"""

import json
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://store.steampowered.com/search/"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}

# Steam tag IDs for common genres (subset, easy to extend)
GENRE_TAGS = {
    "Action": 19,
    "Adventure": 21,
    "RPG": 122,
    "Strategy": 9,
    "Simulation": 599,
    "Sports": 701,
    "Indie": 492,
    "Racing": 699,
}

DATA_DIR = Path(__file__).parent / "data"
OUTPUT_FILE = DATA_DIR / "deals.json"
FALLBACK_FILE = DATA_DIR / "sample_deals.json"

RESULTS_PER_GENRE = 25  # keep it light and fast
REQUEST_DELAY = 1.0     # seconds between requests, be polite


def _parse_price(text):
    """Turn a Steam price string like '$9.99' or 'Free' into a float."""
    if not text:
        return None
    text = text.strip()
    if text.lower() in ("free", "free to play"):
        return 0.0
    cleaned = "".join(ch for ch in text if ch.isdigit() or ch == ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def _scrape_genre(genre, tag_id, session):
    params = {
        "specials": "1",
        "tags": tag_id,
        "l": "english",
        "cc": "us",
    }
    resp = session.get(BASE_URL, params=params, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    rows = soup.select("a.search_result_row")
    deals = []

    for row in rows[:RESULTS_PER_GENRE]:
        appid = row.get("data-ds-appid")
        title_el = row.select_one(".title")
        if not title_el or not appid:
            continue
        title = title_el.get_text(strip=True)

        discount_el = row.select_one(".discount_pct")
        discount = 0
        if discount_el:
            discount_text = discount_el.get_text(strip=True).replace("-", "").replace("%", "")
            discount = int(discount_text) if discount_text.isdigit() else 0

        final_price_el = row.select_one(".discount_final_price")
        original_price_el = row.select_one(".discount_original_price")

        final_price = _parse_price(final_price_el.get_text() if final_price_el else None)
        original_price = _parse_price(original_price_el.get_text() if original_price_el else None)

        if final_price is None:
            # non-discounted or free listing, skip since this feed is specials-only
            continue
        if original_price is None:
            original_price = final_price

        deals.append({
            "appid": appid,
            "title": title,
            "genre": genre,
            "store": "Steam",
            "original_price": round(original_price, 2),
            "price": round(final_price, 2),
            "discount_pct": discount,
            "url": f"https://store.steampowered.com/app/{appid}",
        })

    return deals


def scrape_all():
    session = requests.Session()
    all_deals = {}

    for genre, tag_id in GENRE_TAGS.items():
        try:
            deals = _scrape_genre(genre, tag_id, session)
        except Exception as exc:  # network errors, layout changes, etc.
            print(f"  [!] Failed to scrape '{genre}': {exc}")
            continue

        for deal in deals:
            # first genre a game is seen under wins, avoids duplicate rows
            all_deals.setdefault(deal["appid"], deal)

        print(f"  [+] {genre}: {len(deals)} deals found")
        time.sleep(REQUEST_DELAY)

    return list(all_deals.values())


def save_deals(deals, path=OUTPUT_FILE):
    DATA_DIR.mkdir(exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(deals, f, indent=2)
    print(f"Saved {len(deals)} deals to {path}")


def load_deals():
    """Steam-only deals. Prefers freshly scraped data, falls back to sample data."""
    for path in (OUTPUT_FILE, FALLBACK_FILE):
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                deals = json.load(f)
                for d in deals:
                    d.setdefault("store", "Steam")
                return deals
    return []


def load_all_deals():
    """Steam deals + CheapShark cross-store deals, merged, for the dashboard."""
    import cheapshark
    return load_deals() + cheapshark.load_deals()


if __name__ == "__main__":
    import db
    import cheapshark

    db.init_db()

    print("Scraping Steam specials by genre...")
    steam_deals = scrape_all()
    if not steam_deals:
        print("No Steam deals scraped (site may be unreachable) - using sample data instead.")
    else:
        save_deals(steam_deals)

    print("Fetching CheapShark cross-store deals...")
    try:
        cs_deals = cheapshark.fetch_deals()
        cheapshark.save_deals(cs_deals)
    except Exception as exc:
        print(f"  [!] CheapShark fetch failed: {exc} - using sample data instead.")

    all_deals = load_all_deals()
    db.record_price_snapshot(all_deals)

    triggered = db.check_watch_alerts(all_deals)
    if triggered:
        print("\nWatchlist alerts:")
        for t in triggered:
            print(f"  [$] {t['title']} is now ${t['current_price']:.2f} "
                  f"(target was ${t['target_price']:.2f})")
