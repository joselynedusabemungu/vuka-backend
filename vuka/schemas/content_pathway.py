from datetime import date as date_type, datetime
from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class ContentPathwayCreate(BaseModel):
    content_id: int = Field(..., gt=0)
    external_media_url: HttpUrl
    media_description: str = Field(..., min_length=1, max_length=2000)
    date: date_type | None = None


class ContentPathwayUpdate(BaseModel):
    external_media_url: HttpUrl | None = None
    media_description: str | None = Field(None, min_length=1, max_length=2000)
    date: date_type | None = None


class ContentPathwayResponse(BaseModel):
    content_pathway_id: int
    content_id: int
    onboarding_id: int
    external_media_url: str
    media_description: str
    date: date_type
    watched: bool = False
    watched_at: datetime | None = None
    relevance_score: int | None = None
    relevance_reason: str | None = None
    model_config = ConfigDict(from_attributes=True)


class RecommendedContentResponse(ContentPathwayResponse):
    source_platform: str
    relevance_score: int | None = None
    relevance_reason: str | None = None
    generated_assessment_id: int | None = None
