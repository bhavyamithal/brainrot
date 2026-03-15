"""Upload orchestration with quota management and queue persistence.

Manages video upload queue, enforces daily limits, handles retries,
and provides human review checkpoints for uploaded content.
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from brainrot.exceptions import QuotaExceededError, UploadFailedError, retry
from brainrot.types import Script, UploadResult, Video
from brainrot.youtube_client import QuotaManager, YouTubeClient

logger = logging.getLogger(__name__)

MAX_UPLOADS_PER_DAY = 5


def _get_default_queue_file() -> Path:
    from brainrot.config import settings
    return settings.cache_dir / "upload_queue.json"


class UploadStatus(str, Enum):
    PENDING = "pending"
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    FAILED = "failed"


@dataclass
class QueuedVideo:
    video_path: Path
    script: Script
    status: UploadStatus = UploadStatus.PENDING
    scheduled_at: datetime | None = None
    uploaded_at: datetime | None = None
    external_id: str | None = None
    error: str | None = None
    retry_count: int = 0
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "video_path": str(self.video_path),
            "script": self.script.model_dump(mode="json"),
            "status": self.status.value,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
            "external_id": self.external_id,
            "error": self.error,
            "retry_count": self.retry_count,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> QueuedVideo:
        return cls(
            id=data["id"],
            video_path=Path(data["video_path"]),
            script=Script(**data["script"]),
            status=UploadStatus(data["status"]),
            scheduled_at=datetime.fromisoformat(data["scheduled_at"]) if data.get("scheduled_at") else None,
            uploaded_at=datetime.fromisoformat(data["uploaded_at"]) if data.get("uploaded_at") else None,
            external_id=data.get("external_id"),
            error=data.get("error"),
            retry_count=data.get("retry_count", 0),
            created_at=datetime.fromisoformat(data["created_at"]),
        )


class UploadQueue:
    def __init__(self, queue_file: Path | None = None) -> None:
        self.queue_file = queue_file or _get_default_queue_file()
        self.queue_file.parent.mkdir(parents=True, exist_ok=True)
        self._queue: list[QueuedVideo] = self._load()

    def _load(self) -> list[QueuedVideo]:
        if not self.queue_file.exists():
            return []

        try:
            with open(self.queue_file, "r") as f:
                data = json.load(f)
            return [QueuedVideo.from_dict(item) for item in data.get("queue", [])]
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to load queue from {self.queue_file}: {e}")
            return []

    def _save(self) -> None:
        data = {
            "queue": [item.to_dict() for item in self._queue],
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        with open(self.queue_file, "w") as f:
            json.dump(data, f, indent=2)

    def add(self, video: QueuedVideo) -> None:
        self._queue.append(video)
        self._save()
        logger.info(f"Added video to queue: {video.id}")

    def get_pending(self) -> list[QueuedVideo]:
        return [v for v in self._queue if v.status == UploadStatus.PENDING]

    def get_failed(self, max_retries: int = 3) -> list[QueuedVideo]:
        return [v for v in self._queue if v.status == UploadStatus.FAILED and v.retry_count < max_retries]

    def get_by_id(self, video_id: str) -> QueuedVideo | None:
        for v in self._queue:
            if v.id == video_id:
                return v
        return None

    def update(self, video: QueuedVideo) -> None:
        for i, v in enumerate(self._queue):
            if v.id == video.id:
                self._queue[i] = video
                self._save()
                return

    def count_by_status(self, status: UploadStatus) -> int:
        return sum(1 for v in self._queue if v.status == status)

    @property
    def length(self) -> int:
        return len(self._queue)

    @property
    def pending_count(self) -> int:
        return self.count_by_status(UploadStatus.PENDING)

    @property
    def uploaded_today(self) -> int:
        today = datetime.now(timezone.utc).date()
        return sum(
            1 for v in self._queue
            if v.status == UploadStatus.UPLOADED
            and v.uploaded_at
            and v.uploaded_at.date() == today
        )


class UploadOrchestrator:
    def __init__(
        self,
        youtube_client: YouTubeClient | None = None,
        quota_manager: QuotaManager | None = None,
        queue_file: Path | None = None,
        max_uploads_per_day: int = MAX_UPLOADS_PER_DAY,
    ) -> None:
        self._youtube_client = youtube_client
        self._quota_manager = quota_manager
        self._queue = UploadQueue(queue_file)
        self._max_uploads_per_day = max_uploads_per_day
        self._uploaded_today = 0

    @property
    def youtube_client(self) -> YouTubeClient:
        if self._youtube_client is None:
            self._youtube_client = YouTubeClient(quota_manager=self.quota_manager)
        return self._youtube_client

    @property
    def quota_manager(self) -> QuotaManager:
        if self._quota_manager is None:
            self._quota_manager = QuotaManager()
        return self._quota_manager

    @property
    def uploads_today(self) -> int:
        return self._queue.uploaded_today

    @property
    def queue_length(self) -> int:
        return self._queue.length

    @property
    def pending_count(self) -> int:
        return self._queue.pending_count

    def queue_video(
        self,
        video_path: Path,
        script: Script,
        scheduled_at: datetime | None = None,
    ) -> QueuedVideo:
        queued = QueuedVideo(
            video_path=video_path,
            script=script,
            scheduled_at=scheduled_at,
        )
        self._queue.add(queued)
        logger.info(f"Queued video {queued.id} from {video_path}")
        return queued

    def _generate_metadata(self, script: Script) -> dict[str, Any]:
        title = script.hook if script.hook else script.text[:60].strip()
        if len(title) > 60:
            title = title[:57] + "..."

        description_parts = [
            script.text,
            "",
            "#shorts #viral #trending",
        ]
        description = "\n".join(description_parts)

        words = script.text.lower().split()
        word_freq: dict[str, int] = {}
        for word in words:
            clean = "".join(c for c in word if c.isalnum())
            if len(clean) > 3:
                word_freq[clean] = word_freq.get(clean, 0) + 1

        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        tags = [word for word, _ in sorted_words[:10]]
        tags.extend(["shorts", "viral", "trending"])

        return {
            "title": title,
            "description": description,
            "tags": tags,
        }

    def _should_upload(self) -> bool:
        if self._queue.uploaded_today >= self._max_uploads_per_day:
            logger.info(f"Daily upload limit reached: {self._queue.uploaded_today}/{self._max_uploads_per_day}")
            return False

        if not self.quota_manager.can_upload():
            logger.info("YouTube quota exhausted")
            return False

        return True

    def _create_video_object(self, queued: QueuedVideo) -> Video:
        return Video(
            id=queued.id,
            script_id=queued.script.id,
            path=queued.video_path,
            duration=0.0,
        )

    @retry(max_attempts=3, backoff_factor=2.0, exceptions=(UploadFailedError,))
    def _upload_with_retry(
        self,
        queued: QueuedVideo,
        metadata: dict[str, Any],
    ) -> UploadResult:
        video = self._create_video_object(queued)

        return self.youtube_client.upload_video(
            video=video,
            title=metadata["title"],
            description=metadata["description"],
            tags=metadata["tags"],
        )

    def _process_single(self, queued: QueuedVideo, human_review: bool) -> UploadResult | None:
        if not self._should_upload():
            logger.info(f"Skipping upload for {queued.id}: quota or limit reached")
            return None

        if human_review:
            metadata = self._generate_metadata(queued.script)
            logger.info(f"Human review required for {queued.id}:")
            logger.info(f"  Title: {metadata['title']}")
            logger.info(f"  Tags: {', '.join(metadata['tags'][:5])}...")
            return None

        queued.status = UploadStatus.UPLOADING
        self._queue.update(queued)

        metadata = self._generate_metadata(queued.script)

        try:
            result = self._upload_with_retry(queued, metadata)

            queued.status = UploadStatus.UPLOADED
            queued.uploaded_at = datetime.now(timezone.utc)
            queued.external_id = result.external_id
            self._queue.update(queued)

            logger.info(f"Successfully uploaded {queued.id} as {result.external_id}")
            return result

        except QuotaExceededError as e:
            queued.status = UploadStatus.FAILED
            queued.error = str(e)
            self._queue.update(queued)
            logger.warning(f"Quota exceeded for {queued.id}: {e}")
            return None

        except UploadFailedError as e:
            queued.status = UploadStatus.FAILED
            queued.error = str(e)
            queued.retry_count += 1
            self._queue.update(queued)
            logger.error(f"Upload failed for {queued.id} (attempt {queued.retry_count}): {e}")
            raise

        except Exception as e:
            queued.status = UploadStatus.FAILED
            queued.error = f"Unexpected error: {e}"
            queued.retry_count += 1
            self._queue.update(queued)
            logger.error(f"Unexpected error uploading {queued.id}: {e}")
            raise UploadFailedError(f"Upload failed: {e}", {"video_id": queued.id}) from e

    def process_queue(
        self,
        human_review: bool = True,
        max_uploads: int | None = None,
    ) -> list[UploadResult]:
        results: list[UploadResult] = []
        max_to_upload = max_uploads or self._max_uploads_per_day

        pending = self._queue.get_pending()
        failed = self._queue.get_failed(max_retries=3)
        to_process = pending + failed

        logger.info(f"Processing queue: {len(pending)} pending, {len(failed)} for retry")

        uploaded_count = 0
        for queued in to_process:
            if uploaded_count >= max_to_upload:
                logger.info(f"Reached max uploads for this run: {max_to_upload}")
                break

            if not self._should_upload():
                break

            try:
                result = self._process_single(queued, human_review)
                if result:
                    results.append(result)
                    uploaded_count += 1
            except UploadFailedError:
                continue

        logger.info(f"Queue processing complete: {len(results)} uploads")
        return results

    def get_queue_status(self) -> dict[str, Any]:
        return {
            "total": self._queue.length,
            "pending": self._queue.count_by_status(UploadStatus.PENDING),
            "uploading": self._queue.count_by_status(UploadStatus.UPLOADING),
            "uploaded": self._queue.count_by_status(UploadStatus.UPLOADED),
            "failed": self._queue.count_by_status(UploadStatus.FAILED),
            "uploaded_today": self._queue.uploaded_today,
            "remaining_quota": self.quota_manager.remaining_quota(),
            "uploads_remaining": min(
                self._max_uploads_per_day - self._queue.uploaded_today,
                self.quota_manager.uploads_remaining(),
            ),
        }
