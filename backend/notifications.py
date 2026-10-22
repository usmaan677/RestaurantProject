from datetime import datetime

from fastapi import APIRouter

router = APIRouter(prefix="/api/notifications", tags=["notifications"])

# ---------- 1. MODELS (what data looks like + validation) ----------
# Nothing needed: notifications are created by the backend, not sent in by the user.

# ---------- 2. DATA (fake database for now) ----------

notifications = []
next_notification_id = 1


# ---------- 3. LOGIC (the rules) ----------

def add_notification(email: int, message: str):
    global next_notification_id

    notification = {
        "id": next_notification_id,
        "email": email.lower(),
        "message": message,
        "time": datetime.now().strftime("%I:%M %p"),
    }

    notifications.append(notification)
    next_notification_id += 1

    return notification


def get_notifications(email: str):
    email = email.lower()
    return [n for n in notifications if n["email"] == email]


def has_notification(email: str, message: str) -> bool:
    # used so we don't send the same "you're almos
    for n in notifications:
        if n["email"] == email.lower() and n["message"] == message:
            return True

    return False


# ---------- 4. ROUTES (the URLs the frontend call

@router.get("/{email}")
def get_notifications_route(email: str):
    return get_notifications(email)

