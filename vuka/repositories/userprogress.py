from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

from vuka.models.userprogress import UserProgress
from vuka.models.verifiedassessment import VerifiedAssessment


class UserProgressRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, progress_id: int) -> UserProgress | None:
        return self.db.get(UserProgress, progress_id)

    def get_by_assessment(self, assessment_id: int) -> UserProgress | None:
        return (
            self.db.query(UserProgress)
            .filter(UserProgress.assessment_id == assessment_id)
            .first()
        )

    def list(self, skip: int = 0, limit: int = 100):
        return self.db.query(UserProgress).offset(skip).limit(limit).all()

    def create(self, data: dict) -> UserProgress:
        obj = UserProgress(**data)
        self.db.add(obj)
        self.db.flush()
        return obj

    def update(self, obj: UserProgress, updates: dict) -> UserProgress:
        for key, value in updates.items():
            setattr(obj, key, value)
        self.db.flush()
        return obj

    def delete(self, obj: UserProgress) -> None:
        self.db.delete(obj)
        self.db.flush()

    def list_by_user(self, user_id: int):
        return (
            self.db.query(UserProgress)
            .filter(UserProgress.user_id == user_id)
            .order_by(UserProgress.created_at.desc())
            .all()
        )

    def get_most_recent_completed(self, user_id: int):
        return (
            self.db.query(UserProgress)
            .join(
                VerifiedAssessment,
                UserProgress.assessment_id == VerifiedAssessment.assessment_id,
            )
            .filter(
                UserProgress.user_id == user_id,
                VerifiedAssessment.status == "completed",
            )
            .order_by(VerifiedAssessment.completed_at.desc())
            .first()
        )

    def get_average_score(self, user_id: int) -> int:
        avg = (
            self.db.query(func.avg(UserProgress.score))
            .join(
                VerifiedAssessment,
                UserProgress.assessment_id == VerifiedAssessment.assessment_id,
            )
            .filter(
                UserProgress.user_id == user_id,
                VerifiedAssessment.status == "completed",
            )
            .scalar()
        )
        return round(avg) if avg is not None else 0

    def get_average_score_by_category(self, user_id: int):
        rows = (
            self.db.query(VerifiedAssessment.category, func.avg(UserProgress.score))
            .join(
                VerifiedAssessment,
                UserProgress.assessment_id == VerifiedAssessment.assessment_id,
            )
            .filter(
                UserProgress.user_id == user_id,
                VerifiedAssessment.status == "completed",
            )
            .group_by(VerifiedAssessment.category)
            .all()
        )
        return [(category, round(avg)) for category, avg in rows]

    def get_active_dates_in_range(self, user_id: int, start: date, end: date):
        rows = (
            self.db.query(VerifiedAssessment.completed_at)
            .join(
                UserProgress,
                UserProgress.assessment_id == VerifiedAssessment.assessment_id,
            )
            .filter(
                UserProgress.user_id == user_id,
                VerifiedAssessment.status == "completed",
                VerifiedAssessment.completed_at.isnot(None),
                VerifiedAssessment.completed_at >= start,
                VerifiedAssessment.completed_at < end,
            )
            .all()
        )
        return {row[0].date() for row in rows}

    def get_recent_completed(self, user_id: int, limit: int = 5):
        rows = (
            self.db.query(
                VerifiedAssessment.assessment_id,
                UserProgress.progress_id,
                VerifiedAssessment.category,
                VerifiedAssessment.completed_at,
                UserProgress.score,
                UserProgress.performance_tier,
            )
            .join(
                VerifiedAssessment,
                UserProgress.assessment_id == VerifiedAssessment.assessment_id,
            )
            .filter(
                UserProgress.user_id == user_id,
                VerifiedAssessment.status == "completed",
            )
            .order_by(VerifiedAssessment.completed_at.desc())
            .limit(limit)
            .all()
        )
        return rows
