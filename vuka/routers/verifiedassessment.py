import logging

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from database import SessionLocal, get_db
from vuka.dependency import get_current_user
from vuka.models.registration import Registration
from vuka.schemas.verifiedassessment import (
    AssessmentProgressUpdate,
    AssessmentSubmission,
    VerifiedAssessmentResponse,
)
from vuka.services.verifiedassessment import VerifiedAssessmentService

logger = logging.getLogger("vuka.verifiedassessment")

router = APIRouter(prefix="/verified-assessment", tags=["Verified Assessment"])


def get_service(db: Session = Depends(get_db)):
    return VerifiedAssessmentService(db)


@router.post(
    "/start/{generated_assessment_id}", response_model=VerifiedAssessmentResponse
)
def start_assessment(
    generated_assessment_id: int,
    db: Session = Depends(get_db),
    current_user: Registration = Depends(get_current_user),
):
    return get_service(db).start(current_user.user_id, generated_assessment_id)


@router.get(
    "/resume/{generated_assessment_id}",
    response_model=VerifiedAssessmentResponse | None,
)
def resume_assessment(
    generated_assessment_id: int,
    db: Session = Depends(get_db),
    current_user: Registration = Depends(get_current_user),
):
    return get_service(db).get_resume(current_user.user_id, generated_assessment_id)


@router.patch("/{assessment_id}/progress", response_model=VerifiedAssessmentResponse)
def save_progress(
    assessment_id: int,
    payload: AssessmentProgressUpdate,
    db: Session = Depends(get_db),
    current_user: Registration = Depends(get_current_user),
):
    return get_service(db).save_progress(assessment_id, current_user.user_id, payload)


def _refresh_opportunities_after_submission(user_id: int) -> None:
    db = SessionLocal()
    try:
        from vuka.services.opportunity_recommendation import (
            OpportunityRecommendationService,
        )

        OpportunityRecommendationService(db).refresh_for_user(user_id)
    except Exception as exc:
        logger.warning(
            "Background opportunity refresh failed for user_id=%s: %s",
            user_id,
            exc,
        )
        db.rollback()
    finally:
        db.close()


@router.post("/{assessment_id}/submit", response_model=dict)
def submit_assessment(
    assessment_id: int,
    payload: AssessmentSubmission,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: Registration = Depends(get_current_user),
):
    result = get_service(db).submit(assessment_id, current_user.user_id, payload)
    if result.get("status") == "completed" and result.get("progress_id"):
        background_tasks.add_task(
            _refresh_opportunities_after_submission, current_user.user_id
        )
    return result


@router.get("/me", response_model=list[VerifiedAssessmentResponse])
def get_my_assessments(
    db: Session = Depends(get_db),
    current_user: Registration = Depends(get_current_user),
):
    return get_service(db).list_for_user(current_user.user_id)


@router.get("/{assessment_id}", response_model=VerifiedAssessmentResponse)
def get_assessment(
    assessment_id: int,
    db: Session = Depends(get_db),
    current_user: Registration = Depends(get_current_user),
):
    return get_service(db).get_for_user(assessment_id, current_user.user_id)
