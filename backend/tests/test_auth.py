import pymysql
import pytest
from fastapi.testclient import TestClient
from main import app
import auth

client = TestClient(app)


# ---------- Fake database (a plain list instead of MySQL) ----------

fake_users = []
admin_password_hash = auth.hash_password("admin1234")
user_password_hash = auth.hash_password("user1234")


def fake_get_user_by_email(email):
    for user in fake_users:
        if user["email"] == email:
            return user

    return None


def fake_add_user(user):
    fake_users.append(user)
    return user


@pytest.fixture(autouse=True)
def use_fake_database(monkeypatch):
    fake_users.clear()
    fake_users.append({
        "email": "admin@queuesmart.com",
        "password_hash": admin_password_hash,
        "role": "admin",
        "full_name": "Admin User",
    })
    fake_users.append({
        "email": "user@queuesmart.com",
        "password_hash": user_password_hash,
        "role": "user",
        "full_name": "Test User",
    })
    monkeypatch.setattr(auth, "get_user_by_email", fake_get_user_by_email)
    monkeypatch.setattr(auth, "add_user", fake_add_user)


def test_health():
    assert client.get("/api/health").json() == {"status": "ok"}


# ---------- Register ----------

def test_register_success():
    response = client.post("/api/auth/register", json={
        "full_name": "Test Person",
        "email": "new1@gmail.com",
        "password": "password123",
        "confirm_password": "password123",
    })

    assert response.status_code == 201
    assert response.json() == {"email": "new1@gmail.com", "role": "user", "full_name": "Test Person"}


def test_register_does_not_return_password():
    response = client.post("/api/auth/register", json={
        "full_name": "Test Person",
        "email": "new2@gmail.com",
        "password": "password123",
        "confirm_password": "password123",
    })

    assert "password" not in response.json()
    assert "password_hash" not in response.json()


def test_register_duplicate_email():
    body = {"full_name": "Test Person", "email": "new3@gmail.com", "password": "password123", "confirm_password": "password123"}
    client.post("/api/auth/register", json=body)

    response = client.post("/api/auth/register", json=body)

    assert response.status_code == 400
    assert response.json()["detail"] == "Email is already registered"


def test_register_passwords_do_not_match():
    response = client.post("/api/auth/register", json={
        "full_name": "Test Person",
        "email": "new4@gmail.com",
        "password": "password123",
        "confirm_password": "different123",
    })

    assert response.status_code == 400
    assert response.json()["detail"] == "Passwords do not match"


def test_register_password_too_short():
    response = client.post("/api/auth/register", json={
        "full_name": "Test Person",
        "email": "new5@gmail.com",
        "password": "short",
        "confirm_password": "short",
    })

    assert response.status_code == 422


def test_register_password_too_long():
    long_password = "a" * 65
    response = client.post("/api/auth/register", json={
        "full_name": "Test Person",
        "email": "new6@gmail.com",
        "password": long_password,
        "confirm_password": long_password,
    })

    assert response.status_code == 422


def test_register_invalid_email():
    response = client.post("/api/auth/register", json={
        "full_name": "Test Person",
        "email": "not-an-email",
        "password": "password123",
        "confirm_password": "password123",
    })

    assert response.status_code == 422


def test_register_missing_field():
    response = client.post("/api/auth/register", json={
        "full_name": "Test Person",
        "email": "new7@gmail.com",
        "password": "password123",
    })

    assert response.status_code == 422


def test_register_wrong_type():
    response = client.post("/api/auth/register", json={
        "full_name": "Test Person",
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
        "full_name": "Test Person",
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


def test_passwords_use_bcrypt():
    password_hash = auth.hash_password("password123")

    assert password_hash.startswith("$2b$")
    assert auth.check_password("password123", password_hash) is True
    assert auth.check_password("wrongpassword", password_hash) is False


def test_same_password_gets_different_hashes():
    assert auth.hash_password("password123") != auth.hash_password("password123")


# ---------- Full name ----------

def test_register_saves_full_name():
    client.post("/api/auth/register", json={
        "full_name": "  Jane Doe  ",
        "email": "jane@gmail.com",
        "password": "password123",
        "confirm_password": "password123",
    })

    response = client.post("/api/auth/login", json={
        "email": "jane@gmail.com",
        "password": "password123",
    })

    assert response.json()["full_name"] == "Jane Doe"


def test_register_missing_full_name():
    response = client.post("/api/auth/register", json={
        "email": "noname@gmail.com",
        "password": "password123",
        "confirm_password": "password123",
    })

    assert response.status_code == 422


def test_register_blank_full_name():
    response = client.post("/api/auth/register", json={
        "full_name": "   ",
        "email": "blank@gmail.com",
        "password": "password123",
        "confirm_password": "password123",
    })

    assert response.status_code == 400
    assert response.json()["detail"] == "Full name is required"


def test_register_full_name_too_long():
    response = client.post("/api/auth/register", json={
        "full_name": "a" * 101,
        "email": "longname@gmail.com",
        "password": "password123",
        "confirm_password": "password123",
    })

    assert response.status_code == 422


# ---------- Long passwords (bcrypt limit is 72 bytes) ----------

def test_register_password_over_72_bytes():
    long_password = "é" * 40
    response = client.post("/api/auth/register", json={
        "full_name": "Test Person",
        "email": "bytes@gmail.com",
        "password": long_password,
        "confirm_password": long_password,
    })

    assert response.status_code == 400
    assert response.json()["detail"] == "Password is too long"


def test_login_password_over_72_bytes():
    response = client.post("/api/auth/login", json={
        "email": "user@queuesmart.com",
        "password": "é" * 40,
    })

    assert response.status_code == 401


# ---------- Duplicate caught by the database ----------

def test_register_database_blocks_duplicate(monkeypatch):
    def add_user_that_fails(user):
        raise pymysql.err.IntegrityError(1062, "Duplicate entry")

    monkeypatch.setattr(auth, "add_user", add_user_that_fails)

    response = client.post("/api/auth/register", json={
        "full_name": "Test Person",
        "email": "race@gmail.com",
        "password": "password123",
        "confirm_password": "password123",
    })

    assert response.status_code == 400
    assert response.json()["detail"] == "Email is already registered"