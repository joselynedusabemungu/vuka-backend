from sqlalchemy.orm import Session

from vuka.repositories.registration import RegistrationRepository
from vuka.schemas.registration import RegistrationUpdate


class RegistrationService:
    def __init__(self, db: Session):
        self.repository = RegistrationRepository(db)

    def get_registrations(self):
        return self.repository.get_registrations()

    def get_registration(self, user_id: int):
        return self.repository.get_registration(user_id)

    def update_registration(
        self,
        user_id: int,
        registration: RegistrationUpdate,
    ):
        return self.repository.update_registration(
            user_id,
            registration,
        )

    def delete_registration(self, user_id: int):
        return self.repository.delete_registration(user_id)


def get_registrations(db: Session):
    return RegistrationService(db).get_registrations()


def get_registration(db: Session, user_id: int):
    return RegistrationService(db).get_registration(user_id)


def update_registration(
    db: Session,
    user_id: int,
    registration: RegistrationUpdate,
):
    return RegistrationService(db).update_registration(
        user_id,
        registration,
    )


def delete_registration(db: Session, user_id: int):
    return RegistrationService(db).delete_registration(user_id)
