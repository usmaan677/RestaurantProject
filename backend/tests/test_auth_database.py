from contextlib import contextmanager

import auth


# ---------- Fake connection (records the SQL instead of running it) ----------

class FakeCursor:
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def execute(self, query, params):
        self.connection.queries.append((query, params))

    def fetchone(self):
        return self.connection.row


class FakeConnection:
    def __init__(self, row=None):
        self.queries = []
        self.row = row

    def cursor(self):
        return FakeCursor(self)


def use_fake_connection(monkeypatch, row=None):
    connection = FakeConnection(row)

    @contextmanager
    def connection_scope():
        yield connection

    monkeypatch.setattr(auth.database, "connection_scope", connection_scope)
    return connection


# ---------- get_user_by_email ----------

def test_get_user_by_email_returns_row(monkeypatch):
    row = {"id": 1, "email": "a@test.com", "role": "user", "full_name": "A Test"}
    connection = use_fake_connection(monkeypatch, row)

    assert auth.get_user_by_email("a@test.com") == row

    query, params = connection.queries[0]
    assert "FROM user_credentials" in query
    assert params == ("a@test.com",)


def test_get_user_by_email_returns_none_when_missing(monkeypatch):
    use_fake_connection(monkeypatch, row=None)

    assert auth.get_user_by_email("nobody@test.com") is None


# ---------- add_user ----------

def test_add_user_saves_credentials_and_profile(monkeypatch):
    connection = use_fake_connection(monkeypatch)
    user = {
        "email": "a@test.com",
        "password_hash": "hashed",
        "role": "user",
        "full_name": "A Test",
    }

    assert auth.add_user(user) == user

    credentials_query, credentials_params = connection.queries[0]
    profile_query, profile_params = connection.queries[1]

    assert "INSERT INTO user_credentials" in credentials_query
    assert credentials_params == ("a@test.com", "hashed", "user")
    assert "INSERT INTO user_profiles" in profile_query
    assert profile_params == ("a@test.com", "A Test")
