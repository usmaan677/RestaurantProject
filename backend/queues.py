from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field

import auth
import history
import services

router = APIRouter(prefix="/api/queues", tags=["queues"])

# ---------- 1. MODELS (what data looks like + validation) ----------

class QueueJoin(BaseModel):
    email: EmailStr
    service_id: int = Field(..., gt=0)
    priority: int = Field(1, ge=1, le=5)

class QueueLeave(BaseModel):
    email: EmailStr
    service_id: int = Field(..., gt=0)

class AdminQueueAction(BaseModel):
    email: EmailStr


# ---------- 2. DATA (fake database for now) ----------

queue_entries = []
next_entry_id = 1


# ---------- 3. LOGIC (the rules) ----------

def get_queue_for_service(service_id: int):
    entries = [e for e in queue_entries if e["service_id"] == service_id]
    # higher priority first, then earlier arrival (smaller id) first
    return sorted(entries, key=lambda e: (-e["priority"], e["id"]))


def get_position(service_id: int, email: str):
    email = email.lower()
    ordered = get_queue_for_service(service_id)

    for index, entry in enumerate(ordered):
        if entry["email"] == email:
            return index + 1

    return None


def calculate_wait(service_id: int, position: int):
    service = services.get_service(service_id)

    return position * service["expected_duration"]


def is_user_in_queue(service_id: int, email: str) -> bool:
    email = email.lower()

    for entry in queue_entries:
        if entry["service_id"] == service_id and entry["email"] == email:
            return True

    return False


def build_status(service_id: int, email: str):
    email = email.lower()
    position = get_position(service_id, email)

    for entry in queue_entries:
        if entry["service_id"] == service_id and entry["email"] == email:
            return {
                "id": entry["id"],
                "service_id": entry["service_id"],
                "email": entry["email"],
                "priority": entry["priority"],
                "position": position,
                "estimated_wait": calculate_wait(service_id, position),
            }

    return None


def join_queue(join_data: QueueJoin):
    global next_entry_id

    entry = {
        "id": next_entry_id,
        "service_id": join_data.service_id,
        "email": join_data.email.lower(),
        "priority": join_data.priority,
    }

    queue_entries.append(entry)
    next_entry_id += 1

    return build_status(entry["service_id"], entry["email"])


def leave_queue(leave_data: QueueLeave):
    email = leave_data.email.lower()

    for entry in queue_entries:
        if entry["service_id"] == leave_data.service_id and entry["email"] == email:
            queue_entries.remove(entry)
            return entry

    return None


def get_entries_for_email(email: str):
    email = email.lower()
    return [e for e in queue_entries if e["email"] == email]


def get_queue_count(service_id: int):
    return len(get_queue_for_service(service_id))


def serve_next(service_id: int):
    ordered = get_queue_for_service(service_id)

    if not ordered:
        return None

    entry = ordered[0]
    queue_entries.remove(entry)
    return entry


# ---------- 4. ROUTES (the URLs the frontend calls) ----------

@router.post("/join")
def join_queue_route(join_data: QueueJoin):
    service = services.get_service(join_data.service_id)

    if service is None:
        raise HTTPException(status_code=404, detail="Service not found")

    if is_user_in_queue(join_data.service_id, join_data.email):
        raise HTTPException(status_code=400, detail="User already in queue for this service")

    entry = join_queue(join_data)
    history.add_history_entry(join_data.email, join_data.service_id, service["name"], "Joined Queue")

    return entry


@router.post("/leave")
def leave_queue_route(leave_data: QueueLeave):
    service = services.get_service(leave_data.service_id)

    if service is None:
        raise HTTPException(status_code=404, detail="Service not found")

    if not is_user_in_queue(leave_data.service_id, leave_data.email):
        raise HTTPException(status_code=404, detail="User not in queue for this service")

    entry = leave_queue(leave_data)
    history.add_history_entry(leave_data.email, leave_data.service_id, service["name"], "Left Queue")

    return entry


@router.get("/{service_id}/position/{email}")
def get_position_route(service_id: int, email: str):
    service = services.get_service(service_id)

    if service is None:
        raise HTTPException(status_code=404, detail="Service not found")

    if not is_user_in_queue(service_id, email):
        raise HTTPException(status_code=404, detail="User not in queue for this service")

    return build_status(service_id, email)


@router.get("/mine")
def get_my_queues_route(email: str):
    entries = get_entries_for_email(email)
    return [build_status(entry["service_id"], entry["email"]) for entry in entries]


@router.get("/{service_id}/admin")
def get_admin_queue_route(service_id: int, email: EmailStr):
    if not auth.is_admin(str(email)):
        raise HTTPException(status_code=403, detail="Administrator access required")

    service = services.get_service(service_id)
    if service is None:
        raise HTTPException(status_code=404, detail="Service not found")

    return [
        {
            **entry,
            "position": position,
            "estimated_wait": calculate_wait(service_id, position),
        }
        for position, entry in enumerate(get_queue_for_service(service_id), start=1)
    ]


@router.post("/{service_id}/serve-next")
def serve_next_route(service_id: int, action: AdminQueueAction):
    if not auth.is_admin(str(action.email)):
        raise HTTPException(status_code=403, detail="Administrator access required")

    service = services.get_service(service_id)
    if service is None:
        raise HTTPException(status_code=404, detail="Service not found")

    entry = serve_next(service_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Queue is empty")

    history.add_history_entry(entry["email"], service_id, service["name"], "Served")
    return entry


@router.get("/{service_id}/count")
def get_queue_count_route(service_id: int):
    service = services.get_service(service_id)

    if service is None:
        raise HTTPException(status_code=404, detail="Service not found")

    return {"service_id": service_id, "count": get_queue_count(service_id)}
