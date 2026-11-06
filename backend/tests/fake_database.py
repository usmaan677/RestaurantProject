from contextlib import contextmanager

import database
import history
import notifications


# ---------- Fake notifications (a plain list instead of MySQL) ----------

def use_fake_notifications(monkeypatch):
    fake_notifications = []

    def add_notification(email, message):
        note = {
            "id": len(fake_notifications) + 1,
            "email": email.lower(),
            "message": message,
            "time": "Nov 06, 12:00 PM",
            "status": "sent",
        }
        fake_notifications.append(note)
        return note

    def get_notifications(email):
        return [note for note in fake_notifications if note["email"] == email.lower()]

    def mark_notifications_viewed(email):
        for note in get_notifications(email):
            note["status"] = "viewed"

    monkeypatch.setattr(notifications, "add_notification", add_notification)
    monkeypatch.setattr(notifications, "get_notifications", get_notifications)
    monkeypatch.setattr(notifications, "mark_notifications_viewed", mark_notifications_viewed)


# ---------- Fake history (a plain list instead of MySQL) ----------

def use_fake_history(monkeypatch):
    fake_history = []

    def add_history_entry(email, service_id, service_name, outcome):
        entry = {
            "id": len(fake_history) + 1,
            "email": email.lower(),
            "service_id": service_id,
            "service_name": service_name,
            "date": "2026-11-06",
            "outcome": outcome,
        }
        fake_history.append(entry)
        return entry

    def get_history_for_email(email):
        entries = [entry for entry in fake_history if entry["email"] == email.lower()]
        return list(reversed(entries))

    monkeypatch.setattr(history, "add_history_entry", add_history_entry)
    monkeypatch.setattr(history, "get_history_for_email", get_history_for_email)


# ---------- Fake connection (records the SQL instead of running it) ----------

class FakeCursor:
    def __init__(self, connection):
        self.connection = connection
        self.lastrowid = 7

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def execute(self, query, params):
        self.connection.queries.append((query, params))

    def fetchall(self):
        return self.connection.rows


class FakeConnection:
    def __init__(self, rows):
        self.queries = []
        self.rows = rows

    def cursor(self):
        return FakeCursor(self)


def use_fake_connection(monkeypatch, rows=()):
    connection = FakeConnection(list(rows))

    @contextmanager
    def connection_scope():
        yield connection

    monkeypatch.setattr(database, "connection_scope", connection_scope)
    return connection
