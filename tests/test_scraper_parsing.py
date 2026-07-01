import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import scraper  # noqa: E402
import cheapshark  # noqa: E402


# ---------- scraper._parse_price ----------

@pytest.mark.parametrize("raw,expected", [
    ("$9.99", 9.99),
    ("$59.99", 59.99),
    ("Free", 0.0),
    ("Free To Play", 0.0),
    ("", None),
    (None, None),
    ("not a price", None),
])
def test_parse_price(raw, expected):
    assert scraper._parse_price(raw) == expected


# ---------- scraper.load_deals fallback behavior ----------

def test_load_deals_falls_back_to_sample(tmp_path, monkeypatch):
    fake_output = tmp_path / "deals.json"          # deliberately does not exist
    fake_fallback = tmp_path / "sample_deals.json"
    fake_fallback.write_text(json.dumps([
        {"appid": "1", "title": "Sample Game", "genre": "RPG", "price": 5, "original_price": 10,
         "discount_pct": 50, "url": "https://example.com"}
    ]))

    monkeypatch.setattr(scraper, "OUTPUT_FILE", fake_output)
    monkeypatch.setattr(scraper, "FALLBACK_FILE", fake_fallback)

    deals = scraper.load_deals()
    assert len(deals) == 1
    assert deals[0]["title"] == "Sample Game"
    assert deals[0]["store"] == "Steam"  # default injected by load_deals


def test_load_deals_prefers_fresh_output(tmp_path, monkeypatch):
    fake_output = tmp_path / "deals.json"
    fake_fallback = tmp_path / "sample_deals.json"
    fake_output.write_text(json.dumps([{"appid": "1", "title": "Fresh Game", "genre": "RPG",
                                         "price": 1, "original_price": 2, "discount_pct": 50,
                                         "url": "https://example.com", "store": "Steam"}]))
    fake_fallback.write_text(json.dumps([{"appid": "2", "title": "Stale Sample", "genre": "RPG",
                                           "price": 1, "original_price": 2, "discount_pct": 50,
                                           "url": "https://example.com", "store": "Steam"}]))

    monkeypatch.setattr(scraper, "OUTPUT_FILE", fake_output)
    monkeypatch.setattr(scraper, "FALLBACK_FILE", fake_fallback)

    deals = scraper.load_deals()
    assert deals[0]["title"] == "Fresh Game"


# ---------- cheapshark genre guessing ----------

@pytest.mark.parametrize("title,expected_genre", [
    ("Cyberpunk 2077", "RPG"),
    ("The Witcher 3: Wild Hunt - GOTY", "RPG"),
    ("Rocket League", "Sports"),
    ("Some Totally Unknown Indie Thing", "Other"),
])
def test_guess_genre(title, expected_genre):
    assert cheapshark._guess_genre(title) == expected_genre


def test_cheapshark_load_deals_fallback(tmp_path, monkeypatch):
    fake_output = tmp_path / "cheapshark_deals.json"
    fake_fallback = tmp_path / "sample_cheapshark_deals.json"
    fake_fallback.write_text(json.dumps([
        {"appid": "cs-1", "title": "Sample Cross Store Game", "genre": "Other", "store": "GOG",
         "original_price": 20, "price": 10, "discount_pct": 50, "url": "https://example.com"}
    ]))

    monkeypatch.setattr(cheapshark, "OUTPUT_FILE", fake_output)
    monkeypatch.setattr(cheapshark, "FALLBACK_FILE", fake_fallback)

    deals = cheapshark.load_deals()
    assert len(deals) == 1
    assert deals[0]["store"] == "GOG"
