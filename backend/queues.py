from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/queues", tags=["queues"])

# ---------- 1. MODELS (what data looks like + validation) ----------

# ---------- 2. DATA (fake database for now) ----------

# ---------- 3. LOGIC (the rules) ----------

# ---------- 4. ROUTES (the URLs the frontend calls) ----------