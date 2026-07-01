import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import db  # noqa: E402


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    test_db_path = tmp_path / "test_deals.db"
    monkeypatch.setattr(db, "DB_PATH", test_db_path)
    db.init_db()
    return test_db_path


def test_init_db_creates_tables(temp_db):
    with db.get_conn() as conn:
        tables = {row["name"] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )}
    assert "price_history" in tables
    assert "watchlist" in tables


def test_record_price_snapshot_inserts_new_price(temp_db):
    deals = [{"appid": "1", "store": "Steam", "title": "Test Game", "price": 9.99, "discount_pct": 50}]
    db.record_price_snapshot(deals)
    history = db.get_price_history("1", "Steam")
    assert len(history) == 1
    assert history[0]["price"] == 9.99


def test_record_price_snapshot_skips_unchanged_price(temp_db):
    deals = [{"appid": "1", "store": "Steam", "title": "Test Game", "price": 9.99, "discount_pct": 50}]
    db.record_price_snapshot(deals)
    db.record_price_snapshot(deals)  # same price again
    history = db.get_price_history("1", "Steam")
    assert len(history) == 1  # no duplicate row


def test_record_price_snapshot_adds_row_on_price_change(temp_db):
    db.record_price_snapshot([{"appid": "1", "store": "Steam", "title": "Test Game", "price": 9.99, "discount_pct": 50}])
    db.record_price_snapshot([{"appid": "1", "store": "Steam", "title": "Test Game", "price": 7.99, "discount_pct": 60}])
    history = db.get_price_history("1", "Steam")
    assert len(history) == 2
    assert [h["price"] for h in history] == [9.99, 7.99]


def test_add_and_remove_watch(temp_db):
    watch_id = db.add_watch("1", "Steam", "Test Game", 5.0)
    watches = db.get_watches()
    assert len(watches) == 1
    assert watches[0]["id"] == watch_id

    db.remove_watch(watch_id)
    assert db.get_watches() == []


def test_check_watch_alerts_triggers_when_price_at_or_below_target(temp_db):
    db.add_watch("1", "Steam", "Test Game", 10.0)
    current_deals = [{"appid": "1", "store": "Steam", "title": "Test Game", "price": 8.0, "discount_pct": 60}]

    triggered = db.check_watch_alerts(current_deals)
    assert len(triggered) == 1
    assert triggered[0]["current_price"] == 8.0

    # alert_met_at should now be set
    watches = db.get_watches()
    assert watches[0]["alert_met_at"] is not None


def test_check_watch_alerts_does_not_trigger_above_target(temp_db):
    db.add_watch("1", "Steam", "Test Game", 5.0)
    current_deals = [{"appid": "1", "store": "Steam", "title": "Test Game", "price": 8.0, "discount_pct": 20}]

    triggered = db.check_watch_alerts(current_deals)
    assert triggered == []
