# Game Deals Scraper

A Python/BeautifulSoup scraper pulls currently discounted games from Steam
and CheapShark (cross-store: GOG, Epic, Humble, Fanatical, etc.), and a
Flask dashboard displays them with search, filters, sorting, price-history
sparklines, and a price-target watchlist.

## Stack
- **Scraping:** `requests` + `BeautifulSoup4` (Steam), CheapShark REST API (cross-store)
- **Storage:** JSON snapshots for "what's on sale now" + SQLite for price history and the watchlist
- **Backend:** Flask (`/api/deals`, `/api/deals/<appid>/history`, `/api/watchlist`)
- **Frontend:** plain HTML/CSS/JS, no build step, dark mode, responsive down to mobile
- **Tests:** pytest (34 tests — filtering/sorting/search, DB layer, scraper parsing)
- **Deploy:** Dockerfile + docker-compose, Render config, Procfile, GitHub Actions

## Project structure
```
game-deals-scraper/
├── app.py                      # Flask routes: deals, history, watchlist
├── scraper.py                  # Steam scraper (BeautifulSoup) + merges CheapShark
├── cheapshark.py                # CheapShark API client (cross-store deals)
├── db.py                        # SQLite: price_history + watchlist tables
├── scheduler.py                  # APScheduler loop for long-running deployments
├── requirements.txt
├── Dockerfile / docker-compose.yml
├── render.yaml                   # Render.com one-click deploy config
├── Procfile                      # Railway/Heroku-style deploy target
├── .github/workflows/
│   ├── ci.yml                    # runs pytest on every push/PR
│   └── scrape.yml                # scheduled scrape, commits refreshed data
├── tests/
│   ├── test_filters.py
│   ├── test_db.py
│   └── test_scraper_parsing.py
├── data/
│   ├── deals.json                 # Steam scrape output (git-ignored)
│   ├── cheapshark_deals.json       # CheapShark output (git-ignored)
│   ├── deals.db                    # SQLite: history + watchlist (git-ignored)
│   ├── sample_deals.json           # fallback Steam data
│   └── sample_cheapshark_deals.json # fallback cross-store data
├── templates/index.html
└── static/{style.css, script.js}
```

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python db.py                    # creates data/deals.db
```

## 1. Scrape the deals (optional)

```bash
python scraper.py
```

Scrapes Steam's specials page once per genre tag, fetches CheapShark's
cross-store deals, writes `data/deals.json` + `data/cheapshark_deals.json`,
records a price-history snapshot, and checks the watchlist for triggered
alerts (printed to stdout).

If you skip this, or a source is unreachable / changes its layout, the app
falls back to the bundled sample data automatically, so it always runs.

**Keeping it fresh automatically**, three options:
- `python scheduler.py` — long-running process, re-scrapes every 60 min (`REFRESH_MINUTES` env var to change)
- `docker-compose up` — runs the web app + a scraper container together (see below)
- `.github/workflows/scrape.yml` — scrapes every 6 hours on GitHub's infra and commits fresh data back to the repo; no server required

## 2. Run the dashboard

```bash
python app.py
```

Open **http://127.0.0.1:5000**.

## Features

- **Search** — live-filtered by title as you type
- **Filters** — genre, store, max price (slider), best-deals-only toggle
- **Sort** — biggest discount, price low/high, title A–Z
- **Pagination** — 12 per page
- **Best deal badges** — any item ≥60% off gets a red sticker (`BEST_DEAL_THRESHOLD` in `app.py`)
- **Price history** — click the history icon on a card for a sparkline built from SQLite snapshots
- **Watchlist** — set a target price on any game; the Watchlist tab shows current price vs. target and flags when it's been hit
- **Share** — copy a deal's store link to clipboard
- **Dark mode** — toggle in the header, persisted via `localStorage`, respects system preference by default
- **Responsive** — grid collapses to 2 columns then 1 on phones; filter bar stacks vertically

## Running tests

```bash
python -m pytest tests/ -v
```

34 tests covering filter/sort/search logic, the SQLite layer (history +
watchlist alerts), price parsing, and fallback-data behavior.

## Deployment

**Docker (self-hosted):**
```bash
docker-compose up --build
```
Runs the web app plus a `scheduler.py`-driven scraper container, both
sharing a persistent volume for `data/`. Comment out the `scraper` service
in `docker-compose.yml` if you'd rather rely on the GitHub Actions workflow
instead.

**Render.com:** connect the repo — `render.yaml` is already configured
(free tier, persistent disk for `data/`, gunicorn entrypoint).

**Railway/Heroku-style platforms:** `Procfile` is included; set the
`PORT` env var per platform convention if it isn't set automatically.

> Note: the Dockerfile and gunicorn entrypoint were verified to run
> correctly in development, but the actual container build wasn't run
> end-to-end in this environment (no Docker available here) — worth a
> `docker-compose up --build` sanity check before you deploy.

## Extending it further

- Real email/push notifications for watchlist alerts (currently logged to
  stdout during a scrape run) — wire `db.check_watch_alerts()`'s return
  value into `smtplib` or a webhook
- More stores: add tag IDs to `GENRE_TAGS` in `scraper.py`, or extend
  `cheapshark.py`'s store filter
- Swap SQLite for Postgres if the dataset/traffic grows — `db.py` is the
  only file that would need to change
- Charting library (Chart.js) instead of the hand-rolled SVG sparkline, if
  you want tooltips/zoom on price history

## Notes

- Steam's HTML structure can change without notice; if `scraper.py`
  returns 0 Steam results, check the CSS selectors in `_scrape_genre()`
  first.
- Be a good citizen: `REQUEST_DELAY` in `scraper.py` throttles requests
  between genre pages — don't drop it if you add more genres.
- CheapShark genre labels are a best-effort keyword match (`cheapshark.py`
  `_guess_genre()`), not authoritative — unmatched titles fall under "Other".
