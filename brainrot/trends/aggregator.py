"""Trend aggregation and caching for the brainrot platform.

Provides TrendAggregator for combining trends from multiple sources
with deduplication and ranking, and TrendCache for tracking processed trends.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from brainrot.config import settings
from brainrot.exceptions import TrendFetchError
from brainrot.types import Trend

logger = logging.getLogger(__name__)


class TrendSource(Protocol):
    """Protocol for trend sources used by TrendAggregator."""

    def fetch(self, limit: int = 10) -> list[Trend]:
        """Fetch trends from the source.

        Args:
            limit: Maximum number of trends to fetch.

        Returns:
            List of Trend objects.
        """
        ...


class TrendCache:
    """Cache for tracking processed trends to avoid duplication.

    Persists processed trend IDs to a JSON file, allowing the system
    to skip already-processed content across sessions.

    Attributes:
        cache_file: Path to the JSON cache file.
        processed_ids: Set of already processed trend IDs.

    Example:
        >>> cache = TrendCache()
        >>> cache.is_processed("reddit-abc123")
        False
        >>> cache.mark_processed("reddit-abc123")
        >>> cache.is_processed("reddit-abc123")
        True
    """

    def __init__(self, cache_file: Path | None = None) -> None:
        """Initialize the trend cache.

        Args:
            cache_file: Path to the JSON cache file.
                        Defaults to cache_dir/trend_cache.json.
        """
        self.cache_file = cache_file or settings.cache_dir / "trend_cache.json"
        self._processed_ids: set[str] | None = None
        self._cache_data: dict[str, Any] | None = None

    @property
    def processed_ids(self) -> set[str]:
        """Lazy load of processed IDs from cache file.

        Returns:
            Set of processed trend IDs.
        """
        if self._processed_ids is None:
            self._load_cache()
        return self._processed_ids  # type: ignore[return-value]

    def _load_cache(self) -> None:
        """Load cache from JSON file."""
        self._processed_ids = set()
        self._cache_data = {}

        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._processed_ids = set(data.get("processed_ids", []))
                    self._cache_data = data
                logger.debug(
                    f"Loaded {len(self._processed_ids)} cached trend IDs"
                )
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load trend cache: {e}")
                self._processed_ids = set()
                self._cache_data = {}

    def _save_cache(self) -> None:
        """Save cache to JSON file."""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)

        cache_data = {
            "processed_ids": list(self.processed_ids),
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2)
            logger.debug(f"Saved {len(self.processed_ids)} trend IDs to cache")
        except IOError as e:
            logger.error(f"Failed to save trend cache: {e}")

    def is_processed(self, trend_id: str) -> bool:
        """Check if a trend has been processed.

        Args:
            trend_id: Unique identifier of the trend.

        Returns:
            True if the trend has already been processed.
        """
        return trend_id in self.processed_ids

    def mark_processed(self, trend_id: str) -> None:
        """Mark a trend as processed.

        Args:
            trend_id: Unique identifier of the trend.
        """
        self.processed_ids.add(trend_id)
        self._save_cache()

    def mark_many_processed(self, trend_ids: list[str]) -> None:
        """Mark multiple trends as processed.

        Args:
            trend_ids: List of trend IDs to mark as processed.
        """
        for trend_id in trend_ids:
            self.processed_ids.add(trend_id)
        self._save_cache()

    def clear(self) -> None:
        """Clear all cached trend IDs."""
        self._processed_ids = set()
        self._save_cache()
        logger.info("Trend cache cleared")

    def cleanup_old_entries(self, max_age_days: int = 30) -> int:
        """Remove old entries from cache (placeholder for future).

        Currently a no-op since we don't track timestamps per ID.
        Can be extended to track processing dates.

        Args:
            max_age_days: Maximum age in days to keep entries.

        Returns:
            Number of entries removed (currently 0).
        """
        return 0


class TrendAggregator:
    """Aggregates trends from multiple sources with deduplication and ranking.

    Combines trends from multiple TrendSource implementations,
    deduplicates by title similarity, and ranks by combined score.

    Attributes:
        sources: List of trend sources to aggregate from.
        cache: TrendCache instance for tracking processed trends.

    Example:
        >>> from brainrot.trends import RedditTrendSource, GoogleTrendsSource
        >>> sources = [RedditTrendSource(), GoogleTrendsSource()]
        >>> aggregator = TrendAggregator(sources=sources)
        >>> trends = aggregator.get_trends(limit=10)
    """

    def __init__(
        self,
        sources: list[TrendSource] | None = None,
        cache: TrendCache | None = None,
    ) -> None:
        """Initialize the trend aggregator.

        Args:
            sources: List of trend sources to aggregate from.
                     If None, sources must be added via add_source().
            cache: Optional TrendCache instance for filtering processed trends.
        """
        self.sources: list[TrendSource] = sources or []
        self.cache = cache or TrendCache()

    def add_source(self, source: TrendSource) -> None:
        """Add a trend source to the aggregator.

        Args:
            source: TrendSource instance to add.
        """
        self.sources.append(source)
        logger.debug(f"Added trend source: {source.__class__.__name__}")

    def _normalize_title(self, title: str) -> str:
        """Normalize a title for comparison.

        Args:
            title: Title to normalize.

        Returns:
            Normalized title string.
        """
        return title.lower().strip()

    def _calculate_similarity(self, title1: str, title2: str) -> float:
        """Calculate simple similarity between two titles.

        Uses word overlap ratio for a simple but effective comparison.

        Args:
            title1: First title.
            title2: Second title.

        Returns:
            Similarity score between 0.0 and 1.0.
        """
        words1 = set(self._normalize_title(title1).split())
        words2 = set(self._normalize_title(title2).split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union)

    def _deduplicate(
        self,
        trends: list[Trend],
        similarity_threshold: float = 0.7,
    ) -> list[Trend]:
        """Remove duplicate trends based on title similarity.

        Args:
            trends: List of trends to deduplicate.
            similarity_threshold: Threshold for considering titles duplicates.

        Returns:
            Deduplicated list of trends.
        """
        if not trends:
            return []

        unique_trends: list[Trend] = []

        for trend in trends:
            is_duplicate = False

            for existing in unique_trends:
                similarity = self._calculate_similarity(trend.title, existing.title)
                if similarity >= similarity_threshold:
                    if trend.score > existing.score:
                        unique_trends.remove(existing)
                        unique_trends.append(trend)
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_trends.append(trend)

        logger.debug(
            f"Deduplicated {len(trends)} trends to {len(unique_trends)}"
        )
        return unique_trends

    def _filter_processed(self, trends: list[Trend]) -> list[Trend]:
        """Filter out already processed trends.

        Args:
            trends: List of trends to filter.

        Returns:
            List of unprocessed trends.
        """
        filtered = [
            t for t in trends
            if not self.cache.is_processed(t.id)
        ]
        logger.debug(
            f"Filtered {len(trends) - len(filtered)} processed trends"
        )
        return filtered

    def _rank_trends(self, trends: list[Trend]) -> list[Trend]:
        """Rank trends by combined scoring.

        Scoring factors:
        - Raw score from source (upvotes, views, etc.)
        - Recency bonus (newer = higher score)
        - Source diversity bonus

        Args:
            trends: List of trends to rank.

        Returns:
            Sorted list of trends by combined score.
        """
        now = datetime.now(timezone.utc)

        for trend in trends:
            age_hours = (now - trend.fetched_at).total_seconds() / 3600
            recency_bonus = max(0, 1.0 - (age_hours / 24)) * 0.2

            trend.score = int(trend.score * (1.0 + recency_bonus))

        return sorted(trends, key=lambda t: t.score, reverse=True)

    def get_trends(
        self,
        limit: int = 10,
        fetch_limit: int = 20,
        exclude_processed: bool = True,
    ) -> list[Trend]:
        """Fetch and aggregate trends from all sources.

        Args:
            limit: Maximum number of trends to return.
            fetch_limit: Number of trends to fetch per source.
            exclude_processed: Whether to exclude already processed trends.

        Returns:
            Aggregated and ranked list of trends.

        Raises:
            TrendFetchError: If all sources fail to provide trends.

        Example:
            >>> aggregator = TrendAggregator()
            >>> trends = aggregator.get_trends(limit=10)
        """
        all_trends: list[Trend] = []
        errors: list[str] = []

        for source in self.sources:
            source_name = source.__class__.__name__
            try:
                logger.debug(f"Fetching from {source_name}")
                trends = source.fetch(limit=fetch_limit)
                all_trends.extend(trends)
                logger.info(f"Fetched {len(trends)} trends from {source_name}")
            except TrendFetchError as e:
                errors.append(f"{source_name}: {e.message}")
                logger.warning(f"Failed to fetch from {source_name}: {e}")
            except Exception as e:
                errors.append(f"{source_name}: {str(e)}")
                logger.error(f"Unexpected error from {source_name}: {e}")

        if not all_trends:
            raise TrendFetchError(
                "No trends fetched from any source",
                details={"errors": errors},
            )

        unique_trends = self._deduplicate(all_trends)

        if exclude_processed:
            unique_trends = self._filter_processed(unique_trends)

        ranked_trends = self._rank_trends(unique_trends)

        logger.info(
            f"Aggregated {len(ranked_trends)} unique trends "
            f"(from {len(all_trends)} total)"
        )

        return ranked_trends[:limit]

    def mark_trends_processed(self, trends: list[Trend]) -> None:
        """Mark trends as processed in the cache.

        Args:
            trends: List of trends to mark as processed.
        """
        self.cache.mark_many_processed([t.id for t in trends])
