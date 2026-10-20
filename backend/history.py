from datetime import date

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/history", tags=["history"])

# ---------- 1. MODELS (what data looks like + validation) ----------

# ---------- 2. DATA (fake database for now) ----------

history_entries = []
next_history_id = 1

# ---------- 3. LOGIC (the rules) ----------

def add_history_entry(email: str, service_id: int, service_name: str, outcome: str):
    global next_history_id

    entry = {
        "id": next_history_id,
        "email": email.lower(),
        "service_id": service_id,
        "service_name": service_name,
        "date": date.today().isoformat(),
        "outcome": outcome,
    }

    history_entries.append(entry)
    next_history_id += 1

    return entry


def get_history_for_email(email: str):
    email = email.lower()
    entries = [e for e in history_entries if e["email"] == email]
    return list(reversed(entries))

# ---------- 4. ROUTES (the URLs the frontend calls) ----------

@router.get("")
def get_history_route(email: str):
    return get_history_for_email(email)