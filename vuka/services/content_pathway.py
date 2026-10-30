import logging
from datetime import date
from urllib.parse import urlparse

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from database import SessionLocal
from vuka.models.content_pathway import ContentPathway
from vuka.repositories.content_pathway import ContentPathwayRepository
from vuka.repositories.contents import ContentRepository
from vuka.repositories.generated_assessment import GeneratedAssessmentRepository
from vuka.repositories.onboarding import OnboardingRepository
from vuka.services.generated_assessment import GeneratedAssessmentService

logger = logging.getLogger("vuka.content_pathway")

TRUSTED_MEDIA_DOMAINS = {
    "tiktok.com",
    "www.tiktok.com",
    "youtube.com",
    "www.youtube.com",
    "youtu.be",
    "instagram.com",
    "www.instagram.com",
}


class ContentPathwayService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ContentPathwayRepository(db)
        self.onboarding_repo = OnboardingRepository(db)

    def get_onboarding_for_user(self, user_id: int):
        onboarding = self.onboarding_repo.get_by_user(user_id)
        if not onboarding:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Onboarding not found")
        return onboarding

    def get_onboarding_for_user_or_conflict(self, user_id: int):
        onboarding = self.onboarding_repo.get_by_user(user_id)
        if not onboarding:
            raise HTTPException(status.HTTP_409_CONFLICT, "Complete onboarding first")
        return onboarding

    def generate_pathway(self, schema: dict, onboarding_id: int) -> ContentPathway:
        content = ContentRepository(self.db).get_by_id(schema["content_id"])
        if not content:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Content not found")

        if not self.onboarding_repo.get_by_id(onboarding_id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Onboarding not found")

        url = str(schema["external_media_url"])
        self.assert_trusted_url(url)

        existing = self.repo.get_by_onboarding_content(
            onboarding_id, content.content_id
        )
        if existing:
            return existing

        record = self.repo.create(
            {
                "content_id": content.content_id,
                "onboarding_id": onboarding_id,
                "external_media_url": url,
                "media_description": schema["media_description"],
                "date": schema.get("date") or date.today(),
            }
        )
        self.db.commit()
        self.db.refresh(record)
        return record

    def retrieve_pathway(self, pathway_id: int, onboarding_id: int | None = None):
        record = self.repo.get_by_id(pathway_id)
        if not record:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Content pathway not found")
        if onboarding_id is not None and record.onboarding_id != onboarding_id:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, "Content pathway does not belong to the user"
            )
        return record

    def list_for_onboarding(self, onboarding_id: int, skip: int = 0, limit: int = 50):
        return self.repo.list_by_onboarding(onboarding_id, skip, limit)

    def get_my_pathway(self, user_id: int, skip: int = 0, limit: int = 50):
        onboarding = self.get_onboarding_for_user(user_id)
        return self.list_for_onboarding(onboarding.onboarding_id, skip, limit)

    def create_for_user(self, user_id: int, schema: dict):
        onboarding = self.get_onboarding_for_user_or_conflict(user_id)
        return self.generate_pathway(schema, onboarding.onboarding_id)

    def get_for_user(self, user_id: int, pathway_id: int):
        onboarding = self.get_onboarding_for_user(user_id)
        return self.retrieve_pathway(pathway_id, onboarding.onboarding_id)

    def mark_watched_for_user(self, user_id: int, pathway_id: int):
        onboarding = self.get_onboarding_for_user(user_id)
        record = self.mark_watched(pathway_id, onboarding.onboarding_id)
        return record

    def update_for_user(self, user_id: int, pathway_id: int, schema):
        onboarding = self.get_onboarding_for_user(user_id)
        return self.modify_pathway(pathway_id, schema, onboarding.onboarding_id)

    def delete_for_user(self, user_id: int, pathway_id: int):
        onboarding = self.get_onboarding_for_user(user_id)
        self.remove_pathway(pathway_id, onboarding.onboarding_id)

    def mark_watched(self, pathway_id: int, onboarding_id: int):
        self.retrieve_pathway(pathway_id, onboarding_id)
        record = self.repo.mark_watched(pathway_id)
        self.db.commit()
        self.db.refresh(record)
        return record

    def modify_pathway(self, pathway_id: int, schema, onboarding_id: int | None = None):
        record = self.retrieve_pathway(pathway_id, onboarding_id)
        if schema.external_media_url is not None:
            self.assert_trusted_url(str(schema.external_media_url))

        updates = schema.model_dump(exclude_unset=True, mode="json")
        if "external_media_url" in updates:
            updates["external_media_url"] = str(updates["external_media_url"])

        record = self.repo.update(pathway_id, updates)
        self.db.commit()
        return record

    def remove_pathway(self, pathway_id: int, onboarding_id: int | None = None):
        self.retrieve_pathway(pathway_id, onboarding_id)
        self.repo.delete(pathway_id)
        self.db.commit()

    @staticmethod
    def generate_assessment_after_watched(content_id: int) -> None:
        db = SessionLocal()
        try:
            if GeneratedAssessmentRepository(db).get_by_content_id(content_id):
                return
            GeneratedAssessmentService(db).generate_for_content(content_id)
        except Exception as exc:
            logger.warning(
                f"Background assessment generation failed for content_id={content_id}: {exc}"
            )
            db.rollback()
        finally:
            db.close()

    @staticmethod
    def assert_trusted_url(url: str):
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid media URL"
            )
        if parsed.hostname.lower() not in TRUSTED_MEDIA_DOMAINS:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY, "Media source is not trusted"
            )
