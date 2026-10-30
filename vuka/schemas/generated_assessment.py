import json
from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from vuka.models.enums import CategoryEnum


class QuizQuestion(BaseModel):
    question: str
    options: list[str] = Field(..., min_length=4, max_length=4)
    correct_index: int = Field(..., ge=0, le=3)
    explanation: str

    @field_validator("correct_index")
    @classmethod
    def validate_index(cls, v: int, info):
        options = info.data.get("options")
        if options is not None and not (0 <= v < len(options)):
            raise ValueError("correct_index must point at one of the provided options")
        return v


class PublicQuizQuestion(BaseModel):
    question: str
    options: list[str] = Field(..., min_length=4, max_length=4)


class GenerateAssessmentRequest(BaseModel):
    num_questions: int = Field(10, ge=10, le=10)
    category: CategoryEnum | None = None


class GeneratedAssessmentResponse(BaseModel):
    assessment_id: int
    content_id: int
    category: str
    questions: list[PublicQuizQuestion]
    model_used: str
    generated_at: datetime
    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def parse_questions_json(cls, data):
        questions = (
            getattr(data, "questions", None)
            if not isinstance(data, dict)
            else data.get("questions")
        )
        if isinstance(questions, str):
            parsed = json.loads(questions)
            if isinstance(data, dict):
                data = {**data, "questions": parsed}
            else:
                data = {
                    "assessment_id": data.assessment_id,
                    "content_id": data.content_id,
                    "category": data.category,
                    "questions": parsed,
                    "model_used": data.model_used,
                    "generated_at": data.generated_at,
                }
        return data


class GenerateAllResult(BaseModel):
    generated: list[GeneratedAssessmentResponse]
    skipped_existing: list[int]
    failed: list[dict]
    message: str
