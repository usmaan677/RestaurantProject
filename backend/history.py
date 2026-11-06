from fastapi import APIRouter
from pydantic import BaseModel, Field

import auth
import database

router = APIRouter(prefix="/api/history", tags=["history"])

# ---------- 1. MODELS (what data looks like + validation) ----------

# ---------- 2. DATA (MySQL database) ----------

def add_history_entry(email: str, service_id: int, service_name: str, outcome: str):
    email = email.lower()
    user = auth.get_user_by_email(email)

    if user is None:
        return None

    with database.connection_scope() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO queue_history (user_id, service_id, service_name, outcome)
                VALUES (%s, %s, %s, %s)
                """,
                (user["id"], service_id, service_name, outcome),
            )
            return {
                "id": cursor.lastrowid,
                "email": email,
                "service_id": service_id,
                "service_name": service_name,
                "outcome": outcome,
            }


def get_history_for_email(email: str):
    with database.connection_scope() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT queue_history.id, user_credentials.email, queue_history.service_id,
                       queue_history.service_name, queue_history.created_at, queue_history.outcome
                FROM queue_history
                JOIN user_credentials ON user_credentials.id = queue_history.user_id
                WHERE user_credentials.email = %s
                ORDER BY queue_history.id DESC
                """,
                (email.lower(),),
            )
            rows = cursor.fetchall()

    return [
        {
            "id": row["id"],
            "email": row["email"],
            "service_id": row["service_id"],
            "service_name": row["service_name"],
            "date": row["created_at"].date().isoformat(),
            "outcome": row["outcome"],
        }
        for row in rows
    ]

# ---------- 3. LOGIC (the rules) ----------

# ---------- 4. ROUTES (the URLs the frontend calls) ----------

@router.get("")
def get_history_route(email: str):
    return get_history_for_email(email)
