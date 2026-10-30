from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AssessmentStatus(str, Enum):
    in_progress = "in_progress"
    completed = "completed"


class VerifiedAssessmentCreate(BaseModel):
    user_id: int
    category: str
    score: int = Field(0, ge=0, le=100)


class AnswerInput(BaseModel):
    question_index: int = Field(..., ge=0)
    selected_index: int = Field(..., ge=0, le=3)


class AssessmentProgressUpdate(BaseModel):
    answers: list[AnswerInput] = Field(default_factory=list)
    current_step: int = Field(0, ge=0)


class AssessmentSubmission(BaseModel):
    answers: list[AnswerInput] = Field(..., min_length=1)


class VerifiedAssessmentResponse(BaseModel):
    assessment_id: int
    generated_assessment_id: int
    user_id: int
    category: str
    score: int
    status: AssessmentStatus
    answers: dict[str, int]
    current_step: int
    performance_tier: str | None = None
    streak_count: int | None = None
    assessment_date: datetime
    completed_at: datetime | None = None
    questions: list[dict[str, Any]] | None = None

    model_config = {"from_attributes": True}


class VerifiedAssessmentUpdate(BaseModel):
    category: str | None = None
    score: int | None = Field(None, ge=0, le=100)
