from fastapi.testclient import TestClient
from main import app
from fake_database import use_fake_services
import pytest

client = TestClient(app)


@pytest.fixture(autouse=True)
def fake_services(monkeypatch):
    return use_fake_services(monkeypatch)
    

def test_create_service():
    response = client.post("/api/services/?email=admin@queuesmart.com", json={
        "name": "Takeout",
        "description": "Order food for pickup",
        "expected_duration": 15,
        "priority": 3
    })
    
    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert response.json()["name"] == "Takeout"
    

def test_list_services():
    client.post("/api/services/?email=admin@queuesmart.com", json={
        "name": "Takeout",
        "description": "Order food for pickup",
        "expected_duration": 15,
        "priority": 3
    })
    
    response = client.get("/api/services/")
    
    assert response.status_code == 200
    assert len(response.json()) == 1
    
    
def test_get_service():
    client.post("/api/services/?email=admin@queuesmart.com", json={
        "name": "Takeout",
        "description": "Order food for pickup",
        "expected_duration": 15,
        "priority": 3
    })
    
    response = client.get("/api/services/1")
    
    assert response.status_code == 200
    assert response.json()["name"] == "Takeout"
    
    
def test_update_service():
    client.post("/api/services/?email=admin@queuesmart.com", json={
        "name": "Takeout",
        "description": "Order food for pickup",
        "expected_duration": 15,
        "priority": 3
    })
    
    response = client.put("/api/services/1?email=admin@queuesmart.com", json={
        "priority": 1
    })
    
    assert response.status_code == 200
    assert response.json()["priority"] == 1
    assert response.json()["name"] == "Takeout"
    
    
def test_update_service_not_found():
    response = response = client.put("/api/services/999?email=admin@queuesmart.com", json={
        "priority": 1
    })
    
    assert response.status_code == 404
    
    
def test_create_service_missing_name():
    response = client.post("/api/services/?email=admin@queuesmart.com", json={
        "description": "Order food for pickup",
        "expected_duration": 15,
        "priority": 3
    })
    
    assert response.status_code == 422
    
    
def test_create_service_invalid_duration():
    response = client.post("/api/services/?email=admin@queuesmart.com", json={
       "name": "Takeout",
       "description": "Order food for pickup",
       "expected_duration": 0,
       "priority": 3
    })
    
    assert response.status_code == 422
    
    
def test_create_service_invalid_priority():
    response = client.post("/api/services/?email=admin@queuesmart.com", json={
        "name": "Takeout",
        "description": "Order food for pickup",
        "expected_duration": 15,
        "priority": 6
    })
    
    assert response.status_code == 422
    
    
def test_create_service_name_too_long():
    response = client.post("/api/services/?email=admin@queuesmart.com", json={
        "name": "A" * 101,
        "description": "Order food for pickup",
        "expected_duration": 15,
        "priority": 3
    })
    
    assert response.status_code == 422
    
    
def test_get_service_not_found():
    response = client.get("/api/services/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Service not found"