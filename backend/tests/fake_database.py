from contextlib import contextmanager

import database
import history
import notifications
import queues


# ---------- Fake queue entries (a plain list instead of MySQL) ----------

def use_fake_queue_entries(monkeypatch):
    fake_entries = []  # only people still waiting, like the real table query
    ids_used = []

    def get_queue_for_service(service_id):
        entries = [entry for entry in fake_entries if entry["service_id"] == service_id]
        return sorted(entries, key=lambda entry: (-entry["priority"], entry["id"]))

    def get_entries_for_email(email):
        return [entry for entry in fake_entries if entry["email"] == email.lower()]

    def add_queue_entry(service_id, email, priority):
        ids_used.append(None)
        entry = {
            "id": len(ids_used),  # ids keep counting up even after people leave
            "service_id": service_id,
            "email": email.lower(),
            "priority": priority,
        }
        fake_entries.append(entry)
        return entry

    def finish_queue_entry(service_id, new_status, email=None):
        waiting = get_queue_for_service(service_id)
        if email is not None:
            waiting = [entry for entry in waiting if entry["email"] == email.lower()]
        if not waiting:
            return None

        fake_entries.remove(waiting[0])
        return waiting[0]

    monkeypatch.setattr(queues, "get_queue_for_service", get_queue_for_service)
    monkeypatch.setattr(queues, "get_entries_for_email", get_entries_for_email)
    monkeypatch.setattr(queues, "add_queue_entry", add_queue_entry)
    monkeypatch.setattr(queues, "finish_queue_entry", finish_queue_entry)
    return fake_entries


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
