import pytest
from fastapi.testclient import TestClient
from fake_database import use_fake_history, use_fake_notifications, use_fake_queue_entries
from main import app
import notifications
import queues
import services

client = TestClient(app)


@pytest.fixture(autouse=True)
def open_queue_for_notification_tests(monkeypatch):
    monkeypatch.setattr(
        queues,
        "get_active_queue",
        lambda service_id: {
            "id": 1,
            "service_id": service_id,
            "status": "open",
        },
    )
    use_fake_notifications(monkeypatch)
    use_fake_history(monkeypatch)
    use_fake_queue_entries(monkeypatch)


def setup_function():
    services.services.clear()
    services.next_service_id = 1


def create_test_service():
    response = client.post("/api/services/", json={
        "name": "Takeout", "description": "Pickup", "priority": 3, "expected_duration": 10
    })
    return response.json()["id"]


def join(email, service_id):
    return client.post("/api/queues/join", json={"email": email, "service_id": service_id})


def get_messages(email):
    return [n["message"] for n in client.get(f"/api/notifications/{email}").json()]


def test_no_notifications_returns_empty_list():
    response = client.get("/api/notifications/a@test.com")

    assert response.status_code == 200
    assert response.json() == []


def test_join_creates_notification():
    service_id = create_test_service()
    join("a@test.com", service_id)

    assert "You joined the Takeout queue. You are #1." in get_messages("a@test.com")


def test_close_to_served_notification():
    service_id = create_test_service()
    join("a@test.com", service_id)

    assert "You're almost up for Takeout!" in get_messages("a@test.com")


def test_far_back_user_not_notified_until_moving_up():
    service_id = create_test_service()
    join("a@test.com", service_id)
    join("b@test.com", service_id)
    join("c@test.com", service_id)  # 3rd in line, not close yet

    assert "You're almost up for Takeout!" not in get_messages("c@test.com")

    client.post("/api/queues/leave", json={"email": "a@test.com", "service_id": service_id})

    assert "You're almost up for Takeout!" in get_messages("c@test.com")


def test_close_notification_not_duplicated():
    service_id = create_test_service()
    join("a@test.com", service_id)
    join("b@test.com", service_id)

    assert get_messages("a@test.com").count("You're almost up for Takeout!") == 1


def test_notifications_email_is_not_case_sensitive():
    service_id = create_test_service()
    join("A@Test.com", service_id)

    assert "You joined the Takeout queue. You are #1." in get_messages("a@test.com")


def test_add_and_get_notification_logic():
    notifications.add_notification("a@test.com", "hello")

    assert len(notifications.get_notifications("a@test.com")) == 1
    assert notifications.get_notifications("b@test.com") == []


def test_rejoining_sends_close_notification_again():
    service_id = create_test_service()
    join("a@test.com", service_id)
    client.post("/api/queues/leave", json={"email": "a@test.com", "service_id": service_id})
    join("a@test.com", service_id)

    assert get_messages("a@test.com").count("You're almost up for Takeout!") == 2


def test_joining_other_service_does_not_repeat_close_notification():
    takeout_id = create_test_service()
    dine_in_id = client.post("/api/services/", json={
        "name": "Dine In", "description": "Table", "priority": 3, "expected_duration": 10
    }).json()["id"]

    join("a@test.com", takeout_id)
    join("a@test.com", dine_in_id)
    join("b@test.com", takeout_id)

    assert get_messages("a@test.com").count("You're almost up for Takeout!") == 1


def test_new_notifications_have_status_sent():
    notifications.add_notification("a@test.com", "hello")

    response = client.get("/api/notifications/a@test.com")

    assert response.json()[0]["status"] == "sent"


def test_mark_viewed_only_changes_that_user():
    notifications.add_notification("a@test.com", "hello")
    notifications.add_notification("b@test.com", "hello")

    response = client.post("/api/notifications/A@Test.com/viewed")

    assert response.status_code == 200
    assert response.json()[0]["status"] == "viewed"
    assert client.get("/api/notifications/b@test.com").json()[0]["status"] == "sent"
