from datetime import datetime

from fake_database import use_fake_connection
import auth
import history


# ---------- add_history_entry ----------

def test_add_history_entry_saves_user_id_and_service(monkeypatch):
    connection = use_fake_connection(monkeypatch)
    monkeypatch.setattr(auth, "get_user_by_email", lambda email: {"id": 3, "email": email})

    entry = history.add_history_entry("A@Test.com", 2, "Takeout", "Served")

    query, params = connection.queries[0]
    assert "INSERT INTO queue_history" in query
    assert params == (3, 2, "Takeout", "Served")
    assert entry["id"] == 7
    assert entry["email"] == "a@test.com"


def test_add_history_entry_skips_unregistered_user(monkeypatch):
    connection = use_fake_connection(monkeypatch)
    monkeypatch.setattr(auth, "get_user_by_email", lambda email: None)

    assert history.add_history_entry("nobody@test.com", 2, "Takeout", "Served") is None
    assert connection.queries == []


# ---------- get_history_for_email ----------

def test_get_history_formats_rows(monkeypatch):
    connection = use_fake_connection(monkeypatch, rows=[{
        "id": 1,
        "email": "a@test.com",
        "service_id": 2,
        "service_name": "Takeout",
        "created_at": datetime(2026, 11, 6, 14, 30),
        "outcome": "Served",
    }])

    assert history.get_history_for_email("A@Test.com") == [{
        "id": 1,
        "email": "a@test.com",
        "service_id": 2,
        "service_name": "Takeout",
        "date": "2026-11-06",
        "time": "02:30 PM",
        "outcome": "Served",
    }]
    assert connection.queries[0][1] == ("a@test.com",)
