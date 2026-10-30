from __future__ import annotations

import os
from typing import Any
from urllib.parse import urlparse

import httpx
from dotenv import load_dotenv

load_dotenv()

SERPER_SEARCH_URL = os.getenv("SERPER_URL", "https://google.serper.dev/search" )


class SerperClient:
    _SOCIAL_DOMAINS: dict[str, str] = {
        "tiktok": "tiktok.com",
        "instagram": "instagram.com",
        "facebook": "facebook.com",
        "linkedin": "linkedin.com",
    }

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("SERPER_API_KEY")
        if not self.api_key:
            raise RuntimeError("SERPER_API_KEY is not configured")

    def _headers(self) -> dict[str, str]:
        return {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json",
        }

    @staticmethod
    def _clean_result(item: dict[str, Any]) -> dict[str, str] | None:
        title = str(item.get("title") or "").strip()
        url = str(item.get("link") or "").strip()
        description = str(item.get("snippet") or "").strip()

        parsed_url = urlparse(url)
        if not url or parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            return None

        return {
            "title": title,
            "url": url,
            "description": description,
        }

    def search(self, query: str, num_results: int = 10) -> list[dict[str, str]]:
        payload = {"q": query, "num": min(max(num_results, 1), 20)}
        try:
            with httpx.Client(timeout=20.0) as client:
                response = client.post(
                    SERPER_SEARCH_URL,
                    json=payload,
                    headers=self._headers(),
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Serper API request failed: {exc}") from exc

        results: list[dict[str, str]] = []
        for item in data.get("organic", []):
            if not isinstance(item, dict):
                continue
            cleaned = self._clean_result(item)
            if cleaned:
                results.append(cleaned)
        return results

    async def search_async(self, query: str, num_results: int = 10) -> list[dict[str, str]]:
        payload = {"q": query, "num": min(max(num_results, 1), 20)}
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(
                    SERPER_SEARCH_URL,
                    json=payload,
                    headers=self._headers(),
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Serper API request failed: {exc}") from exc

        results: list[dict[str, str]] = []
        for item in data.get("organic", []):
            if not isinstance(item, dict):
                continue
            cleaned = self._clean_result(item)
            if cleaned:
                results.append(cleaned)
        return results

    async def search_social(self, platform: str, keyword: str, num_results: int = 10) -> list[dict[str, str]]:
        """
        Search for social media content WITHOUT using the site: operator.
        Instead, we search naturally and then filter the URLs by domain.
        """
        normalized_platform = platform.strip().lower()
        domain = self._SOCIAL_DOMAINS.get(normalized_platform)
        if not domain:
            raise ValueError(f"Unsupported Serper social platform: {platform}")

        query = f"{normalized_platform} {keyword} tutorial OR course"

        results = await self.search_async(query, num_results * 3)

        filtered = [
            {
                "platform": normalized_platform,
                "title": r["title"],
                "url": r["url"],
                "description": r["description"],
            }
            for r in results
            if domain in urlparse(r["url"]).netloc.lower()
        ]

        return filtered[:num_results]
