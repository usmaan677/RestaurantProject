import bcrypt
import pymysql
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field

import database

router = APIRouter(prefix="/api/auth", tags=["auth"])

# ---------- 1. MODELS (what data looks like + validation) ----------
class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=64)
    confirm_password: str = Field(..., min_length=8, max_length=64)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=64)


class UserResponse(BaseModel):
    email: str
    role: str
    full_name: str
# ---------- 2. DATA (MySQL database) ----------
def hash_password(password: str):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def check_password(password: str, password_hash: str):
    # bcrypt only accepts up to 72 bytes
    if len(password.encode()) > 72:
        return False

    return bcrypt.checkpw(password.encode(), password_hash.encode())


def get_user_by_email(email: str):
    with database.connection_scope() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT user_credentials.id, user_credentials.email,
                       user_credentials.password_hash, user_credentials.role,
                       user_profiles.full_name
                FROM user_credentials
                JOIN user_profiles ON user_profiles.email = user_credentials.email
                WHERE user_credentials.email = %s
                """,
                (email,),
            )
            return cursor.fetchone()


def add_user(user: dict):
    with database.connection_scope() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO user_credentials (email, password_hash, role) VALUES (%s, %s, %s)",
                (user["email"], user["password_hash"], user["role"]),
            )
            cursor.execute(
                "INSERT INTO user_profiles (email, full_name) VALUES (%s, %s)",
                (user["email"], user["full_name"]),
            )

    return user
# ---------- 3. LOGIC (the rules) ----------
def register_user(data: RegisterRequest):
    email = data.email.lower()
    full_name = data.full_name.strip()

    if not full_name:
        raise HTTPException(status_code=400, detail="Full name is required")

    if data.password != data.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    if len(data.password.encode()) > 72:
        raise HTTPException(status_code=400, detail="Password is too long")

    if get_user_by_email(email) is not None:
        raise HTTPException(status_code=400, detail="Email is already registered")

    # The database also blocks a duplicate if two people register at the same time
    try:
        add_user({
            "email": email,
            "password_hash": hash_password(data.password),
            "role": "user",
            "full_name": full_name,
        })
    except pymysql.err.IntegrityError:
        raise HTTPException(status_code=400, detail="Email is already registered")

    return {"email": email, "role": "user", "full_name": full_name}
def login_user(data: LoginRequest):
    user = get_user_by_email(data.email.lower())

    if user is None or not check_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return {"email": user["email"], "role": user["role"], "full_name": user["full_name"]}


def is_admin(email: str):
    user = get_user_by_email(email.lower())
    return user is not None and user["role"] == "admin"
# ---------- 4. ROUTES (the URLs the frontend calls) ----------
@router.post("/register", response_model=UserResponse, status_code=201)
def register_route(data: RegisterRequest):
    return register_user(data)


@router.post("/login", response_model=UserResponse)
def login_route(data: LoginRequest):
    return login_user(data)