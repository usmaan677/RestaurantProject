from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

import services

router = APIRouter(prefix="/api/queues", tags=["queues"])

# ---------- 1. MODELS (what data looks like + validation) ----------

class QueueJoin(BaseModel):
    user_id: int = Field(..., gt=0)
    service_id: int = Field(..., gt=0)
    priority: int = Field(1, ge=1, le=5)

class QueueLeave(BaseModel):
    user_id: int = Field(..., gt=0)
    service_id: int = Field(..., gt=0)


# ---------- 2. DATA (fake database for now) ----------

queue_entries = []
next_entry_id = 1


# ---------- 3. LOGIC (the rules) ----------

def get_queue_for_service(service_id: int):
    entries = [e for e in queue_entries if e["service_id"] == service_id]
    # higher priority first, then earlier arrival (smaller id) first
    return sorted(entries, key=lambda e: (-e["priority"], e["id"]))


def get_position(service_id: int, user_id: int):
    ordered = get_queue_for_service(service_id)

    for index, entry in enumerate(ordered):
        if entry["user_id"] == user_id:
            return index + 1

    return None


def calculate_wait(service_id: int, position: int):
    service = services.get_service(service_id)
    people_ahead = position - 1

    return people_ahead * service["expected_duration"]


def is_user_in_queue(service_id: int, user_id: int) -> bool:
    for entry in queue_entries:
        if entry["service_id"] == service_id and entry["user_id"] == user_id:
            return True

    return False


def build_status(service_id: int, user_id: int):
    position = get_position(service_id, user_id)

    for entry in queue_entries:
        if entry["service_id"] == service_id and entry["user_id"] == user_id:
            return {
                "id": entry["id"],
                "service_id": entry["service_id"],
                "user_id": entry["user_id"],
                "priority": entry["priority"],
                "position": position,
                "estimated_wait": calculate_wait(service_id, position),
            }

    return None


def join_queue(join_data: QueueJoin):
    global next_entry_id

    entry = join_data.model_dump()
    entry["id"] = next_entry_id

    queue_entries.append(entry)
    next_entry_id += 1

    return build_status(join_data.service_id, join_data.user_id)


def leave_queue(leave_data: QueueLeave):
    for entry in queue_entries:
        if entry["service_id"] == leave_data.service_id and entry["user_id"] == leave_data.user_id:
            queue_entries.remove(entry)
            return entry

    return None


# ---------- 4. ROUTES (the URLs the frontend calls) ----------

@router.post("/join")
def join_queue_route(join_data: QueueJoin):
    service = services.get_service(join_data.service_id)

    if service is None:
        raise HTTPException(status_code=404, detail="Service not found")

    if is_user_in_queue(join_data.service_id, join_data.user_id):
        raise HTTPException(status_code=400, detail="User already in queue for this service")

    return join_queue(join_data)


@router.post("/leave")
def leave_queue_route(leave_data: QueueLeave):
    service = services.get_service(leave_data.service_id)

    if service is None:
        raise HTTPException(status_code=404, detail="Service not found")

    if not is_user_in_queue(leave_data.service_id, leave_data.user_id):
        raise HTTPException(status_code=404, detail="User not in queue for this service")

    return leave_queue(leave_data)


@router.get("/{service_id}/position/{user_id}")
def get_position_route(service_id: int, user_id: int):
    service = services.get_service(service_id)

    if service is None:
        raise HTTPException(status_code=404, detail="Service not found")

    if not is_user_in_queue(service_id, user_id):
        raise HTTPException(status_code=404, detail="User not in queue for this service")

    return build_status(service_id, user_id)
