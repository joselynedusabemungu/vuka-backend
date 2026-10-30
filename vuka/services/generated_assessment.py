from __future__ import annotations
import json
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from vuka.integrations.gemini_client import GeminiClient
from vuka.models.enums import CategoryEnum
from vuka.models.generated_assessment import GeneratedAssessment
from vuka.repositories.contents import ContentRepository
from vuka.repositories.generated_assessment import GeneratedAssessmentRepository
from vuka.repositories.content_pathway import ContentPathwayRepository
from vuka.repositories.onboarding import OnboardingRepository


class GeneratedAssessmentService:
    def __init__(self, db: Session, gemini_client: GeminiClient | None = None):
        self.db = db
        self.content_repo = ContentRepository(db)
        self.repo = GeneratedAssessmentRepository(db)
        self.pathway_repo = ContentPathwayRepository(db)
        self.gemini = gemini_client

    @staticmethod
    def parse_questions(record: GeneratedAssessment) -> list[dict]:
        try:
            questions = json.loads(record.questions)
        except (TypeError, json.JSONDecodeError) as exc:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Stored assessment questions are invalid") from exc
        if not isinstance(questions, list) or not questions:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Stored assessment contains no questions")
        return questions

    def get_by_id(self, assessment_id: int):
        record = self.repo.get_by_id(assessment_id)
        if not record:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Generated assessment not found")
        return record

    def get_by_content_id(self, content_id: int):
        record = self.repo.get_by_content_id(content_id)
        if not record:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"No generated assessment for content_id={content_id}")
        return record

    def get_all(self, skip: int = 0, limit: int = 100):
        return self.repo.get_all(skip, limit)


    def list_for_user(self, user_id: int, skip: int = 0, limit: int = 100):
        onboarding = OnboardingRepository(self.db).get_by_user(user_id)
        if not onboarding:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "Complete onboarding before requesting assessments",
            )
        return self.repo.list_by_onboarding(onboarding.onboarding_id, skip, limit)

    def generate_for_content(self, content_id: int, num_questions: int = 10, category: CategoryEnum | None = None):
        content = self.content_repo.get_by_id(content_id)
        if not content:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Content record not found")
        gemini = self.gemini or GeminiClient()
        try:
            quiz = gemini.generate_quiz(
                media_description=content.media_description,
                source_platform=content.source_platform,
                external_media_url=content.external_media_url,
                num_questions=num_questions,
                category_hint=category.value if category else None,
            )
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Gemini assessment generation failed: {exc}") from exc

        if not quiz or not quiz.get("questions"):
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Gemini returned no assessment questions")
        resolved_category = quiz.get("category", CategoryEnum.CAREER_READINESS.value)
        allowed = {c.value for c in CategoryEnum}
        if resolved_category not in allowed:
            resolved_category = CategoryEnum.CAREER_READINESS.value

        record = self.repo.upsert(
            content_id=content_id,
            category=resolved_category,
            questions_json=json.dumps(quiz["questions"], ensure_ascii=False),
            model_used=gemini.model,
        )
        self.db.commit()
        self.db.refresh(record)
        return record

    def assert_user_can_access_content(self, user_id: int, content_id: int):
        pathways = self.pathway_repo.get_by_content(content_id)
        user_pathways = [p for p in pathways if p.onboarding and p.onboarding.user_id == user_id]
        if not user_pathways:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "This content is not in the user's pathway")
        if not any(p.watched for p in user_pathways):
            raise HTTPException(status.HTTP_409_CONFLICT, "Mark the content as watched before generating or starting its assessment")

    def generate_for_all(self, num_questions: int = 10, skip_existing: bool = True):
        contents = self.content_repo.get_all(skip=0, limit=10000)
        generated, skipped, failed = [], [], []
        for content in contents:
            if skip_existing and self.repo.get_by_content_id(content.content_id):
                skipped.append(content.content_id)
                continue
            try:
                generated.append(self.generate_for_content(content.content_id, num_questions=num_questions))
            except Exception as exc:
                failed.append({"content_id": content.content_id, "error": str(exc)})
        if not generated and failed:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, {"message": "Gemini failed to generate assessments", "failed": failed})
        return {"generated": generated, "skipped_existing": skipped, "failed": failed, "message": "Assessments generated successfully"}
