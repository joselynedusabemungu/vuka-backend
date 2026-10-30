import os
import secrets

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from vuka.repositories.registration import RegistrationRepository
from vuka.schemas.registration import RegistrationUpdate
from vuka.security.audit import record_event


class AdminService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = RegistrationRepository(db)

    def bootstrap_admin(self, user_id: int, bootstrap_key: str):
        admin_bootstrap_key = os.getenv("ADMIN_BOOTSTRAP_KEY")

        if not admin_bootstrap_key:
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                "Admin bootstrap is not configured",
            )

        if not secrets.compare_digest(bootstrap_key, admin_bootstrap_key):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                "Invalid bootstrap credentials",
            )

        if self.repository.admin_exists():
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "Administrator already exists",
            )

        user = self.repository.get_registration_by_id(user_id)

        if not user:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                "User not found",
            )

        user.user_type = "admin"
        self.db.commit()
        self.db.refresh(user)

        record_event(
            self.db,
            event_type="ADMIN_CREATED",
            action="bootstrap_admin",
            user_id=user.user_id,
            target_type="user",
            target_id=user.user_id,
            severity="CRITICAL",
            alert=True,
        )
        self.db.commit()

        return user

    def get_user(self, user_id: int):
        user = self.repository.get_registration(user_id)

        if not user:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                "User not found",
            )

        return user

    def update_user(
        self,
        user_id: int,
        registration: RegistrationUpdate,
        current_user_id: int,
    ):
        user = self.repository.get_registration_by_id(user_id)

        if not user:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                "User not found",
            )

        old_role = user.user_type

        user = self.repository.update_registration(user_id, registration)

        if old_role != user.user_type:
            record_event(
                self.db,
                event_type="ROLE_CHANGED",
                action="role_change",
                user_id=current_user_id,
                target_type="user",
                target_id=user_id,
                metadata={
                    "from": old_role,
                    "to": user.user_type,
                },
                severity="HIGH",
                alert=True,
            )
            self.db.commit()

        return user

    def delete_user(self, user_id: int):
        user = self.repository.delete_registration(user_id)

        if not user:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                "User not found",
            )

        return {"detail": "User deactivated"}
