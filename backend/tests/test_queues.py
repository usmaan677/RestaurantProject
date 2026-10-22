from fastapi.testclient import TestClient
from main import app
import history
import queues
import services
import notifications

client = TestClient(app)


def setup_function():
    queues.queue_entries.clear()
    queues.next_entry_id = 1
    services.services.clear()
    services.next_service_id = 1
    history.history_entries.clear()
    history.next_history_id = 1
    notifications.notifications.clear()
    notifications.next_notification_id = 1


def create_test_service(expected_duration=15, priority=3):
    response = client.post("/api/services/", json={
        "name": "Takeout",
        "description": "Order food for pickup",
        "expected_duration": expected_duration,
        "priority": priority
    })

    return response.json()["id"]


def test_join_queue_success():
    service_id = create_test_service(expected_duration=10)

    response = client.post("/api/queues/join", json={
        "email": "alice@gmail.com",
        "service_id": service_id,
        "priority": 3
    })

    assert response.status_code == 200
    assert response.json()["position"] == 1
    assert response.json()["estimated_wait"] == 10


def test_join_queue_adds_history_entry():
    service_id = create_test_service()

    client.post("/api/queues/join", json={
        "email": "alice@gmail.com",
        "service_id": service_id,
        "priority": 3
    })

    response = client.get("/api/history?email=alice@gmail.com")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["outcome"] == "Joined Queue"


def test_join_queue_default_priority():
    service_id = create_test_service()

    response = client.post("/api/queues/join", json={
        "email": "alice@gmail.com",
        "service_id": service_id
    })

    assert response.status_code == 200
    assert response.json()["priority"] == 1


def test_join_queue_service_not_found():
    response = client.post("/api/queues/join", json={
        "email": "alice@gmail.com",
        "service_id": 999,
        "priority": 3
    })

    assert response.status_code == 404
    assert response.json()["detail"] == "Service not found"


def test_join_queue_duplicate_user():
    service_id = create_test_service()

    client.post("/api/queues/join", json={
        "email": "alice@gmail.com",
        "service_id": service_id,
        "priority": 3
    })

    response = client.post("/api/queues/join", json={
        "email": "alice@gmail.com",
        "service_id": service_id,
        "priority": 3
    })

    assert response.status_code == 400


def test_join_queue_email_is_not_case_sensitive():
    service_id = create_test_service()

    client.post("/api/queues/join", json={
        "email": "alice@gmail.com",
        "service_id": service_id,
        "priority": 3
    })

    response = client.post("/api/queues/join", json={
        "email": "ALICE@gmail.com",
        "service_id": service_id,
        "priority": 3
    })

    assert response.status_code == 400


def test_join_queue_missing_email():
    service_id = create_test_service()

    response = client.post("/api/queues/join", json={
        "service_id": service_id,
        "priority": 3
    })

    assert response.status_code == 422


def test_join_queue_invalid_email():
    service_id = create_test_service()

    response = client.post("/api/queues/join", json={
        "email": "not-an-email",
        "service_id": service_id,
        "priority": 3
    })

    assert response.status_code == 422


def test_join_queue_missing_service_id():
    response = client.post("/api/queues/join", json={
        "email": "alice@gmail.com",
        "priority": 3
    })

    assert response.status_code == 422


def test_join_queue_invalid_priority_too_high():
    service_id = create_test_service()

    response = client.post("/api/queues/join", json={
        "email": "alice@gmail.com",
        "service_id": service_id,
        "priority": 6
    })

    assert response.status_code == 422


def test_join_queue_invalid_priority_too_low():
    service_id = create_test_service()

    response = client.post("/api/queues/join", json={
        "email": "alice@gmail.com",
        "service_id": service_id,
        "priority": 0
    })

    assert response.status_code == 422


def test_leave_queue_success():
    service_id = create_test_service()

    client.post("/api/queues/join", json={
        "email": "alice@gmail.com",
        "service_id": service_id,
        "priority": 3
    })

    response = client.post("/api/queues/leave", json={
        "email": "alice@gmail.com",
        "service_id": service_id
    })

    assert response.status_code == 200

    rejoin = client.post("/api/queues/join", json={
        "email": "alice@gmail.com",
        "service_id": service_id,
        "priority": 3
    })

    assert rejoin.status_code == 200


def test_leave_queue_adds_history_entry():
    service_id = create_test_service()

    client.post("/api/queues/join", json={
        "email": "alice@gmail.com",
        "service_id": service_id,
        "priority": 3
    })

    client.post("/api/queues/leave", json={
        "email": "alice@gmail.com",
        "service_id": service_id
    })

    response = client.get("/api/history?email=alice@gmail.com")

    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["outcome"] == "Left Queue"
    assert response.json()[1]["outcome"] == "Joined Queue"


def test_leave_queue_service_not_found():
    response = client.post("/api/queues/leave", json={
        "email": "alice@gmail.com",
        "service_id": 999
    })

    assert response.status_code == 404


def test_leave_queue_user_not_in_queue():
    service_id = create_test_service()

    response = client.post("/api/queues/leave", json={
        "email": "alice@gmail.com",
        "service_id": service_id
    })

    assert response.status_code == 404


def test_leave_queue_missing_fields():
    response = client.post("/api/queues/leave", json={
        "email": "alice@gmail.com"
    })

    assert response.status_code == 422


def test_queue_ordering_by_priority():
    service_id = create_test_service()

    client.post("/api/queues/join", json={"email": "alice@gmail.com", "service_id": service_id, "priority": 2})
    client.post("/api/queues/join", json={"email": "bob@gmail.com", "service_id": service_id, "priority": 5})
    client.post("/api/queues/join", json={"email": "carol@gmail.com", "service_id": service_id, "priority": 3})

    pos_bob = client.get(f"/api/queues/{service_id}/position/bob@gmail.com").json()["position"]
    pos_carol = client.get(f"/api/queues/{service_id}/position/carol@gmail.com").json()["position"]
    pos_alice = client.get(f"/api/queues/{service_id}/position/alice@gmail.com").json()["position"]

    assert pos_bob == 1
    assert pos_carol == 2
    assert pos_alice == 3


def test_queue_ordering_tiebreak_by_arrival():
    service_id = create_test_service()

    client.post("/api/queues/join", json={"email": "alice@gmail.com", "service_id": service_id, "priority": 3})
    client.post("/api/queues/join", json={"email": "bob@gmail.com", "service_id": service_id, "priority": 3})
    client.post("/api/queues/join", json={"email": "carol@gmail.com", "service_id": service_id, "priority": 3})

    pos_alice = client.get(f"/api/queues/{service_id}/position/alice@gmail.com").json()["position"]
    pos_bob = client.get(f"/api/queues/{service_id}/position/bob@gmail.com").json()["position"]
    pos_carol = client.get(f"/api/queues/{service_id}/position/carol@gmail.com").json()["position"]

    assert pos_alice == 1
    assert pos_bob == 2
    assert pos_carol == 3


def test_wait_time_calculation():
    service_id = create_test_service(expected_duration=10)

    client.post("/api/queues/join", json={"email": "alice@gmail.com", "service_id": service_id, "priority": 3})
    client.post("/api/queues/join", json={"email": "bob@gmail.com", "service_id": service_id, "priority": 3})
    client.post("/api/queues/join", json={"email": "carol@gmail.com", "service_id": service_id, "priority": 3})

    wait_alice = client.get(f"/api/queues/{service_id}/position/alice@gmail.com").json()["estimated_wait"]
    wait_bob = client.get(f"/api/queues/{service_id}/position/bob@gmail.com").json()["estimated_wait"]
    wait_carol = client.get(f"/api/queues/{service_id}/position/carol@gmail.com").json()["estimated_wait"]

    assert wait_alice == 10
    assert wait_bob == 20
    assert wait_carol == 30


def test_wait_time_with_mixed_priority():
    service_id = create_test_service(expected_duration=10)

    client.post("/api/queues/join", json={"email": "alice@gmail.com", "service_id": service_id, "priority": 1})
    client.post("/api/queues/join", json={"email": "bob@gmail.com", "service_id": service_id, "priority": 5})

    wait_alice = client.get(f"/api/queues/{service_id}/position/alice@gmail.com").json()["estimated_wait"]
    wait_bob = client.get(f"/api/queues/{service_id}/position/bob@gmail.com").json()["estimated_wait"]

    assert wait_bob < wait_alice


def test_get_position_route_success():
    service_id = create_test_service()

    client.post("/api/queues/join", json={"email": "alice@gmail.com", "service_id": service_id, "priority": 3})

    response = client.get(f"/api/queues/{service_id}/position/alice@gmail.com")

    assert response.status_code == 200
    assert response.json()["position"] == 1


def test_get_position_route_user_not_in_queue():
    service_id = create_test_service()

    response = client.get(f"/api/queues/{service_id}/position/alice@gmail.com")

    assert response.status_code == 404


def test_get_position_route_service_not_found():
    response = client.get("/api/queues/999/position/alice@gmail.com")

    assert response.status_code == 404


def test_get_my_queues_route():
    service_id_1 = create_test_service()
    service_id_2 = create_test_service()

    client.post("/api/queues/join", json={"email": "alice@gmail.com", "service_id": service_id_1, "priority": 3})
    client.post("/api/queues/join", json={"email": "alice@gmail.com", "service_id": service_id_2, "priority": 3})

    response = client.get("/api/queues/mine?email=alice@gmail.com")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_my_queues_route_empty():
    response = client.get("/api/queues/mine?email=alice@gmail.com")

    assert response.status_code == 200
    assert response.json() == []


def test_get_queue_count_route():
    service_id = create_test_service()

    client.post("/api/queues/join", json={"email": "alice@gmail.com", "service_id": service_id, "priority": 3})
    client.post("/api/queues/join", json={"email": "bob@gmail.com", "service_id": service_id, "priority": 3})

    response = client.get(f"/api/queues/{service_id}/count")

    assert response.status_code == 200
    assert response.json()["count"] == 2


def test_get_queue_count_route_service_not_found():
    response = client.get("/api/queues/999/count")

    assert response.status_code == 404
