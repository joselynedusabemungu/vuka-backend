from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from vuka.dependency import get_current_user, require_admin
from vuka.models.registration import Registration
from vuka.schemas.userprogress import UserProgressResponse, ProgressSummary
from vuka.services.userprogress import UserProgressService


router = APIRouter(prefix="/user-progress", tags=["User Progress"])


@router.get("/me", response_model=list[UserProgressResponse])
def get_my_progress(
    db: Session = Depends(get_db),
    current_user: Registration = Depends(get_current_user),
):
    return UserProgressService(db).list_by_user(current_user.user_id)


@router.get("/summary", response_model=ProgressSummary)
def get_my_progress_summary(
    db: Session = Depends(get_db),
    current_user: Registration = Depends(get_current_user),
):
    return UserProgressService(db).get_summary(current_user.user_id)


@router.get("/", response_model=list[UserProgressResponse])
def get_all_progress_records(
    db: Session = Depends(get_db),
    current_user: Registration = Depends(require_admin),
):
    return UserProgressService(db).list_all()


@router.get("/{progress_id}", response_model=UserProgressResponse)
def get_one_progress_record(
    progress_id: int,
    db: Session = Depends(get_db),
    current_user: Registration = Depends(get_current_user),
):
    return UserProgressService(db).get_for_user(
        progress_id=progress_id,
        user_id=current_user.user_id,
        user_type=current_user.user_type,
    )
