import pymysql
from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel, EmailStr, Field
import notifications

import auth
import database
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


# ---------- 2. DATA (MySQL database) ----------

# Waiting people are served by priority (5 first), then by who joined first (smaller id).
SELECT_QUEUE_ENTRIES = """
    SELECT queue_entries.id, queues.service_id, user_credentials.email,
           queue_entries.priority
    FROM queue_entries
    JOIN queues ON queues.id = queue_entries.queue_id
    JOIN user_credentials ON user_credentials.id = queue_entries.user_id
"""
SERVING_ORDER = "ORDER BY queue_entries.priority DESC, queue_entries.id"


def get_queue_for_service(service_id: int):
    with database.connection_scope() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                SELECT_QUEUE_ENTRIES
                + "WHERE queues.service_id = %s AND queue_entries.status = 'waiting' "
                + SERVING_ORDER,
                (service_id,),
            )
            return list(cursor.fetchall())


def get_entries_for_email(email: str):
    with database.connection_scope() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                SELECT_QUEUE_ENTRIES
                + "WHERE user_credentials.email = %s AND queue_entries.status = 'waiting' "
                + "ORDER BY queue_entries.id",
                (email.lower(),),
            )
            return list(cursor.fetchall())


def lock_service_queues(cursor, service_id: int):
    # Locking the service's queues makes joins, leaves and serves happen one at a time
    cursor.execute(
        "SELECT id, status FROM queues WHERE service_id = %s ORDER BY id DESC FOR UPDATE",
        (service_id,),
    )
    return cursor.fetchall()


def renumber_waiting_entries(cursor, service_id: int):
    # Keeps the saved position column in step with the serving order
    cursor.execute(
        """
        UPDATE queue_entries
        JOIN (
            SELECT queue_entries.id AS entry_id,
                   ROW_NUMBER() OVER (
                       ORDER BY queue_entries.priority DESC, queue_entries.id
                   ) AS new_position
            FROM queue_entries
            JOIN queues ON queues.id = queue_entries.queue_id
            WHERE queues.service_id = %s AND queue_entries.status = 'waiting'
        ) AS ranked ON ranked.entry_id = queue_entries.id
        SET queue_entries.position = ranked.new_position
        """,
        (service_id,),
    )


def add_queue_entry(service_id: int, email: str, priority: int):
    email = email.lower()
    user = auth.get_user_by_email(email)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        with database.connection_scope() as connection:
            with connection.cursor() as cursor:
                open_queue = next(
                    (queue for queue in lock_service_queues(cursor, service_id)
                     if queue["status"] == "open"),
                    None,
                )
                if open_queue is None:
                    raise HTTPException(
                        status_code=409,
                        detail="Queue is not open for this service",
                    )

                cursor.execute(
                    """
                    SELECT COUNT(*) AS waiting
                    FROM queue_entries
                    JOIN queues ON queues.id = queue_entries.queue_id
                    WHERE queues.service_id = %s AND queue_entries.status = 'waiting'
                    """,
                    (service_id,),
                )
                position = cursor.fetchone()["waiting"] + 1

                cursor.execute(
                    """
                    INSERT INTO queue_entries (queue_id, user_id, position, priority)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (open_queue["id"], user["id"], position, priority),
                )
                entry_id = cursor.lastrowid
                renumber_waiting_entries(cursor, service_id)
    except pymysql.err.IntegrityError as exc:
        # 1062 = the database refused a second waiting row for the same user and queue
        if exc.args[0] == 1062:
            raise HTTPException(status_code=400, detail="User already in queue for this service")
        raise

    return {"id": entry_id, "service_id": service_id, "email": email, "priority": priority}


def finish_queue_entry(service_id: int, new_status: str, email: str | None = None):
    # Marks one waiting person as 'served' or 'canceled'. With no email it takes the
    # first person in line. The row stays in the table so there is a record of it.
    with database.connection_scope() as connection:
        with connection.cursor() as cursor:
            lock_service_queues(cursor, service_id)

            query = SELECT_QUEUE_ENTRIES + "WHERE queues.service_id = %s AND queue_entries.status = 'waiting' "
            params = [service_id]
            if email is not None:
                query += "AND user_credentials.email = %s "
                params.append(email.lower())
            cursor.execute(query + SERVING_ORDER + " LIMIT 1", tuple(params))

            entry = cursor.fetchone()
            if entry is None:
                return None

            cursor.execute(
                "UPDATE queue_entries SET status = %s WHERE id = %s",
                (new_status, entry["id"]),
            )
            renumber_waiting_entries(cursor, service_id)
            return entry


# ---------- 3. LOGIC (the rules) ----------

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
    return get_position(service_id, email) is not None


def build_status(service_id: int, email: str):
    email = email.lower()

    for position, entry in enumerate(get_queue_for_service(service_id), start=1):
        if entry["email"] == email:
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
    add_queue_entry(join_data.service_id, join_data.email, join_data.priority)

    status = build_status(join_data.service_id, join_data.email)
    service = services.get_service(join_data.service_id)

    notifications.add_notification(
        join_data.email.lower(),
        f"You joined the {service['name']} queue. You are #{status['position']}.",
    )
    notify_close_users(join_data.service_id)

    return status


def leave_queue(leave_data: QueueLeave):
    entry = finish_queue_entry(leave_data.service_id, "canceled", leave_data.email)

    if entry is not None:
        notify_close_users(leave_data.service_id)  # everyone behind moved up

    return entry


def get_queue_count(service_id: int):
    return len(get_queue_for_service(service_id))

CLOSE_POSITION = 2


def notify_close_users(service_id: int):
    service = services.get_service(service_id)
    ordered = get_queue_for_service(service_id)

    for entry in ordered[:CLOSE_POSITION]:
        message = f"You're almost up for {service['name']}!"
        joined_message = f"You joined the {service['name']} queue"

        if not notifications.has_notification(entry["email"], message, joined_message):
            notifications.add_notification(entry["email"], message)


def serve_next(service_id: int):
    return finish_queue_entry(service_id, "served")


def create_queue_record(service_id: int):
    with database.connection_scope() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM services WHERE id = %s FOR UPDATE",
                (service_id,),
            )
            if cursor.fetchone() is None:
                return None

            cursor.execute(
                """
                SELECT id, service_id, status, created_at
                FROM queues
                WHERE service_id = %s AND status = 'open'
                ORDER BY id DESC
                LIMIT 1
                """,
                (service_id,),
            )
            queue = cursor.fetchone()
            if queue is not None:
                return queue

            cursor.execute(
                "INSERT INTO queues (service_id) VALUES (%s)",
                (service_id,),
            )
            queue_id = cursor.lastrowid
            cursor.execute(
                """
                SELECT id, service_id, status, created_at
                FROM queues
                WHERE id = %s
                """,
                (queue_id,),
            )
            queue = cursor.fetchone()
            if queue is None:
                raise RuntimeError("Created queue could not be retrieved")
            return queue


def get_active_queue(service_id: int):
    with database.connection_scope() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, service_id, status, created_at
                FROM queues
                WHERE service_id = %s AND status = 'open'
                ORDER BY id DESC
                LIMIT 1
                """,
                (service_id,),
            )
            return cursor.fetchone()


def close_queue_record(queue_id: int):
    with database.connection_scope() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, service_id, status, created_at
                FROM queues
                WHERE id = %s
                FOR UPDATE
                """,
                (queue_id,),
            )
            queue = cursor.fetchone()
            if queue is None:
                return None

            if queue["status"] == "open":
                cursor.execute(
                    "UPDATE queues SET status = 'closed' WHERE id = %s",
                    (queue_id,),
                )
                cursor.execute(
                    "UPDATE queue_entries SET status = 'canceled' WHERE queue_id = %s AND status = 'waiting'",
                    (queue_id,),
                )
                cursor.execute(
                    """
                    SELECT id, service_id, status, created_at
                    FROM queues
                    WHERE id = %s
                    """,
                    (queue_id,),
                )
                queue = cursor.fetchone()
                if queue is None:
                    raise RuntimeError("Closed queue could not be retrieved")
            return queue


# ---------- 4. ROUTES (the URLs the frontend calls) ----------

@router.post("/services/{service_id}")
def create_queue_route(action: AdminQueueAction, service_id: int = Path(gt=0)):
    if not auth.is_admin(str(action.email)):
        raise HTTPException(status_code=403, detail="Administrator access required")

    queue = create_queue_record(service_id)
    if queue is None:
        raise HTTPException(status_code=404, detail="Service not found")
    return queue


@router.get("/services/{service_id}/active")
def get_active_queue_route(service_id: int = Path(gt=0)):
    queue = get_active_queue(service_id)
    if queue is None:
        raise HTTPException(status_code=404, detail="No active queue for service")
    return queue


@router.post("/{queue_id}/close")
def close_queue_route(action: AdminQueueAction, queue_id: int = Path(gt=0)):
    if not auth.is_admin(str(action.email)):
        raise HTTPException(status_code=403, detail="Administrator access required")

    queue = close_queue_record(queue_id)
    if queue is None:
        raise HTTPException(status_code=404, detail="Queue not found")
    return queue


@router.post("/join")
def join_queue_route(join_data: QueueJoin):
    service = services.get_service(join_data.service_id)

    if service is None:
        raise HTTPException(status_code=404, detail="Service not found")

    if get_active_queue(join_data.service_id) is None:
        raise HTTPException(
            status_code=409,
            detail="Queue is not open for this service",
        )

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
    notify_close_users(service_id)
    return entry


@router.get("/{service_id}/count")
def get_queue_count_route(service_id: int):
    service = services.get_service(service_id)

    if service is None:
        raise HTTPException(status_code=404, detail="Service not found")

    return {"service_id": service_id, "count": get_queue_count(service_id)}
