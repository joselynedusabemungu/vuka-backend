from sqlalchemy.orm import Session

from vuka.models.registration import Registration
from vuka.schemas.registration import RegistrationCreate, RegistrationUpdate


class RegistrationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_registration(self, registration: RegistrationCreate):
        db_registration = Registration(**registration.model_dump())
        self.db.add(db_registration)
        self.db.commit()
        self.db.refresh(db_registration)
        return db_registration

    def get_registrations(self):
        return (
            self.db.query(Registration)
            .filter(Registration.is_active.is_(True))
            .all()
        )

    def get_registration(self, user_id: int):
        return (
            self.db.query(Registration)
            .filter(
                Registration.user_id == user_id,
                Registration.is_active.is_(True),
            )
            .first()
        )

    def update_registration(self, user_id: int, registration: RegistrationUpdate):
        user = self.get_registration(user_id)
        if not user:
            return None

        for key, value in registration.model_dump(exclude_unset=True).items():
            setattr(user, key, value)

        self.db.commit()
        self.db.refresh(user)
        return user

    def delete_registration(self, user_id: int):
        user = self.db.query(Registration).filter(Registration.user_id == user_id).first()
        if user is None:
            return None

        user.is_active = False
        self.db.commit()
        self.db.refresh(user)
        return user