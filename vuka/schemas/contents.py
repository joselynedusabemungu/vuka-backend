from __future__ import annotations

from datetime import datetime as datetime_type
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class ContentBase(BaseModel):
    external_media_url: HttpUrl
    source_platform: str
    media_description: str = ""
    datetime: datetime_type


class ContentCreate(ContentBase):
    pass

class ContentUpdate(BaseModel):
    external_media_url: HttpUrl | None = None
    source_platform: str | None = None
    media_description: str | None = Field(None, min_length=1, max_length=2000)
    datetime: datetime_type | None = None

class ContentResponse(ContentBase):
    content_id: int
    model_config = ConfigDict(from_attributes=True)

class PipelineQuerySchema(BaseModel):

    keyword: str = Field(..., min_length=1, max_length=200)
    platforms: list[str] = Field(
        default_factory=lambda: ["youtube", "tiktok", "instagram"],
        min_length=1,
    )
    max_results: int = Field(default=10, ge=1, le=50)
    quiz_category: int | None = Field(default=None, ge=1)
    quiz_difficulty: Literal["easy", "medium", "hard"] = "medium"

    @field_validator("keyword")
    @classmethod
    def normalize_keyword(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if not normalized:
            raise ValueError("keyword must contain at least one non-space character")
        return normalized

    @field_validator("platforms")
    @classmethod
    def validate_platforms(cls, value: list[str]) -> list[str]:
        allowed = {"youtube", "tiktok", "instagram"}
        normalized = [platform.strip().lower() for platform in value]
        invalid = sorted(set(normalized) - allowed)

        if invalid:
            raise ValueError(
                "Unsupported platforms: " + ", ".join(invalid)
            )

        return list(dict.fromkeys(normalized))

class SocialContentItem(BaseModel):
    platform: str
    title: str
    url: HttpUrl
    description: str

class QuizQuestion(BaseModel):
    category: str
    difficulty: str
    question: str
    correct_answer: str
    incorrect_answers: list[str]

class EducationPipeline(BaseModel):
    category: int | None
    difficulty: str
    questions: list[QuizQuestion]

class OpportunityItem(BaseModel):
    title: str
    url: HttpUrl
    description: str

class PipelineResponseSchema(BaseModel):
    keyword: str
    social: dict[str, list[SocialContentItem]]
    education: EducationPipeline
    opportunities: list[OpportunityItem]
    errors: list[str] = Field(default_factory=list)