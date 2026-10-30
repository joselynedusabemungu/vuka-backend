from sqlalchemy.orm import Session
from vuka.models.verifiedassessment import VerifiedAssessment


class VerifiedAssessmentRepository:
    def __init__(self, db: Session):
        self.db = db
        self.model = VerifiedAssessment

    def create(self, **data):
        record = self.model(**data)
        self.db.add(record)
        self.db.flush()
        return record

    def get_by_id(self, assessment_id: int):
        return self.db.get(self.model, assessment_id)

    def get_by_user_and_generated(self, user_id: int, generated_assessment_id: int, in_progress_only: bool = False):
        query = self.db.query(self.model).filter(
            self.model.user_id == user_id,
            self.model.generated_assessment_id == generated_assessment_id,
        )
        if in_progress_only:
            query = query.filter(self.model.status == "in_progress")
        return query.order_by(self.model.assessment_date.desc()).first()

    def get_latest_completed_by_user_and_generated(self, user_id: int, generated_assessment_id: int):
        return (
            self.db.query(self.model)
            .filter(
                self.model.user_id == user_id,
                self.model.generated_assessment_id == generated_assessment_id,
                self.model.status == "completed",
            )
            .order_by(self.model.completed_at.desc())
            .first()
        )

    def get_all(self, user_id: int | None = None):
        query = self.db.query(self.model)
        if user_id is not None:
            query = query.filter(self.model.user_id == user_id)
        return query.order_by(self.model.assessment_date.desc()).all()

    def update(self, assessment_id: int, updates: dict):
        record = self.get_by_id(assessment_id)
        if not record:
            return None
        for key, value in updates.items():
            setattr(record, key, value)
        self.db.flush()
        return record

    def delete(self, assessment_id: int):
        record = self.get_by_id(assessment_id)
        if record:
            self.db.delete(record)
            self.db.flush()
        return record
