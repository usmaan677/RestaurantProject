from datetime import datetime

from fake_database import use_fake_connection
import auth
import notifications


# ---------- add_notification ----------

def test_add_notification_saves_user_id_and_message(monkeypatch):
    connection = use_fake_connection(monkeypatch)
    monkeypatch.setattr(auth, "get_user_by_email", lambda email: {"id": 3, "email": email})

    note = notifications.add_notification("A@Test.com", "hello")

    query, params = connection.queries[0]
    assert "INSERT INTO notifications" in query
    assert params == (3, "hello")
    assert note == {"id": 7, "email": "a@test.com", "message": "hello", "status": "sent"}


def test_add_notification_skips_unregistered_user(monkeypatch):
    connection = use_fake_connection(monkeypatch)
    monkeypatch.setattr(auth, "get_user_by_email", lambda email: None)

    assert notifications.add_notification("nobody@test.com", "hello") is None
    assert connection.queries == []


# ---------- get_notifications ----------

def test_get_notifications_formats_rows(monkeypatch):
    connection = use_fake_connection(monkeypatch, rows=[{
        "id": 1,
        "email": "a@test.com",
        "message": "hello",
        "created_at": datetime(2026, 11, 6, 14, 30),
        "status": "sent",
    }])

    assert notifications.get_notifications("A@Test.com") == [{
        "id": 1,
        "email": "a@test.com",
        "message": "hello",
        "time": "Nov 06, 02:30 PM",
        "status": "sent",
    }]
    assert connection.queries[0][1] == ("a@test.com",)


# ---------- mark_notifications_viewed ----------

def test_mark_notifications_viewed_updates_that_user(monkeypatch):
    connection = use_fake_connection(monkeypatch)

    notifications.mark_notifications_viewed("A@Test.com")

    query, params = connection.queries[0]
    assert "SET status = 'viewed'" in query
    assert params == ("a@test.com",)
