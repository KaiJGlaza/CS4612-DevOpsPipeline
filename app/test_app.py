"""Tests for app.py. Run them with: pytest"""

from app import app


def test_home_page_works():
    client = app.test_client()
    assert client.get("/").status_code == 200


def test_health_check_says_ok():
    client = app.test_client()
    assert client.get("/health").get_json() == {"status": "ok"}
