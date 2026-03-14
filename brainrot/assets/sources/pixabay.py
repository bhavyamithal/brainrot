"""Pixabay stock footage source.

Pixabay provides free stock videos and images via their API.
API Documentation: https://pixabay.com/api/docs/
"""

from __future__ import annotations

import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)

PIXABAY_DEFAULT_API_KEY = "YOUR_PIXABAY_API_KEY"
PIXABAY_API_BASE = "https://pixabay.com/api"


class PixabaySource:
    """Pixabay stock footage source for free video content.

    Pixabay offers royalty-free stock videos released under the
    Pixabay License, which allows free use for commercial purposes.

    Attributes:
        api_key: Pixabay API key for authentication.
    """

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize Pixabay source.

        Args:
            api_key: Pixabay API key. If not provided, uses a default key.
        """
        self.api_key = api_key or PIXABAY_DEFAULT_API_KEY
        self._session: requests.Session | None = None

    @property
    def session(self) -> requests.Session:
        """Get or create requests session."""
        if self._session is None:
            self._session = requests.Session()
        return self._session

    def search(
        self,
        query: str,
        limit: int = 10,
        video_type: str = "all",
        orientation: str | None = None,
        category: str | None = None,
    ) -> list[dict[str, Any]]:
        """Search for stock videos matching the query.

        Args:
            query: Search query string (keywords).
            limit: Maximum number of results to return.
            video_type: Video type filter ('film', 'animation', 'all').
            orientation: Video orientation filter ('horizontal', 'vertical').
            category: Category filter (e.g., 'nature', 'people', 'technology').

        Returns:
            List of video asset dictionaries with keys:
                - id: Unique asset identifier
                - url: Pixabay page URL
                - thumbnail: Thumbnail image URL
                - duration: Video duration in seconds
                - source: Source identifier ('pixabay')
                - video_url: Direct video file URL (medium quality)
                - width: Video width in pixels
                - height: Video height in pixels
                - user: Photographer name
                - tags: List of tags associated with the video
        """
        params: dict[str, Any] = {
            "key": self.api_key,
            "q": query,
            "per_page": min(limit, 200),
            "video_type": video_type,
        }

        if orientation:
            params["orientation"] = orientation
        if category:
            params["category"] = category

        try:
            response = self.session.get(PIXABAY_API_BASE, params=params)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            logger.error(f" Pixabay API request failed: {e}")
            return []

        results = []
        for video in data.get("hits", []):
            videos = video.get("videos", {})
            medium_video = videos.get("medium", {})

            if not medium_video:
                continue

            asset = {
                "id": f"pixabay_{video['id']}",
                "url": video.get("pageURL", ""),
                "thumbnail": video.get("picture_id", ""),
                "duration": video.get("duration", 0),
                "source": "pixabay",
                "video_url": medium_video.get("url", ""),
                "width": medium_video.get("width", 0),
                "height": medium_video.get("height", 0),
                "user": video.get("user", "Unknown"),
                "tags": video.get("tags", "").split(", ") if video.get("tags") else [],
                "views": video.get("views", 0),
                "downloads": video.get("downloads", 0),
                "license": "Pixabay License (free for commercial use)",
            }
            results.append(asset)

        return results[:limit]

    def search_images(
        self,
        query: str,
        limit: int = 10,
        image_type: str = "photo",
        orientation: str | None = None,
    ) -> list[dict[str, Any]]:
        """Search for stock images matching the query.

        Args:
            query: Search query string (keywords).
            limit: Maximum number of results to return.
            image_type: Image type filter ('photo', 'illustration', 'vector').
            orientation: Image orientation filter ('horizontal', 'vertical').

        Returns:
            List of image asset dictionaries.
        """
        params: dict[str, Any] = {
            "key": self.api_key,
            "q": query,
            "per_page": min(limit, 200),
            "image_type": image_type,
        }

        if orientation:
            params["orientation"] = orientation

        try:
            response = self.session.get(PIXABAY_API_BASE, params=params)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            logger.error(f"Pixabay API request failed: {e}")
            return []

        results = []
        for image in data.get("hits", []):
            asset = {
                "id": f"pixabay_img_{image['id']}",
                "url": image.get("pageURL", ""),
                "thumbnail": image.get("previewURL", ""),
                "source": "pixabay",
                "image_url": image.get("largeImageURL", image.get("webformatURL", "")),
                "width": image.get("imageWidth", 0),
                "height": image.get("imageHeight", 0),
                "user": image.get("user", "Unknown"),
                "tags": image.get("tags", "").split(", ") if image.get("tags") else [],
                "views": image.get("views", 0),
                "downloads": image.get("downloads", 0),
                "license": "Pixabay License (free for commercial use)",
            }
            results.append(asset)

        return results[:limit]

    def get_categories(self) -> list[str]:
        """Get list of available categories for filtering.

        Returns:
            List of category names.
        """
        return [
            "backgrounds",
            "fashion",
            "nature",
            "science",
            "education",
            "people",
            "feelings",
            "religion",
            "health",
            "places",
            "animals",
            "industry",
            "food",
            "computer",
            "sports",
            "transportation",
            "travel",
            "buildings",
            "business",
            "music",
        ]
