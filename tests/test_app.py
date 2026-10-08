import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from app import app  # noqa: E402


def test_health():
    client = app.test_client()
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_search_returns_results():
    client = app.test_client()
    resp = client.get("/search?q=welcome")
    assert resp.status_code == 200
    assert len(resp.get_json()["results"]) == 1
