import hashlib

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field

router = APIRouter(prefix="/api/auth", tags=["auth"])

# ---------- 1. MODELS (what data looks like + validation) ----------
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=64)
    confirm_password: str = Field(..., min_length=8, max_length=64)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=64)


class UserResponse(BaseModel):
    email: str
    role: str
# ---------- 2. DATA (fake database for now) ----------
def hash_password(password: str):
    return hashlib.sha256(password.encode()).hexdigest()


users = [
    {"email": "admin@queuesmart.com", "password_hash": hash_password("admin1234"), "role": "admin"},
    {"email": "user@queuesmart.com", "password_hash": hash_password("user1234"), "role": "user"},
]


def get_user_by_email(email: str):
    for user in users:
        if user["email"] == email:
            return user

    return None


def add_user(user: dict):
    users.append(user)
    return user
# ---------- 3. LOGIC (the rules) ----------
def register_user(data: RegisterRequest):
    email = data.email.lower()

    if data.password != data.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    if get_user_by_email(email) is not None:
        raise HTTPException(status_code=400, detail="Email is already registered")

    add_user({
        "email": email,
        "password_hash": hash_password(data.password),
        "role": "user",
    })

    return {"email": email, "role": "user"}
def login_user(data: LoginRequest):
    user = get_user_by_email(data.email.lower())

    if user is None or user["password_hash"] != hash_password(data.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return {"email": user["email"], "role": user["role"]}


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