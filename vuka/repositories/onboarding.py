from __future__ import annotations

from sqlalchemy.orm import Session

from vuka.models.onboarding import Onboarding


class OnboardingRepository:
    def __init__(self, db: Session):
        self.db = db
        self.model = Onboarding

    def get_by_id(self, onboarding_id: int) -> Onboarding | None:
        return self.db.get(self.model, onboarding_id)

    def get_by_user(self, user_id: int) -> Onboarding | None:
        return self.db.query(self.model).filter(self.model.user_id == user_id).first()

    def create(self, data: dict) -> Onboarding:
        db_record = self.model(**data)
        self.db.add(db_record)
        self.db.commit()
        self.db.refresh(db_record)
        return db_record

    def update(
        self,
        onboarding_id: int,
        data: dict,
    ) -> Onboarding | None:
        db_record = self.get_by_id(onboarding_id)

        if db_record:
            for key, value in data.items():
                setattr(db_record, key, value)

            self.db.commit()
            self.db.refresh(db_record)

        return db_record

    def list_all(self):
        return self.db.query(self.model).all()

    def delete(self, onboarding_id: int) -> bool:
        db_record = self.get_by_id(onboarding_id)

        if db_record:
            self.db.delete(db_record)
            self.db.commit()
            return True

        return False
