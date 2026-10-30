from __future__ import annotations
import json
import os
import time
from typing import Any, Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")


class _GenQuestion(BaseModel):
    question: str
    options: list[str] = Field(min_length=4, max_length=4)
    correct_index: int = Field(ge=0, le=3)
    explanation: str


class _GenQuizResponse(BaseModel):
    category: str
    questions: list[_GenQuestion]


class _RankedItem(BaseModel):
    index: int
    score: int = Field(ge=0, le=100)
    reason: str


class _RankedResponse(BaseModel):
    items: list[_RankedItem]


class GeminiClient:
    def __init__(self, api_key: Optional[str] = None, model: str = GEMINI_MODEL):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured")
        self.model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def _json_call(self, prompt: str, response_schema: Any, retries: int = 2):
        from google.genai import types
        last_exc: Exception | None = None
        
        for attempt in range(retries + 1):
            try:
                response = self._get_client().models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=response_schema,
                        temperature=0.2,
                    ),
                )
                
                if response and response.parsed is not None:
                    return response.parsed.model_dump()
                if response and response.text:
                    return json.loads(response.text)
                    
                raise RuntimeError("Gemini returned an empty response")
                
            except Exception as exc:
                last_exc = exc
                print(f"⚠️ [GEMINI API ERROR] Attempt {attempt + 1} failed: {exc}")
                if attempt < retries:
                    time.sleep(2.0)
                    
        raise RuntimeError(f"Gemini call failed after {retries + 1} attempts: {last_exc}")

    def generate_quiz(
        self,
        media_description: str,
        source_platform: str,
        external_media_url: str,
        num_questions: int = 10,
        category_hint: Optional[str] = None,
    ) -> dict:
        prompt = f"""
You are the assessment engine for VUKA.
Create exactly {num_questions} multiple-choice questions from ONLY the supplied content description.
The URL is context only and must not be used as a knowledge source.
Each question must have exactly four options and exactly one correct answer.
correct_index is zero-based. Include a concise explanation.
Classify the content as exactly one of: technical_skills, soft_skills, career_readiness, digital_literacy.
Questions should test understanding and application rather than trivia.

Source platform: {source_platform}
Content URL: {external_media_url}
Content description:
{media_description}
"""
        if category_hint:
            prompt += f"\nPreferred category when appropriate: {category_hint}\n"
            
        data = self._json_call(prompt, _GenQuizResponse)
        result = _GenQuizResponse.model_validate(data)
        
        if len(result.questions) != num_questions:
            raise RuntimeError(f"Gemini returned {len(result.questions)} questions; expected {num_questions}")
            
        return result.model_dump()

    def rank_content(self, profile: dict[str, Any], candidates: list[dict[str, Any]], limit: int = 10) -> list[dict[str, Any]]:
        if not candidates:
            return []
            
        prompt = f"""
You are VUKA's content-matching engine.
Rank educational content for one Kenyan high-school graduate using their onboarding profile.
Match primarily on stated interests, career aspirations, goals, and selected platforms.
Do not invent facts about a candidate or content item.
Return only the most relevant items, at most {limit}.

USER PROFILE:
{json.dumps(profile, ensure_ascii=False)}

CANDIDATES (index is the candidate identifier):
{json.dumps(candidates, ensure_ascii=False)}
"""
        data = self._json_call(prompt, _RankedResponse)
        ranked = _RankedResponse.model_validate(data).items
        
        output = []
        seen = set()
        for item in sorted(ranked, key=lambda x: x.score, reverse=True):
            if 0 <= item.index < len(candidates) and item.index not in seen:
                candidate = dict(candidates[item.index])
                candidate["relevance_score"] = item.score
                candidate["relevance_reason"] = item.reason
                output.append(candidate)
                seen.add(item.index)
                if len(output) >= limit:
                    break
        return output

    def rank_opportunities(
        self,
        profile: dict[str, Any],
        performance_tier: str,
        candidates: list[dict[str, Any]],
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        if not candidates:
            return []
            
        prompt = f"""
You are VUKA's opportunity-matching engine.
Rank opportunities for a Kenyan learner using their onboarding profile and verified assessment performance.
Performance tiers:
- High (75-100): may unlock unlimited opportunities.
- Average (50-74): may unlock limited opportunities.
- Low (0-49): no opportunities should be returned.
Do not recommend opportunities unrelated to the learner's interests, goals, or career aspirations.
Do not invent eligibility requirements.

PERFORMANCE TIER: {performance_tier}
USER PROFILE:
{json.dumps(profile, ensure_ascii=False)}

CANDIDATES:
{json.dumps(candidates, ensure_ascii=False)}
"""
        data = self._json_call(prompt, _RankedResponse)
        ranked = _RankedResponse.model_validate(data).items
        
        output = []
        seen = set()
        for item in sorted(ranked, key=lambda x: x.score, reverse=True):
            if 0 <= item.index < len(candidates) and item.index not in seen:
                candidate = dict(candidates[item.index])
                candidate["match_score"] = item.score
                candidate["match_reason"] = item.reason
                output.append(candidate)
                seen.add(item.index)
                if len(output) >= limit:
                    break
        return output
