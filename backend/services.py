
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, EmailStr

import database
import auth

router = APIRouter(prefix="/api/services", tags=["services"])


# ---------- 1. MODELS (what data looks like + validation) ----------

class ServiceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., max_length=500)
    expected_duration: int = Field(..., gt=0)
    priority: int = Field(..., ge=1, le=5)


class ServiceUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    expected_duration: int | None = Field(None, gt=0)
    priority: int | None = Field(None, ge=1, le=5)


# ---------- 2. DATABASE OPERATIONS ----------

def create_service(service_data: ServiceCreate):
    with database.connection_scope() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO services
                (name, description, expected_duration, priority)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    service_data.name,
                    service_data.description,
                    service_data.expected_duration,
                    service_data.priority
                )
            )

            service_id = cursor.lastrowid

            cursor.execute(
                "SELECT * FROM services WHERE id = %s",
                (service_id,)
            )

            return cursor.fetchone()


def get_service(service_id: int):
    with database.connection_scope() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM services WHERE id = %s",
                (service_id,)
            )

            return cursor.fetchone()


def list_services():
    with database.connection_scope() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM services ORDER BY id")

            return cursor.fetchall()


def update_service(service_id: int, service_data: ServiceUpdate):
    updated_data = service_data.model_dump(exclude_unset=True)

    # Check whether the service exists.
    service = get_service(service_id)

    if service is None:
        return None

    # Nothing to update.
    if not updated_data:
        return service

    # Build the UPDATE statement using the supplied fields.
    fields = ", ".join(
        f"{field} = %s" for field in updated_data
    )

    values = list(updated_data.values())
    values.append(service_id)

    with database.connection_scope() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                f"UPDATE services SET {fields} WHERE id = %s",
                values
            )

            cursor.execute(
                "SELECT * FROM services WHERE id = %s",
                (service_id,)
            )

            return cursor.fetchone()


# ---------- 3. ROUTES (the URLs the frontend calls) ----------

@router.post("/")
def create_service_route(
    service_data: ServiceCreate,
    email: EmailStr
):
    if not auth.is_admin(str(email)):
        raise HTTPException(
            status_code=403,
            detail="Administrator access required"
        )

    return create_service(service_data)


@router.get("/")
def list_services_route():
    return list_services()


@router.get("/{service_id}")
def get_service_route(service_id: int):
    service = get_service(service_id)

    if service is None:
        raise HTTPException(
            status_code=404,
            detail="Service not found"
        )

    return service


@router.put("/{service_id}")
def update_service_route(
    service_id: int,
    service_data: ServiceUpdate,
    email: EmailStr
):
    if not auth.is_admin(str(email)):
        raise HTTPException(
            status_code=403,
            detail="Administrator access required"
        )

    service = update_service(service_id, service_data)

    if service is None:
        raise HTTPException(
            status_code=404,
            detail="Service not found"
        )

    return service
