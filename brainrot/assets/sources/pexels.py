"""Pexels stock footage source.

Pexels provides free stock videos via their API.
API Documentation: https://www.pexels.com/api/documentation/
"""

from __future__ import annotations

import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)

# Default API key for Pexels (free tier - can be overridden)
# Users should get their own key at https://www.pexels.com/api/new/
PEXELS_DEFAULT_API_KEY = "YOUR_PEXELS_API_KEY"

PEXELS_API_BASE = "https://api.pexels.com/videos"


class PexelsSource:
    """Pexels stock footage source for free video content.

    Pexels offers royalty-free stock videos that can be used freely
    for commercial and non-commercial purposes without attribution.

    Attributes:
        api_key: Pexels API key for authentication.
    """

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize Pexels source.

        Args:
            api_key: Pexels API key. If not provided, uses environment
                variable PEXELS_API_KEY or a default key.
        """
        self.api_key = api_key or PEXELS_DEFAULT_API_KEY
        self._session: requests.Session | None = None

    @property
    def session(self) -> requests.Session:
        """Get or create requests session with headers."""
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update({"Authorization": self.api_key})
        return self._session

    def search(
        self,
        query: str,
        limit: int = 10,
        orientation: str | None = None,
        size: str | None = None,
    ) -> list[dict[str, Any]]:
        """Search for stock videos matching the query.

        Args:
            query: Search query string (keywords).
            limit: Maximum number of results to return.
            orientation: Video orientation filter ('landscape', 'portrait', 'square').
            size: Video size filter ('large', 'medium', 'small').

        Returns:
            List of video asset dictionaries with keys:
                - id: Unique asset identifier
                - url: Pexels page URL
                - thumbnail: Thumbnail image URL
                - duration: Video duration in seconds
                - source: Source identifier ('pexels')
                - video_url: Direct video file URL (highest quality)
                - width: Video width in pixels
                - height: Video height in pixels
                - user: Photographer name
                - user_url: Photographer profile URL
        """
        params: dict[str, Any] = {
            "query": query,
            "per_page": min(limit, 80),  # Pexels max is 80
        }

        if orientation:
            params["orientation"] = orientation
        if size:
            params["size"] = size

        try:
            response = self.session.get(f"{PEXELS_API_BASE}/search", params=params)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            logger.error(f"Pexels API request failed: {e}")
            return []

        results = []
        for video in data.get("videos", []):
            # Get the highest quality video file
            video_files = video.get("video_files", [])
            best_file = max(
                video_files,
                key=lambda f: f.get("width", 0) * f.get("height", 0),
                default=None,
            )

            if not best_file:
                continue

            # Get thumbnail from video pictures
            pictures = video.get("video_pictures", [])
            thumbnail = pictures[0].get("picture") if pictures else None

            asset = {
                "id": f"pexels_{video['id']}",
                "url": video.get("url", ""),
                "thumbnail": thumbnail,
                "duration": video.get("duration", 0),
                "source": "pexels",
                "video_url": best_file.get("link", ""),
                "width": best_file.get("width", 0),
                "height": best_file.get("height", 0),
                "user": video.get("user", {}).get("name", "Unknown"),
                "user_url": video.get("user", {}).get("url", ""),
                "license": "Pexels License (free for commercial use)",
            }
            results.append(asset)

        return results[:limit]

    def get_popular(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get popular stock videos.

        Args:
            limit: Maximum number of results to return.

        Returns:
            List of popular video asset dictionaries.
        """
        params = {"per_page": min(limit, 80)}

        try:
            response = self.session.get(f"{PEXELS_API_BASE}/popular", params=params)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            logger.error(f"Pexels API request failed: {e}")
            return []

        results = []
        for video in data.get("videos", []):
            video_files = video.get("video_files", [])
            best_file = max(
                video_files,
                key=lambda f: f.get("width", 0) * f.get("height", 0),
                default=None,
            )

            if not best_file:
                continue

            pictures = video.get("video_pictures", [])
            thumbnail = pictures[0].get("picture") if pictures else None

            asset = {
                "id": f"pexels_{video['id']}",
                "url": video.get("url", ""),
                "thumbnail": thumbnail,
                "duration": video.get("duration", 0),
                "source": "pexels",
                "video_url": best_file.get("link", ""),
                "width": best_file.get("width", 0),
                "height": best_file.get("height", 0),
                "user": video.get("user", {}).get("name", "Unknown"),
                "user_url": video.get("user", {}).get("url", ""),
                "license": "Pexels License (free for commercial use)",
            }
            results.append(asset)

        return results[:limit]

    def get_by_id(self, video_id: int) -> dict[str, Any] | None:
        """Get a specific video by ID.

        Args:
            video_id: Pexels video ID.

        Returns:
            Video asset dictionary or None if not found.
        """
        try:
            response = self.session.get(f"{PEXELS_API_BASE}/videos/{video_id}")
            response.raise_for_status()
            video = response.json()
        except requests.RequestException as e:
            logger.error(f"Pexels API request failed: {e}")
            return None

        video_files = video.get("video_files", [])
        best_file = max(
            video_files,
            key=lambda f: f.get("width", 0) * f.get("height", 0),
            default=None,
        )

        if not best_file:
            return None

        pictures = video.get("video_pictures", [])
        thumbnail = pictures[0].get("picture") if pictures else None

        return {
            "id": f"pexels_{video['id']}",
            "url": video.get("url", ""),
            "thumbnail": thumbnail,
            "duration": video.get("duration", 0),
            "source": "pexels",
            "video_url": best_file.get("link", ""),
            "width": best_file.get("width", 0),
            "height": best_file.get("height", 0),
            "user": video.get("user", {}).get("name", "Unknown"),
            "user_url": video.get("user", {}).get("url", ""),
            "license": "Pexels License (free for commercial use)",
        }
