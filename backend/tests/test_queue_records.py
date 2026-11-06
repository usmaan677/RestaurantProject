from contextlib import contextmanager

from fastapi.testclient import TestClient

import queues
from main import app

client = TestClient(app)


class FakeCursor:
    def __init__(self, connection):
        self.connection = connection
        self.result = None
        self.lastrowid = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def execute(self, query, params=()):
        normalized_query = " ".join(query.split())
        self.connection.queries.append((normalized_query, params))

        if normalized_query.startswith("SELECT id FROM services"):
            service_id = params[0]
            self.result = (
                {"id": service_id}
                if service_id in self.connection.service_ids
                else None
            )
        elif normalized_query.startswith("SELECT id, service_id, status, created_at"):
            if "WHERE service_id = %s" in normalized_query:
                service_id = params[0]
                matching_queues = [
                    queue
                    for queue in self.connection.queues
                    if queue["service_id"] == service_id
                    and queue["status"] == "open"
                ]
                self.result = max(matching_queues, key=lambda queue: queue["id"], default=None)
            else:
                queue_id = params[0]
                self.result = next(
                    (queue for queue in self.connection.queues if queue["id"] == queue_id),
                    None,
                )
        elif normalized_query.startswith("INSERT INTO queues"):
            service_id = params[0]
            self.lastrowid = self.connection.next_queue_id
            self.connection.queues.append(
                {
                    "id": self.lastrowid,
                    "service_id": service_id,
                    "status": "open",
                    "created_at": "2026-11-05T00:00:00",
                }
            )
            self.connection.next_queue_id += 1
            self.result = None
        elif normalized_query.startswith("UPDATE queues"):
            queue_id = params[0]
            for queue in self.connection.queues:
                if queue["id"] == queue_id:
                    queue["status"] = "closed"
                    break
            self.result = None
        elif normalized_query.startswith("UPDATE queue_entries"):
            self.result = None
        else:
            raise AssertionError(f"Unexpected SQL: {normalized_query}")

    def fetchone(self):
        return self.result


class FakeConnection:
    def __init__(self):
        self.service_ids = {10}
        self.queues = []
        self.next_queue_id = 1
        self.queries = []

    def cursor(self):
        return FakeCursor(self)


def install_fake_database(monkeypatch):
    connection = FakeConnection()

    @contextmanager
    def connection_scope():
        yield connection

    monkeypatch.setattr(queues.database, "connection_scope", connection_scope)
    monkeypatch.setattr(queues.auth, "is_admin", lambda email: True)
    return connection


def test_create_active_queue_returns_existing_queue(monkeypatch):
    connection = install_fake_database(monkeypatch)

    first_response = client.post("/api/queues/services/10", json={"email": "admin@example.com"})
    second_response = client.post("/api/queues/services/10", json={"email": "admin@example.com"})

    assert first_response.status_code == 200
    assert first_response.json()["status"] == "open"
    assert second_response.json() == first_response.json()
    assert len(connection.queues) == 1
    assert ("INSERT INTO queues (service_id) VALUES (%s)", (10,)) in connection.queries


def test_create_queue_requires_existing_service(monkeypatch):
    install_fake_database(monkeypatch)

    response = client.post("/api/queues/services/99", json={"email": "admin@example.com"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Service not found"


def test_retrieve_and_close_active_queue(monkeypatch):
    install_fake_database(monkeypatch)
    created = client.post("/api/queues/services/10", json={"email": "admin@example.com"}).json()

    active_response = client.get("/api/queues/services/10/active")
    closed_response = client.post(
        f"/api/queues/{created['id']}/close",
        json={"email": "admin@example.com"},
    )
    missing_active_response = client.get("/api/queues/services/10/active")

    assert active_response.status_code == 200
    assert active_response.json()["id"] == created["id"]
    assert closed_response.status_code == 200
    assert closed_response.json()["status"] == "closed"
    assert missing_active_response.status_code == 404


def test_close_queue_is_idempotent_and_missing_queue_is_not_found(monkeypatch):
    install_fake_database(monkeypatch)
    created = client.post("/api/queues/services/10", json={"email": "admin@example.com"}).json()

    first_close = client.post(
        f"/api/queues/{created['id']}/close",
        json={"email": "admin@example.com"},
    )
    repeated_close = client.post(
        f"/api/queues/{created['id']}/close",
        json={"email": "admin@example.com"},
    )
    missing_close = client.post(
        "/api/queues/999/close",
        json={"email": "admin@example.com"},
    )

    assert first_close.json()["status"] == "closed"
    assert repeated_close.json()["status"] == "closed"
    assert missing_close.status_code == 404


def test_close_queue_requires_admin(monkeypatch):
    install_fake_database(monkeypatch)
    monkeypatch.setattr(queues.auth, "is_admin", lambda email: False)

    response = client.post(
        "/api/queues/1/close",
        json={"email": "user@example.com"},
    )

    assert response.status_code == 403


def test_open_queue_requires_admin(monkeypatch):
    install_fake_database(monkeypatch)
    monkeypatch.setattr(queues.auth, "is_admin", lambda email: False)

    response = client.post(
        "/api/queues/services/10",
        json={"email": "user@example.com"},
    )

    assert response.status_code == 403


def test_closing_queue_cancels_waiting_entries(monkeypatch):
    connection = install_fake_database(monkeypatch)
    created = client.post("/api/queues/services/10", json={"email": "admin@example.com"}).json()

    client.post(f"/api/queues/{created['id']}/close", json={"email": "admin@example.com"})

    assert (
        "UPDATE queue_entries SET status = 'canceled' WHERE queue_id = %s AND status = 'waiting'",
        (created["id"],),
    ) in connection.queries
