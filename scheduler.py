"""
scheduler.py
------------
Runs scraper.py (Steam) + cheapshark.py on a repeating interval, for
deployments where you want a long-running process to keep data fresh
instead of triggering scrapes externally (e.g. via the GitHub Actions
workflow in .github/workflows/scrape.yml).

Usage:
    python scheduler.py                  # runs forever, scrapes every REFRESH_MINUTES
    REFRESH_MINUTES=15 python scheduler.py

This is intentionally simple — one job, one interval. For anything more
elaborate (different intervals per source, retries, alerting on repeated
failures) swap in a real task queue (Celery, RQ) instead.
"""

import os
import subprocess
import sys
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler

REFRESH_MINUTES = int(os.environ.get("REFRESH_MINUTES", "60"))
PROJECT_DIR = Path(__file__).parent


def run_scrape():
    print(f"[scheduler] Running scrape (every {REFRESH_MINUTES} min)...", flush=True)
    result = subprocess.run(
        [sys.executable, "scraper.py"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    print(result.stdout, flush=True)
    if result.returncode != 0:
        print(f"[scheduler] scraper.py exited with {result.returncode}:\n{result.stderr}", flush=True)


if __name__ == "__main__":
    run_scrape()  # run once immediately, then on the schedule

    scheduler = BlockingScheduler()
    scheduler.add_job(run_scrape, "interval", minutes=REFRESH_MINUTES)
    print(f"[scheduler] Started. Scraping every {REFRESH_MINUTES} minutes. Ctrl+C to stop.", flush=True)
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("[scheduler] Stopped.")
