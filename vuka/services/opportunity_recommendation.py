from __future__ import annotations

import logging
from datetime import datetime, timezone
from urllib.parse import urlparse

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from vuka.integrations.gemini_client import GeminiClient
from vuka.integrations.serper_client import SerperClient
from vuka.models.enums import SubjectFieldEnum
from vuka.repositories.onboarding import OnboardingRepository
from vuka.repositories.opportunity_recomendation import (
    OpportunityRecommendationRepository,
)
from vuka.repositories.registration import RegistrationRepository
from vuka.repositories.userprogress import UserProgressRepository

logger = logging.getLogger("vuka.opportunity_recommendation")


class OpportunityRecommendationService:
    AVERAGE_OPPORTUNITY_LIMIT = 6

    def __init__(
        self,
        db: Session,
        serper_client: SerperClient | None = None,
        gemini_client: GeminiClient | None = None,
    ):
        self.db = db
        self.repository = OpportunityRecommendationRepository(db)
        self.onboarding_repo = OnboardingRepository(db)
        self.progress_repo = UserProgressRepository(db)
        self.registration_repo = RegistrationRepository(db)
        self.serper = serper_client
        self.gemini = gemini_client

    @staticmethod
    def tier_from_score(score: float) -> str:
        if score >= 75:
            return "High"
        if score >= 50:
            return "Average"
        return "Low"

    @staticmethod
    def tier_access(tier: str) -> tuple[int | None, str]:
        if tier == "High":
            return None, "unlimited"
        if tier == "Average":
            return OpportunityRecommendationService.AVERAGE_OPPORTUNITY_LIMIT, "limited"
        return 0, "none"

    def get_opportunity(self, opportunity_id: int):
        record = self.repository.get(opportunity_id)
        if not record:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Opportunity not found")
        return record

    def list_opportunities_for_user(self, user_id: int, progress_id: int | None = None):
        return self.repository.list_by_user(user_id, progress_id)

    def get_my_opportunities(self, user_id: int):
        progress = self.progress_repo.get_most_recent_completed(user_id)

        if not progress:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "Complete an assessment before requesting opportunities",
            )

        tier = progress.performance_tier or self.tier_from_score(progress.score or 0)

        return {
            "opportunities": self.list_opportunities_for_user(
                user_id, progress.progress_id
            ),
            "performance_tier": tier,
            "progress_id": progress.progress_id,
            "message": "Latest matched opportunities for your completed assessment.",
        }

    def refresh_for_user(self, user_id: int):
        onboarding = self.onboarding_repo.get_by_user(user_id)
        if not onboarding:
            raise HTTPException(status.HTTP_409_CONFLICT, "Complete onboarding first")

        progress = self.progress_repo.get_most_recent_completed(user_id)
        if not progress:
            raise HTTPException(
                status.HTTP_409_CONFLICT, "Complete an assessment first"
            )

        existing_matches = self.repository.list_by_user(user_id, progress.progress_id)
        if existing_matches:
            tier = progress.performance_tier or self.tier_from_score(
                progress.score or 0
            )
            return {
                "opportunities": existing_matches,
                "performance_tier": tier,
                "progress_id": progress.progress_id,
                "message": "You have already refreshed your matches for this assessment. Please apply to these opportunities or retake the assessment to unlock new ones.",
            }

        if not onboarding:
            raise HTTPException(status.HTTP_409_CONFLICT, "Complete onboarding first")

        progress = self.progress_repo.get_most_recent_completed(user_id)
        if not progress:
            raise HTTPException(
                status.HTTP_409_CONFLICT, "Complete an assessment first"
            )

        score = progress.score or 0
        tier = progress.performance_tier or self.tier_from_score(score)
        limit, _access = self.tier_access(tier)

        if limit == 0:
            return {
                "opportunities": [],
                "performance_tier": tier,
                "progress_id": progress.progress_id,
                "message": "Opportunities are locked for the Low tier. Retake the assessment.",
            }

        interests = (
            " ".join(onboarding.user_interests.get("selected", []))
            if isinstance(onboarding.user_interests, dict)
            else str(onboarding.user_interests)
        )
        career = onboarding.career_aspirations or ""

        current_year = datetime.now().year
        query = f"Kenya {interests} {career} scholarships bootcamps fellowships {current_year} apply"

        logger.info(f"Live searching opportunities with query: {query}")

        client = self.serper or SerperClient()
        try:
            results = client.search_opportunities(query, num_results=15)
        except Exception as exc:
            logger.error(f"Serper search failed: {exc}")
            raise HTTPException(
                status.HTTP_502_BAD_GATEWAY, f"Live opportunity search failed: {exc}"
            )

        if not results:
            return {
                "opportunities": [],
                "performance_tier": tier,
                "progress_id": progress.progress_id,
                "message": "No live opportunities found matching your profile right now.",
            }

        candidates = [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "description": r.get("description", ""),
                "source": urlparse(r.get("url", "")).netloc,
            }
            for r in results
        ]

        profile = {
            "interests": onboarding.user_interests,
            "goals": onboarding.user_goal,
            "career_aspirations": onboarding.career_aspirations,
        }

        gemini = self.gemini or GeminiClient()
        ranked = []

        try:
            ranked = gemini.rank_opportunities(profile, tier, candidates, limit=limit)
        except Exception as exc:
            logger.warning(f"Gemini matching failed (likely quota/model): {exc}")
            ranked = candidates[:limit]
            for item in ranked:
                item["match_score"] = 75
                item["match_reason"] = "Live search result based on your career goals."

        stored = []
        existing_urls = self.repository.list_urls_for_user_progress(
            user_id, progress.progress_id
        )

        for item in ranked:
            url = item.get("url")
            if not url or url in existing_urls:
                continue

            subject = SubjectFieldEnum.OTHER
            text = (item.get("title", "") + item.get("description", "")).lower()
            if "tech" in text or "code" in text or "software" in text:
                subject = SubjectFieldEnum.TECH
            elif "finance" in text or "fintech" in text:
                subject = SubjectFieldEnum.FINTECH
            elif "health" in text:
                subject = SubjectFieldEnum.HEALTHCARE
            elif "business" in text:
                subject = SubjectFieldEnum.BUSINESS

            record = self.repository.create(
                {
                    "user_id": user_id,
                    "progress_id": progress.progress_id,
                    "subject_field": subject,
                    "external_media_url": url,
                    "source_platform": urlparse(url).netloc or "Search",
                    "media_description": item.get("description")
                    or item.get("title")
                    or "Opportunity",
                    "opportunity_date": datetime.now(timezone.utc).replace(tzinfo=None),
                    "performance_tier": tier,
                    "match_score": item.get("match_score"),
                    "match_reason": item.get("match_reason")
                    or "Matched to your profile.",
                }
            )
            stored.append(record)

        self.db.commit()
        return {
            "opportunities": stored,
            "performance_tier": tier,
            "progress_id": progress.progress_id,
            "message": f"Found {len(stored)} live opportunities matched to your profile.",
        }
