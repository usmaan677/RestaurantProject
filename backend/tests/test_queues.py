from fastapi.testclient import TestClient
from main import app
import queues
import services

client = TestClient(app)


def setup_function():
    queues.queue_entries.clear()
    queues.next_entry_id = 1
    services.services.clear()
    services.next_service_id = 1


def create_test_service(expected_duration=15, priority=3):
    response = client.post("/api/services/", json={
        "name": "Takeout",
        "description": "Order food for pickup",
        "expected_duration": expected_duration,
        "priority": priority
    })

    return response.json()["id"]


def test_join_queue_success():
    service_id = create_test_service()

    response = client.post("/api/queues/join", json={
        "user_id": 1,
        "service_id": service_id,
        "priority": 3
    })

    assert response.status_code == 200
    assert response.json()["position"] == 1
    assert response.json()["estimated_wait"] == 0


def test_join_queue_default_priority():
    service_id = create_test_service()

    response = client.post("/api/queues/join", json={
        "user_id": 1,
        "service_id": service_id
    })

    assert response.status_code == 200
    assert response.json()["priority"] == 1


def test_join_queue_service_not_found():
    response = client.post("/api/queues/join", json={
        "user_id": 1,
        "service_id": 999,
        "priority": 3
    })

    assert response.status_code == 404
    assert response.json()["detail"] == "Service not found"


def test_join_queue_duplicate_user():
    service_id = create_test_service()

    client.post("/api/queues/join", json={
        "user_id": 1,
        "service_id": service_id,
        "priority": 3
    })

    response = client.post("/api/queues/join", json={
        "user_id": 1,
        "service_id": service_id,
        "priority": 3
    })

    assert response.status_code == 400


def test_join_queue_missing_user_id():
    service_id = create_test_service()

    response = client.post("/api/queues/join", json={
        "service_id": service_id,
        "priority": 3
    })

    assert response.status_code == 422


def test_join_queue_missing_service_id():
    response = client.post("/api/queues/join", json={
        "user_id": 1,
        "priority": 3
    })

    assert response.status_code == 422


def test_join_queue_invalid_priority_too_high():
    service_id = create_test_service()

    response = client.post("/api/queues/join", json={
        "user_id": 1,
        "service_id": service_id,
        "priority": 6
    })

    assert response.status_code == 422


def test_join_queue_invalid_priority_too_low():
    service_id = create_test_service()

    response = client.post("/api/queues/join", json={
        "user_id": 1,
        "service_id": service_id,
        "priority": 0
    })

    assert response.status_code == 422


def test_join_queue_wrong_type_user_id():
    service_id = create_test_service()

    response = client.post("/api/queues/join", json={
        "user_id": "abc",
        "service_id": service_id,
        "priority": 3
    })

    assert response.status_code == 422


def test_leave_queue_success():
    service_id = create_test_service()

    client.post("/api/queues/join", json={
        "user_id": 1,
        "service_id": service_id,
        "priority": 3
    })

    response = client.post("/api/queues/leave", json={
        "user_id": 1,
        "service_id": service_id
    })

    assert response.status_code == 200

    rejoin = client.post("/api/queues/join", json={
        "user_id": 1,
        "service_id": service_id,
        "priority": 3
    })

    assert rejoin.status_code == 200


def test_leave_queue_service_not_found():
    response = client.post("/api/queues/leave", json={
        "user_id": 1,
        "service_id": 999
    })

    assert response.status_code == 404


def test_leave_queue_user_not_in_queue():
    service_id = create_test_service()

    response = client.post("/api/queues/leave", json={
        "user_id": 1,
        "service_id": service_id
    })

    assert response.status_code == 404


def test_leave_queue_missing_fields():
    response = client.post("/api/queues/leave", json={
        "user_id": 1
    })

    assert response.status_code == 422


def test_queue_ordering_by_priority():
    service_id = create_test_service()

    client.post("/api/queues/join", json={"user_id": 1, "service_id": service_id, "priority": 2})
    client.post("/api/queues/join", json={"user_id": 2, "service_id": service_id, "priority": 5})
    client.post("/api/queues/join", json={"user_id": 3, "service_id": service_id, "priority": 3})

    pos_user_2 = client.get(f"/api/queues/{service_id}/position/2").json()["position"]
    pos_user_3 = client.get(f"/api/queues/{service_id}/position/3").json()["position"]
    pos_user_1 = client.get(f"/api/queues/{service_id}/position/1").json()["position"]

    assert pos_user_2 == 1
    assert pos_user_3 == 2
    assert pos_user_1 == 3


def test_queue_ordering_tiebreak_by_arrival():
    service_id = create_test_service()

    client.post("/api/queues/join", json={"user_id": 1, "service_id": service_id, "priority": 3})
    client.post("/api/queues/join", json={"user_id": 2, "service_id": service_id, "priority": 3})
    client.post("/api/queues/join", json={"user_id": 3, "service_id": service_id, "priority": 3})

    pos_user_1 = client.get(f"/api/queues/{service_id}/position/1").json()["position"]
    pos_user_2 = client.get(f"/api/queues/{service_id}/position/2").json()["position"]
    pos_user_3 = client.get(f"/api/queues/{service_id}/position/3").json()["position"]

    assert pos_user_1 == 1
    assert pos_user_2 == 2
    assert pos_user_3 == 3


def test_wait_time_calculation():
    service_id = create_test_service(expected_duration=10)

    client.post("/api/queues/join", json={"user_id": 1, "service_id": service_id, "priority": 3})
    client.post("/api/queues/join", json={"user_id": 2, "service_id": service_id, "priority": 3})
    client.post("/api/queues/join", json={"user_id": 3, "service_id": service_id, "priority": 3})

    wait_user_1 = client.get(f"/api/queues/{service_id}/position/1").json()["estimated_wait"]
    wait_user_2 = client.get(f"/api/queues/{service_id}/position/2").json()["estimated_wait"]
    wait_user_3 = client.get(f"/api/queues/{service_id}/position/3").json()["estimated_wait"]

    assert wait_user_1 == 0
    assert wait_user_2 == 10
    assert wait_user_3 == 20


def test_wait_time_with_mixed_priority():
    service_id = create_test_service(expected_duration=10)

    client.post("/api/queues/join", json={"user_id": 1, "service_id": service_id, "priority": 1})
    client.post("/api/queues/join", json={"user_id": 2, "service_id": service_id, "priority": 5})

    wait_user_1 = client.get(f"/api/queues/{service_id}/position/1").json()["estimated_wait"]
    wait_user_2 = client.get(f"/api/queues/{service_id}/position/2").json()["estimated_wait"]

    assert wait_user_2 < wait_user_1


def test_get_position_route_success():
    service_id = create_test_service()

    client.post("/api/queues/join", json={"user_id": 1, "service_id": service_id, "priority": 3})

    response = client.get(f"/api/queues/{service_id}/position/1")

    assert response.status_code == 200
    assert response.json()["position"] == 1


def test_get_position_route_user_not_in_queue():
    service_id = create_test_service()

    response = client.get(f"/api/queues/{service_id}/position/1")

    assert response.status_code == 404


def test_get_position_route_service_not_found():
    response = client.get("/api/queues/999/position/1")

    assert response.status_code == 404
