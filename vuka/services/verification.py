import os
import secrets
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from vuka.models.security import VerificationDocument
from vuka.repositories.verification import VerificationRepository
from vuka.security.audit import record_event


class VerificationService:
    UPLOAD_DIR = Path(
        os.getenv("VERIFICATION_UPLOAD_DIR", "./uploads/verification")
    ).resolve()

    MAX_SIZE = int(
        os.getenv("VERIFICATION_MAX_FILE_SIZE", "5242880")
    )

    ALLOWED = {
        "pdf": "application/pdf",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
    }

    DOCUMENT_TYPE = "FINAL_YEAR_KENYAN_HIGH_SCHOOL_RESULTS"

    def __init__(self, db: Session):
        self.db = db
        self.repository = VerificationRepository(db)

    def validate_file(
        self,
        filename: str,
        content_type: str | None,
        data: bytes,
    ):
        ext = Path(filename or "").suffix.lower().lstrip(".")

        if ext not in self.ALLOWED:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "Unsupported document type",
            )

        if content_type != self.ALLOWED[ext]:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "Invalid document MIME type",
            )

        if len(data) > self.MAX_SIZE:
            raise HTTPException(
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                "File is too large",
            )

        if ext == "pdf" and not data.startswith(b"%PDF-"):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "Invalid PDF file",
            )

        if ext in {"jpg", "jpeg"} and not data.startswith(b"\xff\xd8\xff"):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "Invalid JPEG file",
            )

        if ext == "png" and not data.startswith(b"\x89PNG\r\n\x1a\n"):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "Invalid PNG file",
            )

        return ext

    def upload_document(
        self,
        user_id: int,
        filename: str,
        content_type: str | None,
        data: bytes,
    ):
        ext = self.validate_file(
            filename,
            content_type,
            data,
        )

        self.UPLOAD_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        reference = (
            f"{user_id}/{secrets.token_urlsafe(32)}.{ext}"
        )

        path = (
            self.UPLOAD_DIR / reference
        ).resolve()

        if self.UPLOAD_DIR not in path.parents:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "Invalid file path",
            )

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        path.write_bytes(data)

        document = VerificationDocument(
            user_id=user_id,
            document_reference=reference,
            document_type=self.DOCUMENT_TYPE,
            file_size=len(data),
            mime_type=self.ALLOWED[ext],
        )

        document = self.repository.create_document(document)

        self.db.commit()
        self.db.refresh(document)

        record_event(
            self.db,
            event_type="DOCUMENT_UPLOADED",
            action="graduate_document_upload",
            user_id=user_id,
            target_type="verification_document",
            target_id=document.id,
        )

        self.db.commit()

        return document

    def get_my_documents(self, user_id: int):
        return self.repository.get_by_user_id(user_id)

    def get_pending_documents(self):
        return self.repository.get_pending()

    def review_document(
        self,
        document_id: int,
        reviewer_id: int,
        review_status: str,
        rejection_reason: str | None,
    ):
        document = self.repository.get_by_id(document_id)

        if not document:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                "Verification document not found",
            )

        if document.user_id == reviewer_id:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                "You cannot review your own document",
            )

        if review_status == "REJECTED" and not rejection_reason:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "Rejection reason is required",
            )

        document.verification_status = review_status
        document.rejection_reason = rejection_reason
        document.reviewed_at = datetime.now(timezone.utc)
        document.reviewed_by = reviewer_id

        user = self.repository.get_user(document.user_id)

        if not user:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                "User not found",
            )

        user.is_verified = review_status == "VERIFIED"

        self.db.commit()
        self.db.refresh(document)

        record_event(
            self.db,
            event_type=(
                "DOCUMENT_VERIFIED"
                if review_status == "VERIFIED"
                else "DOCUMENT_REJECTED"
            ),
            action="graduate_document_review",
            user_id=reviewer_id,
            target_type="verification_document",
            target_id=document.id,
            metadata={"status": review_status},
            severity="MEDIUM",
        )

        self.db.commit()

        return document
