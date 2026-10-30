from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from vuka.dependency import get_current_user, require_admin
from vuka.models.registration import Registration
from vuka.schemas.onboarding import (
    OnboardingCreate,
    OnboardingResponse,
    OnboardingUpdate,
)
from vuka.services import onboarding as onboarding_service

router = APIRouter(tags=["Onboarding"])


@router.post("/", response_model=OnboardingResponse, status_code=status.HTTP_200_OK)
def save_onboarding(
    payload: OnboardingCreate,
    db: Session = Depends(get_db),
    current_user: Registration = Depends(get_current_user),
):
    return onboarding_service.create_onboarding(db, current_user.user_id, payload)


@router.get("/me", response_model=OnboardingResponse)
def get_my_onboarding(
    db: Session = Depends(get_db),
    current_user: Registration = Depends(get_current_user),
):
    return onboarding_service.get_my_onboarding(db, current_user.user_id)


@router.get("/", response_model=list[OnboardingResponse])
def get_onboardings(
    db: Session = Depends(get_db),
    current_user: Registration = Depends(require_admin),
):
    return onboarding_service.list_all_onboardings(db)


@router.get("/{onboarding_id}", response_model=OnboardingResponse)
def get_onboarding(
    onboarding_id: int,
    db: Session = Depends(get_db),
    current_user: Registration = Depends(get_current_user),
):
    return onboarding_service.get_user_onboarding(db, onboarding_id, current_user)


@router.patch("/{onboarding_id}", response_model=OnboardingResponse)
def update_onboarding(
    onboarding_id: int,
    payload: OnboardingUpdate,
    db: Session = Depends(get_db),
    current_user: Registration = Depends(get_current_user),
):
    return onboarding_service.update_user_onboarding(
        db, onboarding_id, current_user, payload
    )
