from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from vuka.repositories.userprogress import UserProgressRepository
from vuka.repositories.registration import RegistrationRepository
from vuka.schemas.userprogress import (
    ProgressSummary,
    CategoryScore,
    CompletedAssessment,
    WeeklyActivityDay,
)


WEEKDAY_LABELS = ["M", "T", "W", "T", "F", "S", "S"]


class UserProgressService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = UserProgressRepository(db)
        self.registration_repo = RegistrationRepository(db)

    def get(self, progress_id: int):
        obj = self.repo.get(progress_id)

        if not obj:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                "Progress record not found",
            )

        return obj

    def get_for_user(self, progress_id: int, user_id: int, user_type: str):
        obj = self.get(progress_id)

        if user_type != "admin" and obj.user_id != user_id:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                "You cannot access another user's progress",
            )

        return obj

    def list_by_user(self, user_id: int):
        return self.repo.list_by_user(user_id)

    def list_all(self):
        return self.repo.list()

    def get_summary(self, user_id: int) -> ProgressSummary:
        if not self.registration_repo.get_registration(user_id):
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                "User not found",
            )

        today = datetime.now(timezone.utc).date()
        week_start = today - timedelta(days=today.weekday())
        week_end_exclusive = week_start + timedelta(days=7)

        active_dates = self.repo.get_active_dates_in_range(
            user_id,
            week_start,
            week_end_exclusive,
        )

        recent = self.repo.get_most_recent_completed(user_id)

        return ProgressSummary(
            overall_progress=self.repo.get_average_score(user_id),
            category_breakdown=[
                CategoryScore(
                    category=c,
                    average_score=a,
                )
                for c, a in self.repo.get_average_score_by_category(user_id)
            ],
            current_streak=recent.streak_count if recent else 0,
            weekly_activity=[
                WeeklyActivityDay(
                    weekday=WEEKDAY_LABELS[i],
                    date=week_start + timedelta(days=i),
                    completed=(week_start + timedelta(days=i)) in active_dates,
                )
                for i in range(7)
            ],
            completed_assessments=[
                CompletedAssessment(
                    assessment_id=row.assessment_id,
                    progress_id=row.progress_id,
                    category=row.category,
                    assessment_date=row.completed_at.astimezone(
                        timezone.utc
                    ).date(),
                    score=row.score,
                    performance_tier=row.performance_tier or "Low",
                )
                for row in self.repo.get_recent_completed(
                    user_id,
                    limit=20,
                )
            ],
        )
