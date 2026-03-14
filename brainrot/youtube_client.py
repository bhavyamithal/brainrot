"""YouTube Data API v3 client with quota management.

This module provides a YouTube API client with OAuth 2.0 authentication
and daily quota tracking to ensure compliance with API limits.

Classes:
    QuotaManager: Tracks and persists daily API quota usage.
    YouTubeClient: Handles OAuth authentication and video operations.

Quota Costs (YouTube Data API v3):
    - Video upload: 1,600 units
    - Default daily quota: 10,000 units
    - Quota resets at midnight UTC
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from brainrot.config import settings
from brainrot.exceptions import AuthenticationError, QuotaExceededError, UploadFailedError
from brainrot.types import UploadResult, Video

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
DEFAULT_DAILY_QUOTA = 10000
UPLOAD_QUOTA_COST = 1600

__all__ = ["QuotaManager", "YouTubeClient", "SCOPES", "DEFAULT_DAILY_QUOTA", "UPLOAD_QUOTA_COST"]


class QuotaManager:
    """Manages YouTube API daily quota tracking with persistence.

    Tracks quota usage per day and persists to a JSON file. Automatically
    resets quota when a new day begins (UTC timezone).

    Attributes:
        quota_file: Path to the JSON file for quota persistence.
        daily_quota: Maximum quota units per day.
        upload_cost: Quota cost per video upload.

    Example:
        >>> qm = QuotaManager()
        >>> qm.can_upload()  # Check if quota available
        True
        >>> qm.record_upload()  # Record an upload (1600 units)
        >>> qm.remaining_quota()
        8400
    """

    def __init__(
        self,
        quota_file: Path | None = None,
        daily_quota: int = DEFAULT_DAILY_QUOTA,
        upload_cost: int = UPLOAD_QUOTA_COST,
    ) -> None:
        """Initialize the QuotaManager.

        Args:
            quota_file: Path to JSON file for persistence. Defaults to
                       cache_dir/youtube_quota.json from settings.
            daily_quota: Maximum quota units per day. Defaults to 10000.
            upload_cost: Quota cost per video upload. Defaults to 1600.
        """
        self.quota_file = quota_file or settings.cache_dir / "youtube_quota.json"
        self.daily_quota = daily_quota
        self.upload_cost = upload_cost

        self.quota_file.parent.mkdir(parents=True, exist_ok=True)

        self._date: str = self._get_today_str()
        self._used_quota: int = 0
        self._load_state()

    def _get_today_str(self) -> str:
        """Get today's date as ISO format string (UTC)."""
        return datetime.now(timezone.utc).date().isoformat()

    def _load_state(self) -> None:
        """Load quota state from JSON file."""
        if self.quota_file.exists():
            try:
                with open(self.quota_file, "r") as f:
                    data = json.load(f)
                stored_date = data.get("date", "")
                if stored_date == self._date:
                    self._used_quota = data.get("used_quota", 0)
                    self._date = stored_date
                    logger.debug(f"Loaded quota state: {self._used_quota}/{self.daily_quota}")
                else:
                    logger.info(f"New day detected ({self._date}), resetting quota")
                    self._used_quota = 0
                    self._save_state()
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to load quota state: {e}, starting fresh")
                self._used_quota = 0
                self._save_state()
        else:
            self._save_state()

    def _save_state(self) -> None:
        """Save current quota state to JSON file."""
        data = {
            "date": self._date,
            "used_quota": self._used_quota,
            "daily_quota": self.daily_quota,
        }
        with open(self.quota_file, "w") as f:
            json.dump(data, f, indent=2)
        logger.debug(f"Saved quota state: {self._used_quota}/{self.daily_quota}")

    def _reset_if_new_day(self) -> None:
        """Check if date has changed and reset quota if needed."""
        today = self._get_today_str()
        if today != self._date:
            logger.info(f"Date changed from {self._date} to {today}, resetting quota")
            self._date = today
            self._used_quota = 0
            self._save_state()

    def record_upload(self, units: int | None = None) -> None:
        """Record an upload and deduct quota units.

        Args:
            units: Number of quota units to deduct. Defaults to upload_cost.

        Raises:
            QuotaExceededError: If recording would exceed daily quota.
        """
        self._reset_if_new_day()
        units_to_use = units if units is not None else self.upload_cost

        if self._used_quota + units_to_use > self.daily_quota:
            raise QuotaExceededError(
                "YouTube daily quota would be exceeded",
                {
                    "used": self._used_quota,
                    "requested": units_to_use,
                    "limit": self.daily_quota,
                    "remaining": self.remaining_quota(),
                },
            )

        self._used_quota += units_to_use
        self._save_state()
        logger.info(f"Recorded upload: {units_to_use} units, total used: {self._used_quota}")

    def remaining_quota(self) -> int:
        """Get remaining quota for today.

        Returns:
            Number of quota units remaining.
        """
        self._reset_if_new_day()
        return max(0, self.daily_quota - self._used_quota)

    def can_upload(self, units: int | None = None) -> bool:
        """Check if enough quota remains for an upload.

        Args:
            units: Units required. Defaults to upload_cost.

        Returns:
            True if upload is possible, False otherwise.
        """
        self._reset_if_new_day()
        units_to_use = units if units is not None else self.upload_cost
        return self._used_quota + units_to_use <= self.daily_quota

    def used_quota(self) -> int:
        """Get total used quota for today.

        Returns:
            Number of quota units used.
        """
        self._reset_if_new_day()
        return self._used_quota

    def uploads_remaining(self) -> int:
        """Get number of uploads possible with remaining quota.

        Returns:
            Number of uploads that can be performed.
        """
        self._reset_if_new_day()
        return self.remaining_quota() // self.upload_cost


class YouTubeClient:
    """YouTube Data API v3 client with OAuth 2.0 authentication.

    Handles OAuth flow, video uploads, and analytics retrieval.

    Attributes:
        credentials_path: Path to stored OAuth credentials.
        secrets_path: Path to OAuth client secrets file.
        quota_manager: QuotaManager instance for tracking usage.

    Example:
        >>> client = YouTubeClient()
        >>> client.authenticate()  # Run OAuth flow if needed
        >>> result = client.upload_video(video, "Title", "Description", ["tag1"])
    """

    def __init__(
        self,
        credentials_path: Path | None = None,
        secrets_path: Path | None = None,
        quota_manager: QuotaManager | None = None,
    ) -> None:
        """Initialize the YouTubeClient.

        Args:
            credentials_path: Path to stored credentials. Defaults to
                            settings.youtube_credentials_file.
            secrets_path: Path to client secrets file. Defaults to
                         settings.youtube_client_secrets_file.
            quota_manager: QuotaManager instance. Creates new one if None.
        """
        self.credentials_path = credentials_path or settings.youtube_credentials_file
        self.secrets_path = secrets_path or settings.youtube_client_secrets_file
        self.quota_manager = quota_manager or QuotaManager()
        self._credentials: Credentials | None = None
        self._youtube: Any = None

    def authenticate(self) -> None:
        """Authenticate with YouTube via OAuth 2.0.

        Loads existing credentials from file or runs the OAuth flow
        to obtain new credentials. Credentials are saved for reuse.

        Raises:
            AuthenticationError: If authentication fails.
        """
        try:
            if self.credentials_path.exists():
                self._credentials = Credentials.from_authorized_user_file(
                    str(self.credentials_path), SCOPES
                )
                logger.info("Loaded existing YouTube credentials")

            if not self._credentials or not self._credentials.valid:
                if self._credentials and self._credentials.expired and self._credentials.refresh_token:
                    logger.info("Refreshing expired credentials")
                    self._credentials.refresh(Request())
                else:
                    logger.info("Running OAuth flow for new credentials")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(self.secrets_path), SCOPES
                    )
                    self._credentials = flow.run_local_server(port=0)

                self._save_credentials()
                logger.info("YouTube authentication successful")

            self._youtube = build("youtube", "v3", credentials=self._credentials)

        except Exception as e:
            raise AuthenticationError(
                f"YouTube authentication failed: {e}",
                {"credentials_path": str(self.credentials_path)},
            ) from e

    def _save_credentials(self) -> None:
        """Save credentials to file for reuse."""
        if self._credentials:
            creds_data = {
                "token": self._credentials.token,
                "refresh_token": self._credentials.refresh_token,
                "token_uri": self._credentials.token_uri,
                "client_id": self._credentials.client_id,
                "client_secret": self._credentials.client_secret,
                "scopes": self._credentials.scopes,
            }
            self.credentials_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.credentials_path, "w") as f:
                json.dump(creds_data, f)
            logger.debug(f"Saved credentials to {self.credentials_path}")

    def upload_video(
        self,
        video: Video,
        title: str,
        description: str,
        tags: list[str],
        category_id: str = "22",
        privacy_status: str = "private",
    ) -> UploadResult:
        if not self._youtube:
            self.authenticate()

        if not self.quota_manager.can_upload():
            raise QuotaExceededError(
                "Cannot upload: daily quota exceeded",
                {
                    "remaining": self.quota_manager.remaining_quota(),
                    "required": self.quota_manager.upload_cost,
                },
            )

        try:
            body = {
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": tags,
                    "categoryId": category_id,
                },
                "status": {
                    "privacyStatus": privacy_status,
                    "selfDeclaredMadeForKids": False,
                },
            }

            media = MediaFileUpload(
                str(video.path),
                chunksize=1024 * 1024,
                resumable=True,
            )

            logger.info(f"Starting upload: {title}")
            request = self._youtube.videos().insert(
                part=",".join(body.keys()),
                body=body,
                media_body=media,
            )

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    logger.debug(f"Upload progress: {progress}%")

            self.quota_manager.record_upload()

            video_id = response.get("id")
            logger.info(f"Upload complete: video ID {video_id}")

            return UploadResult(
                video_id=video.id,
                platform="youtube",
                external_id=video_id,
                status="success",
                uploaded_at=datetime.now(timezone.utc),
            )

        except HttpError as e:
            error_details = {}
            try:
                error_details = json.loads(e.content.decode()).get("error", {})
            except Exception:
                pass

            raise UploadFailedError(
                f"YouTube upload failed: {e}",
                {
                    "video_id": video.id,
                    "status_code": e.resp.status,
                    "error_details": error_details,
                },
            ) from e

        except Exception as e:
            raise UploadFailedError(
                f"Unexpected error during upload: {e}",
                {"video_id": video.id},
            ) from e

    def get_video_analytics(self, video_id: str) -> dict[str, Any]:
        if not self._youtube:
            self.authenticate()

        try:
            request = self._youtube.videos().list(
                part="snippet,statistics",
                id=video_id,
            )
            response = request.execute()

            if not response.get("items"):
                return {
                    "views": 0,
                    "likes": 0,
                    "comments": 0,
                    "title": "",
                    "published_at": None,
                    "error": "Video not found",
                }

            item = response["items"][0]
            stats = item.get("statistics", {})
            snippet = item.get("snippet", {})

            return {
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "comments": int(stats.get("commentCount", 0)),
                "title": snippet.get("title", ""),
                "published_at": snippet.get("publishedAt"),
            }

        except HttpError as e:
            logger.error(f"Failed to fetch analytics for {video_id}: {e}")
            return {
                "views": 0,
                "likes": 0,
                "comments": 0,
                "title": "",
                "published_at": None,
                "error": str(e),
            }

    def get_channel_info(self) -> dict[str, Any]:
        if not self._youtube:
            self.authenticate()

        try:
            request = self._youtube.channels().list(
                part="snippet,statistics",
                mine=True,
            )
            response = request.execute()

            if not response.get("items"):
                return {
                    "id": None,
                    "title": "",
                    "subscriber_count": 0,
                    "video_count": 0,
                }

            item = response["items"][0]
            stats = item.get("statistics", {})
            snippet = item.get("snippet", {})

            return {
                "id": item.get("id"),
                "title": snippet.get("title", ""),
                "subscriber_count": int(stats.get("subscriberCount", 0)),
                "video_count": int(stats.get("videoCount", 0)),
            }

        except HttpError as e:
            logger.error(f"Failed to fetch channel info: {e}")
            return {
                "id": None,
                "title": "",
                "subscriber_count": 0,
                "video_count": 0,
                "error": str(e),
            }
