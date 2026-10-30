from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from vuka.dependency import get_current_user
from vuka.models.registration import Registration
from vuka.schemas.generated_assessment import (
    GenerateAllResult,
    GenerateAssessmentRequest,
    GeneratedAssessmentResponse,
)
from vuka.services.generated_assessment import GeneratedAssessmentService

router = APIRouter(prefix="/content-assessments", tags=["Generated Assessments"])


def get_service(db: Session = Depends(get_db)) -> GeneratedAssessmentService:
    return GeneratedAssessmentService(db)


def public_response(record, service: GeneratedAssessmentService):
    questions = service.parse_questions(record)
    return {
        "assessment_id": record.assessment_id,
        "content_id": record.content_id,
        "category": record.category,
        "questions": [{"question": q["question"], "options": q["options"]} for q in questions],
        "model_used": record.model_used,
        "generated_at": record.generated_at,
    }


@router.post("/generate/{content_id}", response_model=GeneratedAssessmentResponse)
def generate_assessment(
    content_id: int,
    payload: GenerateAssessmentRequest = GenerateAssessmentRequest(),
    service: GeneratedAssessmentService = Depends(get_service),
    current_user: Registration = Depends(get_current_user),
):
    service.assert_user_can_access_content(current_user.user_id, content_id)
    record = service.generate_for_content(content_id, payload.num_questions, payload.category)
    return public_response(record, service)


@router.post("/generate-all", response_model=GenerateAllResult)
def generate_all(
    num_questions: int = Query(10, ge=10, le=10),
    skip_existing: bool = True,
    service: GeneratedAssessmentService = Depends(get_service),
    current_user: Registration = Depends(get_current_user),
):
    return service.generate_for_all(num_questions, skip_existing)


@router.get("", response_model=list[GeneratedAssessmentResponse])
def list_generated(
    skip: int = 0,
    limit: int = 100,
    service: GeneratedAssessmentService = Depends(get_service),
    current_user: Registration = Depends(get_current_user),
):
    records = service.list_for_user(current_user.user_id, skip, limit)
    return [public_response(r, service) for r in records]


@router.get("/{content_id}", response_model=GeneratedAssessmentResponse)
def get_generated(
    content_id: int,
    service: GeneratedAssessmentService = Depends(get_service),
    current_user: Registration = Depends(get_current_user),
):
    service.assert_user_can_access_content(current_user.user_id, content_id)
    return public_response(service.get_by_content_id(content_id), service)