# auth.py  — owner: Usmaan
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/auth", tags=["auth"])

# ---------- 1. MODELS (what data looks like + validation) ----------

# ---------- 2. DATA (fake database for now) ----------

# ---------- 3. LOGIC (the rules) ----------

# ---------- 4. ROUTES (the URLs the frontend calls) ----------
