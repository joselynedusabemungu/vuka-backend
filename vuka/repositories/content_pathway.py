from datetime import datetime, timezone

from sqlalchemy.orm import Session

from vuka.models.content_pathway import ContentPathway


class ContentPathwayRepository:
    def __init__(self, db: Session):
        self.db = db
        self.model = ContentPathway

    def get_by_id(self, content_pathway_id: int):
        return self.db.get(self.model, content_pathway_id)

    def get_by_content(self, content_id: int):
        return (
            self.db.query(self.model).filter(self.model.content_id == content_id).all()
        )

    def get_by_onboarding_content(self, onboarding_id: int, content_id: int):
        return (
            self.db.query(self.model)
            .filter(
                self.model.onboarding_id == onboarding_id,
                self.model.content_id == content_id,
            )
            .first()
        )

    def list_by_onboarding(self, onboarding_id: int, skip: int = 0, limit: int = 50):
        return (
            self.db.query(self.model)
            .filter(self.model.onboarding_id == onboarding_id)
            .order_by(self.model.date.desc(), self.model.content_pathway_id.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create(self, data: dict):
        record = self.model(**data)
        self.db.add(record)
        self.db.flush()
        return record

    def mark_watched(self, pathway_id: int):
        record = self.get_by_id(pathway_id)
        if not record:
            return None
        if not record.watched:
            record.watched = True
            record.watched_at = datetime.now(timezone.utc)
            self.db.flush()
        return record

    def update(self, pathway_id: int, data: dict):
        record = self.get_by_id(pathway_id)
        if not record:
            return None
        for key, value in data.items():
            setattr(record, key, value)
        self.db.flush()
        return record

    def delete(self, pathway_id: int) -> bool:
        record = self.get_by_id(pathway_id)
        if not record:
            return False
        self.db.delete(record)
        self.db.flush()
        return True
