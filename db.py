"""
db.py
-----
SQLite persistence for the dashboard.

Two concerns live here:
  1. Price history — every time a deal is (re)scraped, if its price changed
     since the last snapshot we record a new history row. This is what
     powers the per-game sparkline in the UI.
  2. Watchlist — the user can "watch" a game with a target price. The
     scraper checks the watchlist after every run and flags anything that
     has dropped to/below its target (see check_watch_alerts()).

The JSON files (data/deals.json, data/sample_deals.json) remain the
source of truth for "what deals exist right now" — the DB layers price
history and watchlist state on top without needing a schema migration
every time the scraper's fields change.
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "deals.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    appid TEXT NOT NULL,
    store TEXT NOT NULL DEFAULT 'Steam',
    title TEXT NOT NULL,
    price REAL NOT NULL,
    discount_pct INTEGER NOT NULL DEFAULT 0,
    scraped_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_history_appid ON price_history(appid, store);

CREATE TABLE IF NOT EXISTS watchlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    appid TEXT NOT NULL,
    store TEXT NOT NULL DEFAULT 'Steam',
    title TEXT NOT NULL,
    target_price REAL NOT NULL,
    created_at TEXT NOT NULL,
    alert_met_at TEXT
);
"""


@contextmanager
def get_conn():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def record_price_snapshot(deals):
    """
    Insert a history row for each deal, but only if the price differs from
    the most recent recorded price for that appid+store (avoids a row per
    scrape run when nothing changed).
    """
    with get_conn() as conn:
        for deal in deals:
            appid = deal["appid"]
            store = deal.get("store", "Steam")
            last = conn.execute(
                "SELECT price FROM price_history WHERE appid = ? AND store = ? "
                "ORDER BY id DESC LIMIT 1",
                (appid, store),
            ).fetchone()

            if last is not None and float(last["price"]) == float(deal["price"]):
                continue

            conn.execute(
                "INSERT INTO price_history (appid, store, title, price, discount_pct, scraped_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (appid, store, deal["title"], deal["price"], deal.get("discount_pct", 0), _now()),
            )


def get_price_history(appid, store="Steam"):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT price, discount_pct, scraped_at FROM price_history "
            "WHERE appid = ? AND store = ? ORDER BY scraped_at ASC",
            (appid, store),
        ).fetchall()
        return [dict(r) for r in rows]


def add_watch(appid, store, title, target_price):
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO watchlist (appid, store, title, target_price, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (appid, store, title, target_price, _now()),
        )
        return cur.lastrowid


def remove_watch(watch_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM watchlist WHERE id = ?", (watch_id,))


def get_watches():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM watchlist ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]


def check_watch_alerts(current_deals):
    """
    Compare each watched item's target price against the current scrape.
    Marks alert_met_at the first time a target is hit, and returns the list
    of watch rows that are currently at/under target (so the UI or scraper
    log can surface them). Doesn't re-fire on every run once already met —
    that timestamp is what the "alert met" badge in the UI keys off.
    """
    by_key = {(d["appid"], d.get("store", "Steam")): d for d in current_deals}
    triggered = []

    with get_conn() as conn:
        watches = conn.execute("SELECT * FROM watchlist").fetchall()
        for w in watches:
            deal = by_key.get((w["appid"], w["store"]))
            if not deal:
                continue
            if deal["price"] <= w["target_price"]:
                if not w["alert_met_at"]:
                    conn.execute(
                        "UPDATE watchlist SET alert_met_at = ? WHERE id = ?",
                        (_now(), w["id"]),
                    )
                triggered.append({
                    "id": w["id"],
                    "title": w["title"],
                    "target_price": w["target_price"],
                    "current_price": deal["price"],
                })
    return triggered


if __name__ == "__main__":
    init_db()
    print(f"Initialized database at {DB_PATH}")
