from __future__ import annotations
import json
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from vuka.repositories.verifiedassessment import VerifiedAssessmentRepository
from vuka.repositories.generated_assessment import GeneratedAssessmentRepository
from vuka.repositories.userprogress import UserProgressRepository
from vuka.models.verifiedassessment import VerifiedAssessment
from vuka.schemas.verifiedassessment import AssessmentProgressUpdate, AssessmentSubmission


class VerifiedAssessmentService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = VerifiedAssessmentRepository(db)
        self.generated_repo = GeneratedAssessmentRepository(db)
        self.progress_repo = UserProgressRepository(db)

    @staticmethod
    def _tier(score: int) -> str:
        if score >= 75:
            return "High"
        if score >= 50:
            return "Average"
        return "Low"

    @staticmethod
    def _tier_payload(tier: str) -> dict:
        return {
            "High": {
                "description": "Exceptional mastery, deep insight, and flawless application.",
                "opportunity_access": "unlimited",
                "can_retake": False,
            },
            "Average": {
                "description": "Satisfactory, grasps the core concepts and meets the basic standards.",
                "opportunity_access": "limited",
                "can_retake": False,
            },
            "Low": {
                "description": "Unsatisfactory, missed core requirements and needs intervention.",
                "opportunity_access": "none",
                "can_retake": True,
            },
        }[tier]

    @staticmethod
    def _parse_questions(generated) -> list[dict]:
        try:
            questions = json.loads(generated.questions)
        except (TypeError, json.JSONDecodeError) as exc:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Stored generated assessment is invalid") from exc
        if not isinstance(questions, list) or not questions:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Generated assessment contains no questions")
        for q in questions:
            if not isinstance(q, dict) or not isinstance(q.get("options"), list) or len(q["options"]) != 4 or not isinstance(q.get("correct_index"), int):
                raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Generated assessment has an invalid question format")
            if not 0 <= q["correct_index"] < 4:
                raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Generated assessment has an invalid answer key")
        return questions

    def _response(self, assessment: VerifiedAssessment, include_questions: bool = True) -> dict:
        generated = self.generated_repo.get_by_id(assessment.generated_assessment_id)
        questions = self._parse_questions(generated)
        safe_questions = [{"question": q["question"], "options": q["options"]} for q in questions] if include_questions else None
        progress = self.progress_repo.get_by_assessment(assessment.assessment_id)
        return {
            "assessment_id": assessment.assessment_id,
            "generated_assessment_id": assessment.generated_assessment_id,
            "user_id": assessment.user_id,
            "category": assessment.category,
            "score": assessment.score,
            "status": assessment.status,
            "answers": assessment.answers or {},
            "current_step": assessment.current_step,
            "performance_tier": assessment.performance_tier,
            "streak_count": progress.streak_count if progress else None,
            "assessment_date": assessment.assessment_date,
            "completed_at": assessment.completed_at,
            "questions": safe_questions,
        }

    def _check_content_access(self, user_id: int, content_id: int):
        from vuka.repositories.content_pathway import ContentPathwayRepository

        pathways = ContentPathwayRepository(self.db).get_by_content(content_id)
        user_pathways = [
            p for p in pathways
            if p.onboarding and p.onboarding.user_id == user_id
        ]

        if not user_pathways:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                "This content is not in the user's pathway",
            )

        if not any(p.watched for p in user_pathways):
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "Mark the content as watched before generating or starting its assessment",
            )

        return user_pathways

    def start(self, user_id: int, generated_assessment_id: int):
        generated = self.generated_repo.get_by_id(generated_assessment_id)
        if not generated:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Generated assessment not found")

        pathways = self._check_content_access(user_id, generated.content_id)

        existing = self.repository.get_by_user_and_generated(user_id, generated_assessment_id, in_progress_only=True)
        if existing:
            return self._response(existing)
        previous = self.repository.get_latest_completed_by_user_and_generated(user_id, generated_assessment_id)
        if previous and previous.performance_tier != "Low":
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "This assessment has already been completed successfully. Only Low-tier assessments can be retaken.",
            )
        assessment = self.repository.create(
            generated_assessment_id=generated_assessment_id,
            user_id=user_id,
            category=generated.category,
            score=0,
            status="in_progress",
            answers={},
            current_step=0,
            performance_tier=None,
            streak_awarded=0,
        )
        self.db.commit()
        self.db.refresh(assessment)
        return self._response(assessment)

    def get_for_user(self, assessment_id: int, user_id: int):
        assessment = self.repository.get_by_id(assessment_id)
        if not assessment:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Assessment attempt not found")
        if assessment.user_id != user_id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Assessment does not belong to the user")
        return self._response(assessment)

    def get_resume(self, user_id: int, generated_assessment_id: int):
        generated = self.generated_repo.get_by_id(generated_assessment_id)
        if not generated:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Generated assessment not found")

        self._check_content_access(user_id, generated.content_id)

        assessment = self.repository.get_by_user_and_generated(user_id, generated_assessment_id, in_progress_only=True)
        if not assessment:
            return None
        return self._response(assessment)

    def save_progress(self, assessment_id: int, user_id: int, payload: AssessmentProgressUpdate):
        assessment = self.repository.get_by_id(assessment_id)
        if not assessment:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Assessment attempt not found")
        if assessment.user_id != user_id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Assessment does not belong to the user")
        if assessment.status == "completed":
            raise HTTPException(status.HTTP_409_CONFLICT, "Completed assessments cannot be edited")

        generated = self.generated_repo.get_by_id(assessment.generated_assessment_id)
        questions = self._parse_questions(generated)
        answers = dict(assessment.answers or {})
        for answer in payload.answers:
            if answer.question_index >= len(questions):
                raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Question index is outside the assessment")
            answers[str(answer.question_index)] = answer.selected_index

        assessment = self.repository.update(assessment_id, {
            "answers": answers,
            "current_step": min(payload.current_step, len(questions)),
        })
        self.db.commit()
        self.db.refresh(assessment)
        return self._response(assessment)

    def _calculate_score(self, questions: list[dict], answers: dict[str, int]) -> int:
        expected = {str(i) for i in range(len(questions))}
        if set(answers.keys()) != expected:
            missing = sorted(expected - set(answers.keys()), key=int)
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"All questions must be answered before submission. Missing: {missing}")
        correct = 0
        for index, question in enumerate(questions):
            selected = answers[str(index)]
            if not isinstance(selected, int) or not 0 <= selected < 4:
                raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Invalid selected option for question {index}")
            correct += selected == question["correct_index"]
        return round(correct / len(questions) * 100)

    def _previous_streak(self, user_id: int, completion_date):
        previous = self.progress_repo.get_most_recent_completed(user_id)
        if not previous or not previous.assessment.completed_at:
            return 1
        previous_date = previous.assessment.completed_at.astimezone(timezone.utc).date()
        gap = (completion_date - previous_date).days
        if gap == 0:
            return previous.streak_count
        if gap == 1:
            return previous.streak_count + 1
        return 1

    def submit(self, assessment_id: int, user_id: int, payload: AssessmentSubmission):
        assessment = self.repository.get_by_id(assessment_id)
        if not assessment:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Assessment attempt not found")
        if assessment.user_id != user_id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Assessment does not belong to the user")
        if assessment.status == "completed":
            return self._response(assessment)

        generated = self.generated_repo.get_by_id(assessment.generated_assessment_id)
        if not generated:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Generated assessment not found")
        questions = self._parse_questions(generated)

        answers = dict(assessment.answers or {})
        for answer in payload.answers:
            if answer.question_index >= len(questions):
                raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Question index is outside the assessment")
            answers[str(answer.question_index)] = answer.selected_index

        score = self._calculate_score(questions, answers)
        tier = self._tier(score)
        completed_at = datetime.now(timezone.utc)
        completion_date = completed_at.date()
        streak = self._previous_streak(user_id, completion_date)

        assessment = self.repository.update(assessment_id, {
            "answers": answers,
            "current_step": len(questions),
            "score": score,
            "status": "completed",
            "performance_tier": tier,
            "streak_awarded": streak,
            "completed_at": completed_at,
        })

        progress = self.progress_repo.get_by_assessment(assessment_id)
        if progress:
            self.progress_repo.update(progress, {"score": score, "streak_count": streak, "performance_tier": tier})
        else:
            progress = self.progress_repo.create({
                "user_id": user_id,
                "assessment_id": assessment_id,
                "score": score,
                "streak_count": streak,
                "performance_tier": tier,
            })

        self.db.commit()
        self.db.refresh(assessment)
        self.db.refresh(progress)
        response = self._response(assessment)
        response["tier_details"] = self._tier_payload(tier)
        response["progress_id"] = progress.progress_id
        return response

    def list_for_user(self, user_id: int):
        return [self._response(a) for a in self.repository.get_all(user_id)]
