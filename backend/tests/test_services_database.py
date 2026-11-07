
import uuid

import pytest
from fastapi.testclient import TestClient

from main import app
import database

client = TestClient(app)

ADMIN_EMAIL = "admin@queuesmart.com"
USER_EMAIL = "user@queuesmart.com"


# Tracks services created during each test so they can be deleted afterward.
@pytest.fixture
def created_services():
    service_ids = []

    yield service_ids

    if service_ids:
        with database.connection_scope() as connection:
            with connection.cursor() as cursor:
                for service_id in service_ids:
                    cursor.execute(
                        "DELETE FROM services WHERE id = %s",
                        (service_id,)
                    )


# Creates a uniquely named service for testing.
def create_test_service(created_services):
    name = f"Test Service {uuid.uuid4().hex[:8]}"

    response = client.post(
        f"/api/services/?email={ADMIN_EMAIL}",
        json={
            "name": name,
            "description": "Testing MySQL integration",
            "expected_duration": 15,
            "priority": 3
        }
    )

    assert response.status_code == 200

    service = response.json()
    created_services.append(service["id"])

    return service


def test_create_service(created_services):
    service = create_test_service(created_services)

    assert service["id"] is not None
    assert service["name"].startswith("Test Service")


def test_list_services(created_services):
    service = create_test_service(created_services)

    response = client.get("/api/services/")

    assert response.status_code == 200
    assert any(
        item["id"] == service["id"]
        for item in response.json()
    )


def test_get_service(created_services):
    service = create_test_service(created_services)

    response = client.get(f"/api/services/{service['id']}")

    assert response.status_code == 200
    assert response.json()["name"] == service["name"]


def test_update_service(created_services):
    service = create_test_service(created_services)

    response = client.put(
        f"/api/services/{service['id']}?email={ADMIN_EMAIL}",
        json={"priority": 5}
    )

    assert response.status_code == 200
    assert response.json()["priority"] == 5
    assert response.json()["name"] == service["name"]


def test_update_service_not_found():
    response = client.put(
        f"/api/services/999999?email={ADMIN_EMAIL}",
        json={"priority": 1}
    )

    assert response.status_code == 404


def test_get_service_not_found():
    response = client.get("/api/services/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Service not found"


def test_create_service_missing_name():
    response = client.post(
        f"/api/services/?email={ADMIN_EMAIL}",
        json={
            "description": "Testing validation",
            "expected_duration": 15,
            "priority": 3
        }
    )

    assert response.status_code == 422


def test_create_service_invalid_duration():
    response = client.post(
        f"/api/services/?email={ADMIN_EMAIL}",
        json={
            "name": "Invalid Service",
            "description": "Testing validation",
            "expected_duration": 0,
            "priority": 3
        }
    )

    assert response.status_code == 422


def test_create_service_invalid_priority():
    response = client.post(
        f"/api/services/?email={ADMIN_EMAIL}",
        json={
            "name": "Invalid Service",
            "description": "Testing validation",
            "expected_duration": 15,
            "priority": 6
        }
    )

    assert response.status_code == 422


def test_create_service_name_too_long():
    response = client.post(
        f"/api/services/?email={ADMIN_EMAIL}",
        json={
            "name": "A" * 101,
            "description": "Testing validation",
            "expected_duration": 15,
            "priority": 3
        }
    )

    assert response.status_code == 422


def test_regular_user_cannot_create_service():
    response = client.post(
        f"/api/services/?email={USER_EMAIL}",
        json={
            "name": "Unauthorized Service",
            "description": "Testing permissions",
            "expected_duration": 15,
            "priority": 3
        }
    )

    assert response.status_code == 403


def test_regular_user_cannot_update_service(created_services):
    service = create_test_service(created_services)

    response = client.put(
        f"/api/services/{service['id']}?email={USER_EMAIL}",
        json={"priority": 1}
    )

    assert response.status_code == 403


def test_create_service_requires_email():
    response = client.post(
        "/api/services/",
        json={
            "name": "Missing Email",
            "description": "Testing permissions",
            "expected_duration": 15,
            "priority": 3
        }
    )

    assert response.status_code == 422

def test_service_persists_in_database(created_services):
    service = create_test_service(created_services)

    with database.connection_scope() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM services WHERE id = %s",
                (service["id"],)
            )
            result = cursor.fetchone()

    assert result is not None
    assert result["name"] == service["name"]