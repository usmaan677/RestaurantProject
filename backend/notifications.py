from fastapi import APIRouter

import auth
import database

router = APIRouter(prefix="/api/notifications", tags=["notifications"])

# ---------- 1. MODELS (what data looks like + validation) ----------
# Nothing needed: notifications are created by the backend, not sent in by the user.

# ---------- 2. DATA (MySQL database) ----------

def add_notification(email: str, message: str):
    email = email.lower()
    user = auth.get_user_by_email(email)

    if user is None:
        return None

    with database.connection_scope() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO notifications (user_id, message) VALUES (%s, %s)",
                (user["id"], message),
            )
            return {
                "id": cursor.lastrowid,
                "email": email,
                "message": message,
                "status": "sent",
            }


def get_notifications(email: str):
    with database.connection_scope() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT notifications.id, user_credentials.email, notifications.message,
                       notifications.created_at, notifications.status
                FROM notifications
                JOIN user_credentials ON user_credentials.id = notifications.user_id
                WHERE user_credentials.email = %s
                ORDER BY notifications.id
                """,
                (email.lower(),),
            )
            rows = cursor.fetchall()

    return [
        {
            "id": row["id"],
            "email": row["email"],
            "message": row["message"],
            "time": row["created_at"].strftime("%b %d, %I:%M %p"),
            "status": row["status"],
        }
        for row in rows
    ]


def mark_notifications_viewed(email: str):
    with database.connection_scope() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE notifications
                SET status = 'viewed'
                WHERE status = 'sent'
                AND user_id = (SELECT id FROM user_credentials WHERE email = %s)
                """,
                (email.lower(),),
            )


# ---------- 3. LOGIC (the rules) ----------

def has_notification(email: str, message: str, joined_message: str) -> bool:
    # Newest to oldest: stop at their last join so a new visit can notify them again
    for note in reversed(get_notifications(email)):
        if note["message"] == message:
            return True

        if note["message"].startswith(joined_message):
            return False

    return False


# ---------- 4. ROUTES (the URLs the frontend calls) ----------

@router.get("/{email}")
def get_notifications_route(email: str):
    return get_notifications(email)


@router.post("/{email}/viewed")
def mark_notifications_viewed_route(email: str):
    mark_notifications_viewed(email)
    return get_notifications(email)
