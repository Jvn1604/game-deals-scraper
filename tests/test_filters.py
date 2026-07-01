import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import apply_filters, get_genres, get_stores  # noqa: E402

SAMPLE = [
    {"appid": "1", "title": "Alpha Quest", "genre": "RPG", "store": "Steam", "price": 10.0, "original_price": 20.0, "discount_pct": 50},
    {"appid": "2", "title": "Beta Racer", "genre": "Racing", "store": "GOG", "price": 5.0, "original_price": 25.0, "discount_pct": 80},
    {"appid": "3", "title": "Gamma Strike", "genre": "Action", "store": "Steam", "price": 30.0, "original_price": 30.0, "discount_pct": 0},
    {"appid": "4", "title": "Delta Quest II", "genre": "RPG", "store": "Epic Games Store", "price": 15.0, "original_price": 30.0, "discount_pct": 50},
]


def test_genre_filter():
    result = apply_filters(SAMPLE, "RPG", "all", None, False, "", "discount_desc")
    assert {d["appid"] for d in result} == {"1", "4"}


def test_store_filter():
    result = apply_filters(SAMPLE, "all", "GOG", None, False, "", "discount_desc")
    assert [d["appid"] for d in result] == ["2"]


def test_max_price_filter():
    result = apply_filters(SAMPLE, "all", "all", 10, False, "", "discount_desc")
    assert {d["appid"] for d in result} == {"1", "2"}


def test_best_only_filter():
    result = apply_filters(SAMPLE, "all", "all", None, True, "", "discount_desc")
    # threshold is enforced in app.py's route, apply_filters just checks the flag
    # against whatever discount_pct is on each record, so anything >= 60 here
    assert {d["appid"] for d in result} == {"2"}


def test_search_is_case_insensitive_substring():
    result = apply_filters(SAMPLE, "all", "all", None, False, "quest", "discount_desc")
    assert {d["appid"] for d in result} == {"1", "4"}


def test_search_no_match_returns_empty():
    result = apply_filters(SAMPLE, "all", "all", None, False, "nonexistent title", "discount_desc")
    assert result == []


def test_sort_price_asc():
    result = apply_filters(SAMPLE, "all", "all", None, False, "", "price_asc")
    assert [d["appid"] for d in result] == ["2", "1", "4", "3"]


def test_sort_price_desc():
    result = apply_filters(SAMPLE, "all", "all", None, False, "", "price_desc")
    assert [d["appid"] for d in result] == ["3", "4", "1", "2"]


def test_sort_alpha():
    result = apply_filters(SAMPLE, "all", "all", None, False, "", "alpha")
    titles = [d["title"] for d in result]
    assert titles == sorted(titles, key=str.lower)


def test_sort_discount_desc_default():
    result = apply_filters(SAMPLE, "all", "all", None, False, "", "discount_desc")
    discounts = [d["discount_pct"] for d in result]
    assert discounts == sorted(discounts, reverse=True)


def test_combined_filters():
    result = apply_filters(SAMPLE, "RPG", "Steam", 20, False, "alpha", "alpha")
    assert [d["appid"] for d in result] == ["1"]


def test_get_genres_deduped_and_sorted():
    assert get_genres(SAMPLE) == ["Action", "RPG", "Racing"]


def test_get_stores_deduped_and_sorted():
    assert get_stores(SAMPLE) == ["Epic Games Store", "GOG", "Steam"]
