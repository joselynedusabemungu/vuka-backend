from datetime import datetime

from sqlalchemy.orm import Session

from vuka.models.security import LoginAttempt


class SecurityRepository:
    def __init__(self, db: Session):
        self.db = db

    def record_login(self, user, identifier: str, ip: str | None, success: bool):
        attempt = LoginAttempt(
            user_id=user.user_id if user else None,
            identifier=identifier,
            ip_address=ip,
            success=success,
        )
        self.db.add(attempt)
        self.db.commit()

    def count_recent_ip_failures(self, ip: str | None, since: datetime) -> int:
        return (
            self.db.query(LoginAttempt)
            .filter(
                LoginAttempt.ip_address == ip,
                LoginAttempt.success.is_(False),
                LoginAttempt.attempted_at >= since,
            )
            .count()
        )
