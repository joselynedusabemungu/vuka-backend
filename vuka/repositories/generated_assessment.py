from sqlalchemy.orm import Session
from vuka.models.generated_assessment import GeneratedAssessment


class GeneratedAssessmentRepository:
    def __init__(self, db: Session):
        self.db = db
        self.model = GeneratedAssessment

    def get_by_content_id(self, content_id: int):
        return self.db.query(self.model).filter(self.model.content_id == content_id).first()

    def get_by_id(self, assessment_id: int):
        return self.db.get(self.model, assessment_id)

    def get_all(self, skip: int = 0, limit: int = 100):
        return self.db.query(self.model).offset(skip).limit(limit).all()

    def upsert(self, content_id: int, category: str, questions_json: str, model_used: str):
        existing = self.get_by_content_id(content_id)
        if existing:
            existing.category = category
            existing.questions = questions_json
            existing.model_used = model_used
            self.db.flush()
            return existing
        record = self.model(
            content_id=content_id,
            category=category,
            questions=questions_json,
            model_used=model_used,
        )
        self.db.add(record)
        self.db.flush()
        return record

    def delete(self, assessment_id: int) -> bool:
        record = self.get_by_id(assessment_id)
        if not record:
            return False
        self.db.delete(record)
        self.db.flush()
        return True

    def list_by_onboarding(self, onboarding_id: int, skip: int = 0, limit: int = 100):
        from vuka.models.content_pathway import ContentPathway

        return (
            self.db.query(self.model)
            .join(ContentPathway, ContentPathway.content_id == self.model.content_id)
            .filter(ContentPathway.onboarding_id == onboarding_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
