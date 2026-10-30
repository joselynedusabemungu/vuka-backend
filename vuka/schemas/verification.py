from datetime import datetime

from pydantic import BaseModel, Field


class VerificationResponse(BaseModel):
    id: int
    user_id: int
    document_reference: str
    document_type: str
    file_size: int
    mime_type: str
    verification_status: str
    rejection_reason: str | None = None
    uploaded_at: datetime
    reviewed_at: datetime | None = None
    reviewed_by: int | None = None
    model_config = {"from_attributes": True}


class VerificationReview(BaseModel):
    status: str = Field(pattern=r"^(VERIFIED|REJECTED|REQUIRES_REVIEW)$")
    rejection_reason: str | None = Field(None, max_length=1000)
