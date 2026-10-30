from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field
from vuka.models.onboarding import SocialPlatformEnum


class OnboardingBase(BaseModel):
    user_id: int
    user_interests: dict[str, Any]
    social_platforms: list[SocialPlatformEnum] = Field(..., min_length=1)
    user_goal: dict[str, Any]
    career_aspirations: str = Field(..., min_length=1, max_length=5000)


class OnboardingCreate(BaseModel):
    user_id: Optional[int] = None
    user_interests: dict[str, Any]
    social_platforms: list[SocialPlatformEnum] = Field(..., min_length=1)
    user_goal: dict[str, Any]
    career_aspirations: str = Field(..., min_length=1, max_length=5000)


class OnboardingUpdate(BaseModel):
    user_interests: Optional[dict[str, Any]] = None
    social_platforms: Optional[list[SocialPlatformEnum]] = Field(None, min_length=1)
    user_goal: Optional[dict[str, Any]] = None
    career_aspirations: Optional[str] = Field(None, min_length=1, max_length=5000)


class OnboardingResponse(OnboardingBase):
    onboarding_id: int
    model_config = ConfigDict(from_attributes=True)
