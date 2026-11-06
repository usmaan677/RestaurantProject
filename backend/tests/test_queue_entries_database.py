from contextlib import contextmanager

import pymysql
import pytest
from fastapi import HTTPException

import auth
import database
import queues


# ---------- Fake connection that hands back one prepared result per query ----------

class ScriptedCursor:
    def __init__(self, connection):
        self.connection = connection
        self.current = []
        self.lastrowid = 11

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def execute(self, query, params=()):
        self.connection.queries.append((" ".join(query.split()), params))
        self.current = self.connection.results.pop(0) if self.connection.results else []

    def fetchall(self):
        return self.current

    def fetchone(self):
        return self.current[0] if self.current else None


class ScriptedConnection:
    def __init__(self, results):
        self.queries = []
        self.results = list(results)

    def cursor(self):
        return ScriptedCursor(self)


def use_scripted_connection(monkeypatch, results=()):
    connection = ScriptedConnection(results)

    @contextmanager
    def connection_scope():
        yield connection

    monkeypatch.setattr(database, "connection_scope", connection_scope)
    return connection


def entry(entry_id=1, email="a@test.com", priority=3):
    return {"id": entry_id, "service_id": 4, "email": email, "priority": priority}


# ---------- reading the line ----------

def test_get_queue_for_service_reads_waiting_entries_in_serving_order(monkeypatch):
    connection = use_scripted_connection(monkeypatch, [[entry(1), entry(2, "b@test.com")]])

    assert queues.get_queue_for_service(4) == [entry(1), entry(2, "b@test.com")]

    query, params = connection.queries[0]
    assert "FROM queue_entries" in query
    assert "queue_entries.status = 'waiting'" in query
    assert "ORDER BY queue_entries.priority DESC, queue_entries.id" in query
    assert params == (4,)


def test_get_entries_for_email_lowercases_the_email(monkeypatch):
    connection = use_scripted_connection(monkeypatch, [[entry(1)]])

    assert queues.get_entries_for_email("A@Test.com") == [entry(1)]
    assert connection.queries[0][1] == ("a@test.com",)


def test_position_and_status_come_from_the_database_order(monkeypatch):
    monkeypatch.setattr(
        queues, "get_queue_for_service",
        lambda service_id: [entry(1, "first@test.com", 5), entry(2, "a@test.com", 3)],
    )
    monkeypatch.setattr(queues, "calculate_wait", lambda service_id, position: position * 10)

    assert queues.get_position(4, "A@Test.com") == 2
    assert queues.is_user_in_queue(4, "a@test.com") is True
    assert queues.is_user_in_queue(4, "nobody@test.com") is False
    assert queues.build_status(4, "a@test.com") == {
        "id": 2,
        "service_id": 4,
        "email": "a@test.com",
        "priority": 3,
        "position": 2,
        "estimated_wait": 20,
    }
    assert queues.build_status(4, "nobody@test.com") is None


# ---------- joining ----------

def test_add_queue_entry_inserts_row_and_renumbers(monkeypatch):
    connection = use_scripted_connection(monkeypatch, [
        [{"id": 9, "status": "open"}, {"id": 5, "status": "closed"}],  # lock the queues
        [{"waiting": 2}],                                               # how many are waiting
    ])
    monkeypatch.setattr(auth, "get_user_by_email", lambda email: {"id": 3, "email": email})

    result = queues.add_queue_entry(4, "A@Test.com", 5)

    assert result == {"id": 11, "service_id": 4, "email": "a@test.com", "priority": 5}
    lock, count, insert, renumber = connection.queries
    assert "FOR UPDATE" in lock[0] and lock[1] == (4,)
    assert "COUNT(*)" in count[0]
    assert "INSERT INTO queue_entries" in insert[0]
    assert insert[1] == (9, 3, 3, 5)  # open queue 9, user 3, position 3, priority 5
    assert "ROW_NUMBER()" in renumber[0] and renumber[1] == (4,)


def test_add_queue_entry_uses_the_open_queue_not_a_closed_one(monkeypatch):
    connection = use_scripted_connection(monkeypatch, [
        [{"id": 9, "status": "closed"}, {"id": 5, "status": "open"}],
        [{"waiting": 0}],
    ])
    monkeypatch.setattr(auth, "get_user_by_email", lambda email: {"id": 3, "email": email})

    queues.add_queue_entry(4, "a@test.com", 1)

    assert connection.queries[2][1][0] == 5


def test_add_queue_entry_rejects_unregistered_user(monkeypatch):
    connection = use_scripted_connection(monkeypatch)
    monkeypatch.setattr(auth, "get_user_by_email", lambda email: None)

    with pytest.raises(HTTPException) as error:
        queues.add_queue_entry(4, "nobody@test.com", 1)

    assert error.value.status_code == 404
    assert error.value.detail == "User not found"
    assert connection.queries == []


def test_add_queue_entry_rejects_closed_queue(monkeypatch):
    connection = use_scripted_connection(monkeypatch, [[{"id": 9, "status": "closed"}]])
    monkeypatch.setattr(auth, "get_user_by_email", lambda email: {"id": 3, "email": email})

    with pytest.raises(HTTPException) as error:
        queues.add_queue_entry(4, "a@test.com", 1)

    assert error.value.status_code == 409
    assert len(connection.queries) == 1  # nothing was inserted


def test_add_queue_entry_rejects_service_with_no_queue(monkeypatch):
    use_scripted_connection(monkeypatch, [[]])
    monkeypatch.setattr(auth, "get_user_by_email", lambda email: {"id": 3, "email": email})

    with pytest.raises(HTTPException) as error:
        queues.add_queue_entry(4, "a@test.com", 1)

    assert error.value.status_code == 409


def test_add_queue_entry_turns_duplicate_waiting_row_into_400(monkeypatch):
    use_scripted_connection(monkeypatch, [[{"id": 9, "status": "open"}], [{"waiting": 0}]])
    monkeypatch.setattr(auth, "get_user_by_email", lambda email: {"id": 3, "email": email})

    def refuse_duplicate(self, query, params=()):
        if query.lstrip().startswith("INSERT"):
            raise pymysql.err.IntegrityError(1062, "Duplicate entry")
        self.current = self.connection.results.pop(0) if self.connection.results else []

    monkeypatch.setattr(ScriptedCursor, "execute", refuse_duplicate)

    with pytest.raises(HTTPException) as error:
        queues.add_queue_entry(4, "a@test.com", 1)

    assert error.value.status_code == 400
    assert error.value.detail == "User already in queue for this service"


def test_add_queue_entry_does_not_hide_other_database_errors(monkeypatch):
    use_scripted_connection(monkeypatch, [[{"id": 9, "status": "open"}], [{"waiting": 0}]])
    monkeypatch.setattr(auth, "get_user_by_email", lambda email: {"id": 3, "email": email})

    def refuse_foreign_key(self, query, params=()):
        if query.lstrip().startswith("INSERT"):
            raise pymysql.err.IntegrityError(1452, "foreign key fails")
        self.current = self.connection.results.pop(0) if self.connection.results else []

    monkeypatch.setattr(ScriptedCursor, "execute", refuse_foreign_key)

    with pytest.raises(pymysql.err.IntegrityError):
        queues.add_queue_entry(4, "a@test.com", 1)


# ---------- leaving and being served ----------

def test_leave_queue_marks_the_entry_canceled_and_renumbers(monkeypatch):
    connection = use_scripted_connection(monkeypatch, [[], [entry(7)]])
    monkeypatch.setattr(queues, "notify_close_users", lambda service_id: None)

    result = queues.leave_queue(queues.QueueLeave(email="A@Test.com", service_id=4))

    assert result == entry(7)
    lock, find, update, renumber = connection.queries
    assert "FOR UPDATE" in lock[0]
    assert "user_credentials.email = %s" in find[0] and find[1] == (4, "a@test.com")
    assert update[0] == "UPDATE queue_entries SET status = %s WHERE id = %s"
    assert update[1] == ("canceled", 7)
    assert "ROW_NUMBER()" in renumber[0]


def test_leave_queue_when_not_waiting_changes_nothing(monkeypatch):
    connection = use_scripted_connection(monkeypatch, [[], []])
    notified = []
    monkeypatch.setattr(queues, "notify_close_users", lambda service_id: notified.append(service_id))

    assert queues.leave_queue(queues.QueueLeave(email="a@test.com", service_id=4)) is None
    assert len(connection.queries) == 2  # lock and look-up only
    assert notified == []


def test_serve_next_marks_the_first_in_line_served(monkeypatch):
    connection = use_scripted_connection(monkeypatch, [[], [entry(3, "first@test.com", 5)]])

    assert queues.serve_next(4) == entry(3, "first@test.com", 5)

    find, update = connection.queries[1], connection.queries[2]
    assert "user_credentials.email" not in find[0].split("WHERE")[1]
    assert "ORDER BY queue_entries.priority DESC, queue_entries.id LIMIT 1" in find[0]
    assert update[1] == ("served", 3)


def test_serve_next_on_empty_queue_returns_none(monkeypatch):
    connection = use_scripted_connection(monkeypatch, [[], []])

    assert queues.serve_next(4) is None
    assert len(connection.queries) == 2


def test_get_queue_count_counts_waiting_entries(monkeypatch):
    use_scripted_connection(monkeypatch, [[entry(1), entry(2)]])

    assert queues.get_queue_count(4) == 2
