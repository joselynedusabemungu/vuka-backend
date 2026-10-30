from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from database import get_db
from vuka.dependency import get_current_user, require_verifier
from vuka.models.registration import Registration
from vuka.schemas.verification import (
    VerificationResponse,
    VerificationReview,
)
from vuka.services.verification import VerificationService

router = APIRouter(
    prefix="/graduate-verification",
    tags=["Graduate Verification"],
)


def get_service(
    db: Session = Depends(get_db),
) -> VerificationService:
    return VerificationService(db)


@router.post(
    "/documents",
    response_model=VerificationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(...),
    current_user: Registration = Depends(get_current_user),
    service: VerificationService = Depends(get_service),
):
    data = await file.read()

    return service.upload_document(
        user_id=current_user.user_id,
        filename=file.filename or "",
        content_type=file.content_type,
        data=data,
    )


@router.get(
    "/me",
    response_model=list[VerificationResponse],
)
def my_documents(
    current_user: Registration = Depends(get_current_user),
    service: VerificationService = Depends(get_service),
):
    return service.get_my_documents(current_user.user_id)


@router.get(
    "/pending",
    response_model=list[VerificationResponse],
)
def pending_documents(
    current_user: Registration = Depends(require_verifier),
    service: VerificationService = Depends(get_service),
):
    return service.get_pending_documents()


@router.patch(
    "/documents/{document_id}",
    response_model=VerificationResponse,
)
def review_document(
    document_id: int,
    payload: VerificationReview,
    current_user: Registration = Depends(require_verifier),
    service: VerificationService = Depends(get_service),
):
    return service.review_document(
        document_id=document_id,
        reviewer_id=current_user.user_id,
        review_status=payload.status,
        rejection_reason=payload.rejection_reason,
    )
