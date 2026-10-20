from fastapi.testclient import TestClient
from main import app
import history

client = TestClient(app)


def setup_function():
    history.history_entries.clear()
    history.next_history_id = 1


def test_get_history_empty():
    response = client.get("/api/history?email=alice@gmail.com")

    assert response.status_code == 200
    assert response.json() == []


def test_get_history_with_entries():
    history.add_history_entry("alice@gmail.com", 1, "Takeout", "Left Queue")

    response = client.get("/api/history?email=alice@gmail.com")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["service_name"] == "Takeout"
    assert response.json()[0]["outcome"] == "Left Queue"


def test_get_history_only_for_that_email():
    history.add_history_entry("alice@gmail.com", 1, "Takeout", "Left Queue")
    history.add_history_entry("bob@gmail.com", 1, "Takeout", "Left Queue")

    response = client.get("/api/history?email=alice@gmail.com")

    assert len(response.json()) == 1


def test_get_history_email_is_not_case_sensitive():
    history.add_history_entry("alice@gmail.com", 1, "Takeout", "Left Queue")

    response = client.get("/api/history?email=ALICE@gmail.com")

    assert len(response.json()) == 1


def test_get_history_most_recent_first():
    history.add_history_entry("alice@gmail.com", 1, "Takeout", "Left Queue")
    history.add_history_entry("alice@gmail.com", 2, "Dine In", "Left Queue")

    response = client.get("/api/history?email=alice@gmail.com")

    assert response.json()[0]["service_name"] == "Dine In"
    assert response.json()[1]["service_name"] == "Takeout"


def test_get_history_missing_email():
    response = client.get("/api/history")

    assert response.status_code == 422
