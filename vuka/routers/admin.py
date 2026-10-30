from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from vuka.dependency import require_admin
from vuka.schemas.registration import RegistrationResponse, RegistrationUpdate
from vuka.services import registration as registration_service
from vuka.services.admin import AdminService

router = APIRouter(tags=["Admin"])


class BootstrapAdminRequest(BaseModel):
    user_id: int
    bootstrap_key: str


class RoleChangeRequest(BaseModel):
    user_type: str


def get_admin_service(db: Session = Depends(get_db)):
    return AdminService(db)


@router.post("/bootstrap", response_model=RegistrationResponse)
def bootstrap_admin(
    payload: BootstrapAdminRequest,
    service: AdminService = Depends(get_admin_service),
):
    return service.bootstrap_admin(payload.user_id, payload.bootstrap_key)


@router.get("/users", response_model=list[RegistrationResponse])
def get_users(
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    return registration_service.get_registrations(db)


@router.get("/users/{user_id}", response_model=RegistrationResponse)
def get_user(
    user_id: int,
    service: AdminService = Depends(get_admin_service),
    current_user=Depends(require_admin),
):
    return service.get_user(user_id)


@router.patch("/users/{user_id}", response_model=RegistrationResponse)
def update_user(
    user_id: int,
    registration: RegistrationUpdate,
    service: AdminService = Depends(get_admin_service),
    current_user=Depends(require_admin),
):
    return service.update_user(
        user_id,
        registration,
        current_user.user_id,
    )


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    service: AdminService = Depends(get_admin_service),
    current_user=Depends(require_admin),
):
    return service.delete_user(user_id)
