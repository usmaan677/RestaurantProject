from fastapi.testclient import TestClient
from main import app
import auth

client = TestClient(app)


def test_health():
    assert client.get("/api/health").json() == {"status": "ok"}


# ---------- Register ----------

def test_register_success():
    response = client.post("/api/auth/register", json={
        "email": "new1@gmail.com",
        "password": "password123",
        "confirm_password": "password123",
    })

    assert response.status_code == 201
    assert response.json() == {"email": "new1@gmail.com", "role": "user"}


def test_register_does_not_return_password():
    response = client.post("/api/auth/register", json={
        "email": "new2@gmail.com",
        "password": "password123",
        "confirm_password": "password123",
    })

    assert "password" not in response.json()
    assert "password_hash" not in response.json()


def test_register_duplicate_email():
    body = {"email": "new3@gmail.com", "password": "password123", "confirm_password": "password123"}
    client.post("/api/auth/register", json=body)

    response = client.post("/api/auth/register", json=body)

    assert response.status_code == 400
    assert response.json()["detail"] == "Email is already registered"


def test_register_passwords_do_not_match():
    response = client.post("/api/auth/register", json={
        "email": "new4@gmail.com",
        "password": "password123",
        "confirm_password": "different123",
    })

    assert response.status_code == 400
    assert response.json()["detail"] == "Passwords do not match"


def test_register_password_too_short():
    response = client.post("/api/auth/register", json={
        "email": "new5@gmail.com",
        "password": "short",
        "confirm_password": "short",
    })

    assert response.status_code == 422


def test_register_password_too_long():
    long_password = "a" * 65
    response = client.post("/api/auth/register", json={
        "email": "new6@gmail.com",
        "password": long_password,
        "confirm_password": long_password,
    })

    assert response.status_code == 422


def test_register_invalid_email():
    response = client.post("/api/auth/register", json={
        "email": "not-an-email",
        "password": "password123",
        "confirm_password": "password123",
    })

    assert response.status_code == 422


def test_register_missing_field():
    response = client.post("/api/auth/register", json={
        "email": "new7@gmail.com",
        "password": "password123",
    })

    assert response.status_code == 422


def test_register_wrong_type():
    response = client.post("/api/auth/register", json={
        "email": "new8@gmail.com",
        "password": 12345678,
        "confirm_password": 12345678,
    })

    assert response.status_code == 422


# ---------- Login ----------

def test_login_user():
    response = client.post("/api/auth/login", json={
        "email": "user@queuesmart.com",
        "password": "user1234",
    })

    assert response.status_code == 200
    assert response.json()["role"] == "user"


def test_login_admin():
    response = client.post("/api/auth/login", json={
        "email": "admin@queuesmart.com",
        "password": "admin1234",
    })

    assert response.status_code == 200
    assert response.json()["role"] == "admin"


def test_login_after_register():
    client.post("/api/auth/register", json={
        "email": "new9@gmail.com",
        "password": "password123",
        "confirm_password": "password123",
    })

    response = client.post("/api/auth/login", json={
        "email": "new9@gmail.com",
        "password": "password123",
    })

    assert response.status_code == 200


def test_login_email_is_not_case_sensitive():
    response = client.post("/api/auth/login", json = {
        "email": "ADMIN@queuesmart.com",
        "password": "admin1234",
    })

    assert response.status_code == 200


def test_login_wrong_password():
    response = client.post("/api/auth/login", json={
        "email": "user@queuesmart.com",
        "password": "wrongpassword",
    })

    assert response.status_code == 401


def test_login_unknown_email():
    response = client.post("/api/auth/login", json = {
        "email": "nobody@gmail.com",
        "password": "password123",
    })

    assert response.status_code == 401


def test_login_empty_password():
    response = client.post("/api/auth/login", json={
        "email": "user@queuesmart.com",
        "password": "",
    })

    assert response.status_code == 422


#Helpers

def test_passwords_are_hashed():
    user = auth.get_user_by_email("admin@queuesmart.com")

    assert user["password_hash"] != "admin1234"


def test_is_admin():
    assert auth.is_admin("admin@queuesmart.com") is True
    assert auth.is_admin("user@queuesmart.com") is False
    assert auth.is_admin("nobody@gmail.com") is False