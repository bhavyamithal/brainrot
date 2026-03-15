"""YouTube Analytics API integration with SQLite persistence.

Provides fetching, storage, and analysis of YouTube video and channel metrics.
"""

from __future__ import annotations

import asyncio
import csv
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import aiosqlite

logger = logging.getLogger(__name__)


@dataclass
class VideoAnalytics:
    """Per-video performance metrics.

    Attributes:
        video_id: YouTube video ID.
        views: Total view count.
        likes: Total like count.
        comments: Total comment count.
        avg_view_duration: Average view duration in seconds.
        fetched_at: Timestamp when analytics were fetched.
    """

    video_id: str
    views: int = 0
    likes: int = 0
    comments: int = 0
    avg_view_duration: float = 0.0
    fetched_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: int | None = None


@dataclass
class ChannelAnalytics:
    """Channel-level statistics.

    Attributes:
        channel_id: YouTube channel ID.
        subscriber_count: Total subscribers.
        total_views: Total channel view count.
        video_count: Total videos uploaded.
        fetched_at: Timestamp when analytics were fetched.
    """

    channel_id: str
    subscriber_count: int = 0
    total_views: int = 0
    video_count: int = 0
    fetched_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: int | None = None


@dataclass
class VideoGrowth:
    """Video growth metrics for trend detection.

    Attributes:
        video_id: YouTube video ID.
        views_growth: View count growth rate.
        likes_growth: Like count growth rate.
        growth_score: Combined growth score for ranking.
        latest_analytics: Most recent analytics snapshot.
    """

    video_id: str
    views_growth: float = 0.0
    likes_growth: float = 0.0
    growth_score: float = 0.0
    latest_analytics: VideoAnalytics | None = None


class AnalyticsFetcher:
    """Fetches and stores YouTube analytics with SQLite persistence.

    Provides methods for:
    - Fetching video and channel metrics from YouTube API
    - Storing analytics snapshots in SQLite database
    - Detecting trending videos based on growth rate
    - Exporting analytics data to CSV/JSON

    Example:
        >>> fetcher = AnalyticsFetcher()
        >>> analytics = await fetcher.fetch_video("abc123")
        >>> await fetcher.store_video_analytics(analytics)
        >>> trending = await fetcher.get_trending_videos(limit=10)
    """

    def __init__(
        self,
        youtube_client: Any = None,
        db_path: Path | None = None,
    ) -> None:
        """Initialize the AnalyticsFetcher.

        Args:
            youtube_client: YouTubeClient instance for API calls.
                           Created lazily if not provided.
            db_path: Path to SQLite database file.
                    Defaults to cache_dir/analytics.db.
        """
        self._youtube_client = youtube_client
        self._db_path = db_path
        self._db_initialized = False

    def _get_db_path(self) -> Path:
        """Get database path, creating default if needed."""
        if self._db_path is not None:
            return self._db_path
        from brainrot.config import settings

        return settings.cache_dir / "analytics.db"

    def _get_youtube_client(self) -> Any:
        """Get or create YouTube client lazily."""
        if self._youtube_client is None:
            from brainrot.youtube_client import YouTubeClient

            self._youtube_client = YouTubeClient()
        return self._youtube_client

    async def _ensure_db(self) -> None:
        """Initialize database tables if they don't exist."""
        if self._db_initialized:
            return

        db_path = self._get_db_path()
        db_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiosqlite.connect(db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS video_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT NOT NULL,
                    views INTEGER DEFAULT 0,
                    likes INTEGER DEFAULT 0,
                    comments INTEGER DEFAULT 0,
                    avg_view_duration REAL DEFAULT 0.0,
                    fetched_at TEXT NOT NULL
                )
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_video_analytics_video_id
                ON video_analytics(video_id)
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_video_analytics_fetched_at
                ON video_analytics(fetched_at)
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS channel_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_id TEXT NOT NULL,
                    subscriber_count INTEGER DEFAULT 0,
                    total_views INTEGER DEFAULT 0,
                    video_count INTEGER DEFAULT 0,
                    fetched_at TEXT NOT NULL
                )
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_channel_analytics_channel_id
                ON channel_analytics(channel_id)
            """)
            await db.commit()

        self._db_initialized = True
        logger.debug(f"Initialized analytics database at {db_path}")

    def fetch_video(self, video_id: str) -> VideoAnalytics:
        """Fetch analytics for a single video.

        Args:
            video_id: YouTube video ID.

        Returns:
            VideoAnalytics with current metrics.
        """
        client = self._get_youtube_client()
        data = client.get_video_analytics(video_id)

        return VideoAnalytics(
            video_id=video_id,
            views=data.get("views", 0),
            likes=data.get("likes", 0),
            comments=data.get("comments", 0),
            avg_view_duration=0.0,
            fetched_at=datetime.now(timezone.utc),
        )

    def fetch_channel(self) -> ChannelAnalytics:
        """Fetch analytics for the authenticated channel.

        Returns:
            ChannelAnalytics with current metrics.
        """
        client = self._get_youtube_client()
        data = client.get_channel_info()

        return ChannelAnalytics(
            channel_id=data.get("id", ""),
            subscriber_count=data.get("subscriber_count", 0),
            total_views=data.get("total_views", 0),
            video_count=data.get("video_count", 0),
            fetched_at=datetime.now(timezone.utc),
        )

    def fetch_all_videos(self, video_ids: list[str]) -> list[VideoAnalytics]:
        """Fetch analytics for multiple videos.

        Args:
            video_ids: List of YouTube video IDs.

        Returns:
            List of VideoAnalytics for each video.
        """
        return [self.fetch_video(vid) for vid in video_ids]

    async def store_video_analytics(self, analytics: VideoAnalytics) -> None:
        """Store video analytics snapshot in database.

        Args:
            analytics: VideoAnalytics to store.
        """
        await self._ensure_db()

        async with aiosqlite.connect(self._get_db_path()) as db:
            await db.execute(
                """
                INSERT INTO video_analytics
                (video_id, views, likes, comments, avg_view_duration, fetched_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    analytics.video_id,
                    analytics.views,
                    analytics.likes,
                    analytics.comments,
                    analytics.avg_view_duration,
                    analytics.fetched_at.isoformat(),
                ),
            )
            await db.commit()

        logger.debug(
            f"Stored video analytics: {analytics.video_id} - "
            f"{analytics.views} views, {analytics.likes} likes"
        )

    async def store_channel_analytics(self, analytics: ChannelAnalytics) -> None:
        """Store channel analytics snapshot in database.

        Args:
            analytics: ChannelAnalytics to store.
        """
        await self._ensure_db()

        async with aiosqlite.connect(self._get_db_path()) as db:
            await db.execute(
                """
                INSERT INTO channel_analytics
                (channel_id, subscriber_count, total_views, video_count, fetched_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    analytics.channel_id,
                    analytics.subscriber_count,
                    analytics.total_views,
                    analytics.video_count,
                    analytics.fetched_at.isoformat(),
                ),
            )
            await db.commit()

        logger.debug(
            f"Stored channel analytics: {analytics.channel_id} - "
            f"{analytics.subscriber_count} subscribers"
        )

    async def get_video_analytics(
        self, video_id: str, days: int = 30
    ) -> list[VideoAnalytics]:
        """Retrieve stored analytics for a video within date range.

        Args:
            video_id: YouTube video ID.
            days: Number of days to look back.

        Returns:
            List of VideoAnalytics snapshots, newest first.
        """
        await self._ensure_db()

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        async with aiosqlite.connect(self._get_db_path()) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT id, video_id, views, likes, comments,
                       avg_view_duration, fetched_at
                FROM video_analytics
                WHERE video_id = ? AND fetched_at >= ?
                ORDER BY fetched_at DESC
                """,
                (video_id, cutoff.isoformat()),
            )
            rows = await cursor.fetchall()

        return [
            VideoAnalytics(
                id=row["id"],
                video_id=row["video_id"],
                views=row["views"],
                likes=row["likes"],
                comments=row["comments"],
                avg_view_duration=row["avg_view_duration"],
                fetched_at=datetime.fromisoformat(row["fetched_at"]),
            )
            for row in rows
        ]

    async def get_trending_videos(self, limit: int = 10) -> list[VideoGrowth]:
        """Get videos with highest growth rate.

        Analyzes analytics snapshots to find videos with the highest
        growth in views and likes over the past 7 days.

        Args:
            limit: Maximum number of videos to return.

        Returns:
            List of VideoGrowth objects sorted by growth score.
        """
        await self._ensure_db()

        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)

        async with aiosqlite.connect(self._get_db_path()) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT video_id,
                       MAX(fetched_at) as latest_fetched,
                       MIN(fetched_at) as earliest_fetched
                FROM video_analytics
                WHERE fetched_at >= ?
                GROUP BY video_id
                HAVING COUNT(*) >= 2
                """,
                (seven_days_ago.isoformat(),),
            )
            videos_with_data = await cursor.fetchall()

        growth_list: list[VideoGrowth] = []

        for video_row in videos_with_data:
            video_id = video_row["video_id"]

            async with aiosqlite.connect(self._get_db_path()) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    """
                    SELECT views, likes, comments, avg_view_duration, fetched_at
                    FROM video_analytics
                    WHERE video_id = ?
                    ORDER BY fetched_at DESC
                    LIMIT 2
                    """,
                    (video_id,),
                )
                snapshots = await cursor.fetchall()

            if len(snapshots) < 2:
                continue

            latest = snapshots[0]
            earlier = snapshots[1]

            earlier_views = earlier["views"] or 1
            earlier_likes = earlier["likes"] or 1

            views_growth = (latest["views"] - earlier["views"]) / earlier_views
            likes_growth = (latest["likes"] - earlier["likes"]) / earlier_likes

            growth_score = views_growth * 0.7 + likes_growth * 0.3

            latest_analytics = VideoAnalytics(
                video_id=video_id,
                views=latest["views"],
                likes=latest["likes"],
                comments=latest["comments"],
                avg_view_duration=latest["avg_view_duration"],
                fetched_at=datetime.fromisoformat(latest["fetched_at"]),
            )

            growth_list.append(
                VideoGrowth(
                    video_id=video_id,
                    views_growth=views_growth,
                    likes_growth=likes_growth,
                    growth_score=growth_score,
                    latest_analytics=latest_analytics,
                )
            )

        growth_list.sort(key=lambda x: x.growth_score, reverse=True)
        return growth_list[:limit]

    async def export_to_csv(self, output_path: Path) -> None:
        """Export all video analytics to CSV file.

        Args:
            output_path: Path to output CSV file.
        """
        await self._ensure_db()

        async with aiosqlite.connect(self._get_db_path()) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT video_id, views, likes, comments,
                       avg_view_duration, fetched_at
                FROM video_analytics
                ORDER BY fetched_at DESC
                """
            )
            rows = await cursor.fetchall()

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "video_id",
                    "views",
                    "likes",
                    "comments",
                    "avg_view_duration",
                    "fetched_at",
                ]
            )
            for row in rows:
                writer.writerow(
                    [
                        row["video_id"],
                        row["views"],
                        row["likes"],
                        row["comments"],
                        row["avg_view_duration"],
                        row["fetched_at"],
                    ]
                )

        logger.info(f"Exported {len(rows)} video analytics records to {output_path}")

    async def export_to_json(self, output_path: Path) -> None:
        """Export all analytics data to JSON file.

        Includes both video and channel analytics.

        Args:
            output_path: Path to output JSON file.
        """
        await self._ensure_db()

        async with aiosqlite.connect(self._get_db_path()) as db:
            db.row_factory = aiosqlite.Row
            video_cursor = await db.execute(
                """
                SELECT video_id, views, likes, comments,
                       avg_view_duration, fetched_at
                FROM video_analytics
                ORDER BY fetched_at DESC
                """
            )
            video_rows = await video_cursor.fetchall()

            channel_cursor = await db.execute(
                """
                SELECT channel_id, subscriber_count, total_views,
                       video_count, fetched_at
                FROM channel_analytics
                ORDER BY fetched_at DESC
                """
            )
            channel_rows = await channel_cursor.fetchall()

        data = {
            "video_analytics": [
                {
                    "video_id": row["video_id"],
                    "views": row["views"],
                    "likes": row["likes"],
                    "comments": row["comments"],
                    "avg_view_duration": row["avg_view_duration"],
                    "fetched_at": row["fetched_at"],
                }
                for row in video_rows
            ],
            "channel_analytics": [
                {
                    "channel_id": row["channel_id"],
                    "subscriber_count": row["subscriber_count"],
                    "total_views": row["total_views"],
                    "video_count": row["video_count"],
                    "fetched_at": row["fetched_at"],
                }
                for row in channel_rows
            ],
            "exported_at": datetime.now(timezone.utc).isoformat(),
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(
            f"Exported {len(video_rows)} video and {len(channel_rows)} "
            f"channel analytics records to {output_path}"
        )

    async def compare_periods(
        self,
        video_id: str,
        period1_start: datetime,
        period1_end: datetime,
        period2_start: datetime,
        period2_end: datetime,
    ) -> dict[str, Any]:
        """Compare video performance across two time periods.

        Args:
            video_id: YouTube video ID.
            period1_start: Start of first period.
            period1_end: End of first period.
            period2_start: Start of second period.
            period2_end: End of second period.

        Returns:
            Dictionary with comparison metrics.
        """
        await self._ensure_db()

        async with aiosqlite.connect(self._get_db_path()) as db:
            db.row_factory = aiosqlite.Row
            p1_cursor = await db.execute(
                """
                SELECT AVG(views) as avg_views,
                       AVG(likes) as avg_likes,
                       AVG(comments) as avg_comments
                FROM video_analytics
                WHERE video_id = ?
                  AND fetched_at >= ?
                  AND fetched_at <= ?
                """,
                (
                    video_id,
                    period1_start.isoformat(),
                    period1_end.isoformat(),
                ),
            )
            p1_data = await p1_cursor.fetchone()

            p2_cursor = await db.execute(
                """
                SELECT AVG(views) as avg_views,
                       AVG(likes) as avg_likes,
                       AVG(comments) as avg_comments
                FROM video_analytics
                WHERE video_id = ?
                  AND fetched_at >= ?
                  AND fetched_at <= ?
                """,
                (
                    video_id,
                    period2_start.isoformat(),
                    period2_end.isoformat(),
                ),
            )
            p2_data = await p2_cursor.fetchone()

        def safe_divide(a: float, b: float) -> float:
            return (a - b) / b if b != 0 else 0.0

        p1_views = p1_data["avg_views"] or 0
        p1_likes = p1_data["avg_likes"] or 0
        p1_comments = p1_data["avg_comments"] or 0

        p2_views = p2_data["avg_views"] or 0
        p2_likes = p2_data["avg_likes"] or 0
        p2_comments = p2_data["avg_comments"] or 0

        return {
            "video_id": video_id,
            "period1": {
                "start": period1_start.isoformat(),
                "end": period1_end.isoformat(),
                "avg_views": p1_views,
                "avg_likes": p1_likes,
                "avg_comments": p1_comments,
            },
            "period2": {
                "start": period2_start.isoformat(),
                "end": period2_end.isoformat(),
                "avg_views": p2_views,
                "avg_likes": p2_likes,
                "avg_comments": p2_comments,
            },
            "change": {
                "views": safe_divide(p2_views, p1_views),
                "likes": safe_divide(p2_likes, p1_likes),
                "comments": safe_divide(p2_comments, p1_comments),
            },
        }


__all__ = [
    "VideoAnalytics",
    "ChannelAnalytics",
    "VideoGrowth",
    "AnalyticsFetcher",
]
