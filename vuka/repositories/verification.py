from sqlalchemy.orm import Session

from vuka.models.registration import Registration
from vuka.models.security import VerificationDocument


class VerificationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_document(self, document: VerificationDocument):
        self.db.add(document)
        self.db.flush()
        return document

    def get_by_user_id(self, user_id: int):
        return (
            self.db.query(VerificationDocument)
            .filter(VerificationDocument.user_id == user_id)
            .order_by(VerificationDocument.uploaded_at.desc())
            .all()
        )

    def get_pending(self):
        return (
            self.db.query(VerificationDocument)
            .filter(
                VerificationDocument.verification_status.in_(
                    ["PENDING", "REQUIRES_REVIEW"]
                )
            )
            .all()
        )

    def get_by_id(self, document_id: int):
        return self.db.get(VerificationDocument, document_id)

    def get_user(self, user_id: int):
        return self.db.get(Registration, user_id)
