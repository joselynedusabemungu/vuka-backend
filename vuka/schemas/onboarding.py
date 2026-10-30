from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from vuka.models.onboarding import SocialPlatformEnum


class OnboardingBase(BaseModel):
    user_id: int
    user_interests: dict[str, Any]
    social_platforms: list[SocialPlatformEnum] = Field(..., min_length=1)
    user_goal: dict[str, Any]
    career_aspirations: str = Field(..., min_length=1, max_length=5000)


class OnboardingCreate(BaseModel):
    user_id: int | None = None
    user_interests: dict[str, Any]
    social_platforms: list[SocialPlatformEnum] = Field(..., min_length=1)
    user_goal: dict[str, Any]
    career_aspirations: str = Field(..., min_length=1, max_length=5000)


class OnboardingUpdate(BaseModel):
    user_interests: dict[str, Any] | None = None
    social_platforms: list[SocialPlatformEnum] | None = Field(None, min_length=1)
    user_goal: dict[str, Any] | None = None
    career_aspirations: str | None = Field(None, min_length=1, max_length=5000)


class OnboardingResponse(OnboardingBase):
    onboarding_id: int
    model_config = ConfigDict(from_attributes=True)
