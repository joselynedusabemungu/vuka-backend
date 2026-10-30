from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from vuka.models.enums import SubjectFieldEnum


class OpportunityRecommendationBase(BaseModel):

    user_id: int | None = None

    progress_id: int | None = None

    subject_field: SubjectFieldEnum

    external_media_url: str

    source_platform: str = Field(
        ...,
        max_length=100,
    )

    media_description: str

    opportunity_date: datetime

    performance_tier: str | None = None

    match_score: int | None = Field(
        None,
        ge=0,
        le=100,
    )

    match_reason: str | None = None


class OpportunityRecommendationUpdate(BaseModel):

    user_id: int | None = None

    progress_id: int | None = None

    subject_field: SubjectFieldEnum | None = None

    external_media_url: str | None = None

    source_platform: str | None = Field(
        None,
        max_length=100,
    )

    media_description: str | None = None

    opportunity_date: datetime | None = None

    performance_tier: str | None = None

    match_score: int | None = Field(
        None,
        ge=0,
        le=100,
    )

    match_reason: str | None = None


class OpportunityRecommendationRead(OpportunityRecommendationBase):

    opportunity_id: int

    model_config = ConfigDict(
        from_attributes=True,
    )


class OpportunitySubjectFetchRequest(BaseModel):

    subject_field: SubjectFieldEnum

    query: str | None = Field(
        None,
        min_length=3,
    )

    num_results: int = Field(
        10,
        ge=1,
        le=20,
    )


class UserOpportunityResponse(BaseModel):

    opportunities: list[OpportunityRecommendationRead]

    performance_tier: str

    progress_id: int

    message: str
