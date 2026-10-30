from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from vuka.integrations.gemini_client import GeminiClient
from vuka.integrations.serper_client import SerperClient
from vuka.integrations.youtube_client import YouTubeClient
from vuka.models.onboarding import Onboarding
from vuka.repositories.contents import ContentRepository
from vuka.repositories.content_pathway import ContentPathwayRepository
from vuka.schemas.contents import ContentCreate, ContentUpdate


class ContentService:
    def __init__(self, db: Session, gemini_client: GeminiClient | None = None):
        self.db = db
        self.repo = ContentRepository(db)
        self.pathway_repo = ContentPathwayRepository(db)
        self.gemini = gemini_client

    def fetch_and_save_from_serper(self, query: str):
        if not os.getenv("SERPER_API_KEY"):
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "SERPER_API_KEY is not configured",
            )
        try:
            import httpx

            response = httpx.post(
                os.getenv("SERPER_URL", "https://google.serper.dev/search"),
                headers={
                    "X-API-KEY": os.environ["SERPER_API_KEY"],
                    "Content-Type": "application/json",
                },
                json={"q": query, "num": 10},
                timeout=15.0,
            )
            response.raise_for_status()
            data = response.json()
        except Exception as exc:
            raise HTTPException(
                status.HTTP_502_BAD_GATEWAY,
                f"Serper API failure: {exc}",
            ) from exc

        saved = []
        for item in data.get("organic", []):
            candidate = self._content_record(
                {
                    "url": item.get("link"),
                    "title": item.get("title"),
                    "description": item.get("snippet"),
                },
                "Serper/Google",
            )
            if not candidate["external_media_url"]:
                continue
            existing = self.repo.get_by_url(candidate["external_media_url"])
            saved.append(existing or self.repo.create(candidate))
        self.db.commit()
        return saved

    def fetch_and_save_from_youtube(self, query: str):
        try:
            results = asyncio.run(YouTubeClient().search(query, 10))
        except RuntimeError as exc:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from exc

        saved = []
        for item in results:
            candidate = self._content_record(item, "YouTube")
            existing = self.repo.get_by_url(candidate["external_media_url"])
            saved.append(existing or self.repo.create(candidate))
        self.db.commit()
        return saved

    def get_by_id(self, content_id: int):
        record = self.repo.get_by_id(content_id)
        if not record:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Content record not found")
        return record

    def get_all(self, skip: int = 0, limit: int = 100):
        return self.repo.get_all(skip=skip, limit=limit)

    def create(self, schema_data: ContentCreate):
        data = schema_data.model_dump(mode="json")
        data["external_media_url"] = str(data["external_media_url"])
        return self.repo.create(data)

    def update(self, content_id: int, schema_data: ContentUpdate):
        self.get_by_id(content_id)
        data = schema_data.model_dump(exclude_unset=True, mode="json")
        if "external_media_url" in data and data["external_media_url"]:
            data["external_media_url"] = str(data["external_media_url"])
        return self.repo.update(content_id, data)

    def delete(self, content_id: int) -> bool:
        self.get_by_id(content_id)
        return self.repo.delete(content_id)

    @staticmethod
    def _content_record(result: dict, fallback_platform: str) -> dict:
        url = str(result.get("url") or result.get("link") or "").strip()
        title = str(result.get("title") or "").strip()
        description = str(result.get("description") or result.get("snippet") or title).strip()

        if title and title in description:
            media_description = description
        else:
            media_description = f"{title}. {description}".strip(". ")

        return {
            "external_media_url": url,
            "source_platform": str(result.get("platform") or fallback_platform),
            "media_description": media_description,
            "datetime": datetime.now(timezone.utc).replace(tzinfo=None),
        }

    @staticmethod
    def _flatten_profile_values(value) -> list[str]:
        if isinstance(value, str):
            return [value.strip()] if value.strip() else []
        if isinstance(value, (list, tuple, set)):
            result = []
            for item in value:
                result.extend(ContentService._flatten_profile_values(item))
            return result
        if isinstance(value, dict):
            result = []
            for key, item in value.items():
                if key not in {"id"}:
                    result.extend(ContentService._flatten_profile_values(item))
            return result
        return []

    def _build_search_terms(self, onboarding: Onboarding) -> list[str]:
        interests = self._flatten_profile_values(onboarding.user_interests)
        goals = self._flatten_profile_values(onboarding.user_goal)
        career = [onboarding.career_aspirations] if onboarding.career_aspirations else []

        raw_terms = interests + goals + career

        stopwords = {
            "i", "a", "an", "the", "to", "of", "and", "or", "in", "on", "at",
            "is", "am", "are", "be", "want", "wants", "like", "would", "will",
            "my", "me", "mine", "this", "that", "it", "for", "with", "from",
            "about", "learn", "learning", "master", "mastering", "art", "how",
            "get", "getting", "become", "becoming", "study", "studying", "well",
            "career", "skills", "explore", "interested", "interest",
        }

        cleaned_keywords = []
        for term in raw_terms:
            if not isinstance(term, str):
                continue
            words = term.lower().split()
            for w in words:
                clean = w.strip(".,!?;:'\"")
                if clean and clean not in stopwords and len(clean) > 2:
                    cleaned_keywords.append(clean)

        unique = list(dict.fromkeys(k for k in cleaned_keywords if k))
        return unique[:5] or ["career skills"]

    async def get_recommended_for_user(self, user_id: int, limit: int = 20):
        from vuka.repositories.onboarding import OnboardingRepository
        from vuka.schemas.content_pathway import RecommendedContentResponse

        onboarding = OnboardingRepository(self.db).get_by_user(user_id)

        if not onboarding:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "Complete onboarding before requesting personalized content",
            )

        if limit < 1 or limit > 50:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "limit must be between 1 and 50",
            )

        rows = await self.get_personalized_content(onboarding, limit)

        response = []
        for row in rows:
            pathway = row["pathway"]
            content = row["content"]

            response.append(
                RecommendedContentResponse(
                    content_pathway_id=pathway.content_pathway_id,
                    content_id=content.content_id,
                    onboarding_id=pathway.onboarding_id,
                    external_media_url=content.external_media_url,
                    media_description=content.media_description,
                    date=pathway.date,
                    source_platform=content.source_platform,
                    relevance_score=(row.get("relevance_score") or pathway.relevance_score),
                    relevance_reason=(row.get("relevance_reason") or pathway.relevance_reason),
                    generated_assessment_id=(
                        content.generated_assessment.assessment_id
                        if content.generated_assessment
                        else None
                    ),
                    watched=pathway.watched,
                    watched_at=pathway.watched_at,
                )
            )

        return response

    async def get_personalized_content(self, onboarding: Onboarding, limit: int = 20):
        candidates = []
        errors = []

        platforms = [
            p.value if hasattr(p, "value") else str(p)
            for p in onboarding.social_platforms
        ]

        terms = self._build_search_terms(onboarding)
        keyword = " ".join(terms)

        print(f"[FETCH] Live fetching for keywords: {keyword}")
        print(f"[FETCH] User selected platforms: {platforms}")

        tasks = []
        labels = []

        if "youtube" in platforms:
            async def youtube_task():
                try:
                    return await YouTubeClient().search(keyword=keyword, max_results=min(limit, 20))
                except Exception as exc:
                    print(f"[ERROR] YouTube fetch failed: {exc}")
                    return []
            tasks.append(youtube_task())
            labels.append("youtube")

        if "tiktok" in platforms:
            async def tiktok_task():
                try:
                    return await SerperClient().search_social(
                        platform="tiktok",
                        keyword=keyword,
                        num_results=min(limit, 20),
                    )
                except Exception as exc:
                    print(f"[ERROR] TikTok fetch failed: {exc}")
                    return []
            tasks.append(tiktok_task())
            labels.append("tiktok")

        if "instagram" in platforms:
            async def instagram_task():
                try:
                    return await SerperClient().search_social(
                        platform="instagram",
                        keyword=keyword,
                        num_results=min(limit, 20),
                    )
                except Exception as exc:
                    print(f"[ERROR] Instagram fetch failed: {exc}")
                    return []
            tasks.append(instagram_task())
            labels.append("instagram")

        if not tasks:
            async def default_youtube():
                try:
                    return await YouTubeClient().search(keyword=keyword, max_results=min(limit, 20))
                except Exception as exc:
                    print(f"[ERROR] YouTube fetch failed: {exc}")
                    return []
            tasks.append(default_youtube())
            labels.append("youtube")

        results = []
        for task in tasks:
            try:
                result = await task
                results.append(result)
            except Exception as e:
                results.append(e)

        for label, result in zip(labels, results):
            if isinstance(result, Exception):
                errors.append(f"{label}: {result}")
                continue
            if isinstance(result, list):
                candidates.extend(result)

        if not candidates:
            print(f"[ERROR] No candidates found. Errors: {errors}")
            raise HTTPException(
                status.HTTP_502_BAD_GATEWAY,
                {
                    "message": "No content could be fetched from the platforms you selected",
                    "errors": errors,
                },
            )

        unique = {}
        for candidate in candidates:
            url = candidate.get("url")
            if url:
                unique[url] = candidate
        candidates = list(unique.values())
        print(f"[FETCH] Fetched {len(candidates)} candidates from {labels}")

        profile = {
            "interests": onboarding.user_interests,
            "goals": onboarding.user_goal,
            "career_aspirations": onboarding.career_aspirations,
            "platforms": platforms,
        }

        gemini = self.gemini or GeminiClient()
        try:
            print(f"[AI] Sending {len(candidates)} candidates to Gemini")
            ranked = await asyncio.to_thread(gemini.rank_content, profile, candidates, limit)
            print(f"[AI] Gemini returned {len(ranked)} matches")
        except Exception as exc:
            print(f"[ERROR] Gemini matching failed: {exc}")
            ranked = candidates[:limit]
            for item in ranked:
                item["relevance_score"] = 50
                item["relevance_reason"] = "Recommended based on your interests."

        saved = []
        for candidate in ranked:
            url = candidate["url"]
            data = self._content_record(candidate, candidate.get("platform", "external"))

            existing = self.repo.get_by_url(url)
            content = existing or self.repo.create(data)

            if existing:
                content = self.repo.update(
                    content.content_id,
                    {
                        "source_platform": data["source_platform"],
                        "media_description": data["media_description"],
                        "datetime": data["datetime"],
                    },
                )

            pathway = self.pathway_repo.get_by_onboarding_content(
                onboarding.onboarding_id, content.content_id
            )

            if not pathway:
                pathway = self.pathway_repo.create(
                    {
                        "content_id": content.content_id,
                        "onboarding_id": onboarding.onboarding_id,
                        "external_media_url": content.external_media_url,
                        "media_description": content.media_description,
                        "date": datetime.now(timezone.utc).date(),
                        "relevance_score": candidate.get("relevance_score"),
                        "relevance_reason": candidate.get("relevance_reason"),
                    }
                )
            else:
                self.pathway_repo.update(
                    pathway.content_pathway_id,
                    {
                        "relevance_score": candidate.get("relevance_score"),
                        "relevance_reason": candidate.get("relevance_reason"),
                    },
                )

            saved.append(
                {
                    "pathway": pathway,
                    "content": content,
                    "relevance_score": candidate.get("relevance_score"),
                    "relevance_reason": candidate.get("relevance_reason"),
                }
            )

        self.db.commit()
        print(f"[SAVE] Saved {len(saved)} pathways to database")
        return saved