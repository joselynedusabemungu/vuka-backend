from __future__ import annotations

import asyncio
import os
from typing import Any

from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv()


class YouTubeClient:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("YOUTUBE_API_KEY")
        if not self.api_key:
            raise RuntimeError("YOUTUBE_API_KEY is not configured")

    def _search_sync(self, keyword: str, max_results: int) -> list[dict[str, str]]:
        youtube = build(
            "youtube",
            "v3",
            developerKey=self.api_key,
            cache_discovery=False,
        )

        response = (
            youtube.search()
            .list(
                part="snippet",
                q=keyword,
                type="video",
                maxResults=max_results,
            )
            .execute()
        )

        results: list[dict[str, str]] = []
        for item in response.get("items", []):
            item_id: dict[str, Any] = item.get("id", {})
            snippet: dict[str, Any] = item.get("snippet", {})
            video_id = item_id.get("videoId")

            if not video_id:
                continue

            results.append(
                {
                    "platform": "youtube",
                    "title": str(snippet.get("title") or "").strip(),
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "description": str(snippet.get("description") or "").strip(),
                }
            )

        return results

    async def search(self, keyword: str, max_results: int = 10) -> list[dict[str, str]]:
        try:
            return await asyncio.to_thread(
                self._search_sync,
                keyword,
                max_results,
            )
        except HttpError as exc:
            raise RuntimeError(f"YouTube Data API request failed: {exc}") from exc
        except Exception as exc:
            raise RuntimeError(f"YouTube search failed: {exc}") from exc
