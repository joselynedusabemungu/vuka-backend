from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class UserProgressCreate(BaseModel):
    user_id: int
    assessment_id: int


class UserProgressResponse(BaseModel):
    progress_id: int
    user_id: int
    assessment_id: int
    score: int
    streak_count: int
    performance_tier: str | None = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class CategoryScore(BaseModel):
    category: str
    average_score: int


class CompletedAssessment(BaseModel):
    assessment_id: int
    progress_id: int
    category: str
    assessment_date: date
    score: int
    performance_tier: str


class WeeklyActivityDay(BaseModel):
    weekday: str
    date: date
    completed: bool


class ProgressSummary(BaseModel):
    overall_progress: int
    category_breakdown: list[CategoryScore]
    current_streak: int
    weekly_activity: list[WeeklyActivityDay]
    completed_assessments: list[CompletedAssessment]
    model_config = ConfigDict(from_attributes=True)
