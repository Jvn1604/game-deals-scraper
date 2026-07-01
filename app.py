"""
app.py
------
Flask dashboard: search, filters (genre/store/price), sort, pagination,
best-deal highlighting, a watchlist with price-target alerts, and a
per-game price history endpoint.

Run:
    python app.py
Then open http://127.0.0.1:5000
"""

from flask import Flask, jsonify, render_template, request

import db
import scraper

app = Flask(__name__)
db.init_db()

# A deal counts as a "best deal" badge if its discount is this or higher
BEST_DEAL_THRESHOLD = 60

SORT_OPTIONS = {
    "discount_desc": lambda d: -d["discount_pct"],
    "price_asc": lambda d: d["price"],
    "price_desc": lambda d: -d["price"],
    "alpha": lambda d: d["title"].lower(),
}


def get_genres(deals):
    return sorted({d["genre"] for d in deals})


def get_stores(deals):
    return sorted({d.get("store", "Steam") for d in deals})


def apply_filters(deals, genre, store, max_price, best_only, search, sort_by):
    filtered = deals

    if genre and genre != "all":
        filtered = [d for d in filtered if d["genre"] == genre]
    if store and store != "all":
        filtered = [d for d in filtered if d.get("store", "Steam") == store]
    if max_price is not None:
        filtered = [d for d in filtered if d["price"] <= max_price]
    if best_only:
        filtered = [d for d in filtered if d["discount_pct"] >= BEST_DEAL_THRESHOLD]
    if search:
        needle = search.strip().lower()
        filtered = [d for d in filtered if needle in d["title"].lower()]

    key_fn = SORT_OPTIONS.get(sort_by, SORT_OPTIONS["discount_desc"])
    return sorted(filtered, key=key_fn)


@app.route("/")
def index():
    deals = scraper.load_all_deals()
    genres = get_genres(deals)
    stores = get_stores(deals)
    max_price_available = max((d["price"] for d in deals), default=100)
    return render_template(
        "index.html",
        genres=genres,
        stores=stores,
        max_price_available=int(max_price_available) + 1,
        best_deal_threshold=BEST_DEAL_THRESHOLD,
        total_deals=len(deals),
    )


@app.route("/api/deals")
def api_deals():
    """JSON endpoint the front-end fetches from when filters/search/sort change."""
    deals = scraper.load_all_deals()

    genre = request.args.get("genre", "all")
    store = request.args.get("store", "all")
    max_price_raw = request.args.get("max_price")
    best_only = request.args.get("best_only") == "1"
    search = request.args.get("q", "")
    sort_by = request.args.get("sort", "discount_desc")

    page = max(1, request.args.get("page", 1, type=int))
    per_page = max(1, min(60, request.args.get("per_page", 12, type=int)))

    max_price = None
    if max_price_raw not in (None, "", "all"):
        try:
            max_price = float(max_price_raw)
        except ValueError:
            max_price = None

    filtered = apply_filters(deals, genre, store, max_price, best_only, search, sort_by)

    total = len(filtered)
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = min(page, total_pages)
    start = (page - 1) * per_page
    page_items = filtered[start:start + per_page]

    for d in page_items:
        d["is_best_deal"] = d["discount_pct"] >= BEST_DEAL_THRESHOLD

    return jsonify({
        "results": page_items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    })


@app.route("/api/deals/<appid>/history")
def api_deal_history(appid):
    store = request.args.get("store", "Steam")
    history = db.get_price_history(appid, store)
    return jsonify(history)


@app.route("/api/watchlist", methods=["GET"])
def api_watchlist_list():
    deals = scraper.load_all_deals()
    by_key = {(d["appid"], d.get("store", "Steam")): d for d in deals}

    watches = db.get_watches()
    for w in watches:
        deal = by_key.get((w["appid"], w["store"]))
        w["current_price"] = deal["price"] if deal else None
        w["alert_met"] = w["current_price"] is not None and w["current_price"] <= w["target_price"]
    return jsonify(watches)


@app.route("/api/watchlist", methods=["POST"])
def api_watchlist_add():
    payload = request.get_json(silent=True) or {}
    appid = payload.get("appid")
    store = payload.get("store", "Steam")
    title = payload.get("title")
    target_price = payload.get("target_price")

    if not appid or not title or target_price is None:
        return jsonify({"error": "appid, title, and target_price are required"}), 400

    try:
        target_price = float(target_price)
    except (TypeError, ValueError):
        return jsonify({"error": "target_price must be a number"}), 400

    watch_id = db.add_watch(appid, store, title, target_price)
    return jsonify({"id": watch_id}), 201


@app.route("/api/watchlist/<int:watch_id>", methods=["DELETE"])
def api_watchlist_delete(watch_id):
    db.remove_watch(watch_id)
    return jsonify({"deleted": watch_id})


if __name__ == "__main__":
    app.run(debug=True)
