from __future__ import annotations

import os
from typing import Any
from urllib.parse import unquote

import httpx

OPEN_TRIVIA_URL = os.getenv("OPEN_TRIVIA_URL")


class OpenTriviaClient:
    async def fetch_questions(
        self, amount: int = 10, category: int | None = None, difficulty: str = "medium"
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {
            "amount": amount,
            "type": "multiple",
            "difficulty": difficulty,
            "encode": "url3986",
        }
        if category is not None:
            params["category"] = category

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(OPEN_TRIVIA_URL, params=params)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Open Trivia Database request failed: {exc}") from exc

        response_code = data.get("response_code")
        if response_code != 0:
            messages = {
                1: "No questions are available for the requested criteria.",
                2: "Open Trivia Database received invalid parameters.",
                3: "Open Trivia Database session token was not found.",
                4: "Open Trivia Database session token is empty.",
                5: "Open Trivia Database rate limit reached.",
            }
            raise RuntimeError(
                messages.get(
                    response_code,
                    f"Open Trivia Database returned response code {response_code}.",
                )
            )

        questions: list[dict[str, Any]] = []
        for item in data.get("results", []):
            questions.append(
                {
                    "category": unquote(str(item.get("category", ""))),
                    "difficulty": unquote(str(item.get("difficulty", ""))),
                    "question": unquote(str(item.get("question", ""))),
                    "correct_answer": unquote(str(item.get("correct_answer", ""))),
                    "incorrect_answers": [
                        unquote(str(answer))
                        for answer in item.get("incorrect_answers", [])
                    ],
                }
            )

        return questions
