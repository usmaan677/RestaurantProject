from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

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


# ---------- 2. DATA (fake database for now) ----------

services = [{"id": 1, "name": "Dine In", "description": "Sit down and enjoy your meal at the restaurant.", "expected_duration": 20, "priority": 3},
    {"id": 2, "name": "Take Out", "description": "Pick up your order at the front counter.", "expected_duration": 10, "priority": 3},
    {"id": 3, "name": "DoorDash", "description": "Have your order delivered to your door.", "expected_duration": 35, "priority": 3},]
next_service_id = 4


# ---------- 3. LOGIC (the rules) ----------

def create_service(service_data: ServiceCreate):
    global next_service_id
    
    service = service_data.model_dump()
    service["id"] = next_service_id
    
    services.append(service)
    next_service_id += 1
    
    return service

def get_service(service_id: int):
    for service in services:
        if service["id"] == service_id:
            return service
        
    return None


def list_services():
    return services


def update_service(service_id: int, service_data: ServiceUpdate):
    service = get_service(service_id)
    
    if service is None:
        return None
    
    updated_data = service_data.model_dump(exclude_unset=True)
    service.update(updated_data)
    
    return service

# ---------- 4. ROUTES (the URLs the frontend calls) ----------

@router.post("/")
def create_service_route(service_data: ServiceCreate):
    return create_service(service_data)


@router.get("/")
def list_services_route():
    return list_services()


@router.get("/{service_id}")
def get_service_route(service_id: int):
    service = get_service(service_id)
    
    if service is None:
        raise HTTPException(status_code=404, detail="Service not found")
    
    return service



@router.put("/{service_id}")
def update_service_route(service_id: int, service_data: ServiceUpdate):
    service = update_service(service_id, service_data)
    
    if service is None:
        raise HTTPException(status_code=404, detail="Service not found")
    
    return service