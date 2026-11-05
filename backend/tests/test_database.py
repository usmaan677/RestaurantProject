import pytest

import database


def set_database_environment(monkeypatch):
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "3307")
    monkeypatch.setenv("DB_NAME", "queuesmart_test")
    monkeypatch.setenv("DB_USER", "queuesmart_test")
    monkeypatch.setenv("DB_PASSWORD", "test-password")


def test_database_settings_read_environment(monkeypatch):
    set_database_environment(monkeypatch)

    settings = database.DatabaseSettings.from_env()

    assert settings.host == "localhost"
    assert settings.port == 3307
    assert settings.name == "queuesmart_test"
    assert settings.user == "queuesmart_test"
    assert settings.password == "test-password"


def test_database_settings_reject_missing_values(monkeypatch):
    for key in ("DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"):
        monkeypatch.delenv(key, raising=False)

    with pytest.raises(RuntimeError, match="DB_HOST"):
        database.DatabaseSettings.from_env()


@pytest.mark.parametrize("port", ["invalid", "0", "65536"])
def test_database_settings_reject_invalid_port(monkeypatch, port):
    set_database_environment(monkeypatch)
    monkeypatch.setenv("DB_PORT", port)

    with pytest.raises(ValueError, match="DB_PORT"):
        database.DatabaseSettings.from_env()


def test_connection_scope_commits_and_closes(monkeypatch):
    set_database_environment(monkeypatch)
    calls = []

    class FakeConnection:
        def commit(self):
            calls.append("commit")

        def rollback(self):
            calls.append("rollback")

        def close(self):
            calls.append("close")

    connection = FakeConnection()
    monkeypatch.setattr(database.pymysql, "connect", lambda **kwargs: connection)

    with database.connection_scope() as active_connection:
        assert active_connection is connection

    assert calls == ["commit", "close"]


def test_connection_scope_rolls_back_and_closes_on_error(monkeypatch):
    set_database_environment(monkeypatch)
    calls = []

    class FakeConnection:
        def commit(self):
            calls.append("commit")

        def rollback(self):
            calls.append("rollback")

        def close(self):
            calls.append("close")

    monkeypatch.setattr(database.pymysql, "connect", lambda **kwargs: FakeConnection())

    with pytest.raises(RuntimeError, match="query failed"):
        with database.connection_scope():
            raise RuntimeError("query failed")

    assert calls == ["rollback", "close"]
