"""Google Trends source implementation using pytrends.

Fetches trending searches and related topics from Google Trends
for use in the trend aggregation pipeline.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from pytrends.request import TrendReq

from brainrot.exceptions import TrendFetchError
from brainrot.types import Trend

logger = logging.getLogger(__name__)


class GoogleTrendsSource:
    """Fetches trending searches from Google Trends using pytrends.

    Uses the pytrends library to access Google Trends data including
    daily trending searches and real-time trends.

    Attributes:
        geo: Geographic region for trends (e.g., 'US', 'GB').
        pytrends: TrendReq client instance.

    Example:
        >>> source = GoogleTrendsSource(geo="US")
        >>> trends = source.fetch(limit=10)
    """

    def __init__(self, geo: str = "US") -> None:
        """Initialize the Google Trends source.

        Args:
            geo: Geographic region code for trends.
                 Defaults to 'US'.
        """
        self.geo = geo.upper()
        self._pytrends: TrendReq | None = None

    @property
    def pytrends(self) -> TrendReq:
        """Lazy initialization of pytrends client.

        Returns:
            Configured TrendReq instance.
        """
        if self._pytrends is None:
            self._pytrends = TrendReq(
                hl="en-US",
                tz=360,
            )
            logger.debug("pytrends client initialized")
        return self._pytrends

    def _generate_id(self, query: str) -> str:
        """Generate a unique trend ID from search query.

        Args:
            query: Search query string.

        Returns:
            Unique trend ID prefixed with 'gt-'.
        """
        import hashlib
        hash_digest = hashlib.md5(query.encode()).hexdigest()[:12]
        return f"gt-{hash_digest}"

    def _extract_keywords(self, query: str) -> list[str]:
        """Extract keywords from a search query.

        Args:
            query: Search query string.

        Returns:
            List of extracted keywords.
        """
        words = [
            word.lower().strip()
            for word in query.split()
            if len(word) > 2 and word.isalnum()
        ]
        return words[:5]

    def fetch(self, limit: int = 10) -> list[Trend]:
        """Fetch trending searches from Google Trends.

        Uses the trending_searches() method to get daily trending
        searches for the configured geographic region.

        Args:
            limit: Maximum number of trends to return.
                   Defaults to 10.

        Returns:
            List of Trend objects from Google Trends.

        Raises:
            TrendFetchError: If fetching fails.

        Example:
            >>> source = GoogleTrendsSource()
            >>> trends = source.fetch(limit=20)
        """
        trends: list[Trend] = []

        try:
            logger.debug(f"Fetching trending searches for geo={self.geo}")
            trending_df = self.pytrends.trending_searches(pn=self.geo)

            if trending_df.empty:
                logger.warning("No trending searches returned")
                return []

            for idx, row in trending_df.head(limit).iterrows():
                query = str(row[0])
                trend = Trend(
                    id=self._generate_id(query),
                    title=query,
                    source="google_trends",
                    url=f"https://trends.google.com/trends/explore?q={query}&geo={self.geo}",
                    score=limit - idx,
                    fetched_at=datetime.now(timezone.utc),
                    keywords=self._extract_keywords(query),
                )
                trends.append(trend)

            logger.info(f"Fetched {len(trends)} trends from Google Trends")

        except Exception as e:
            logger.error(f"Failed to fetch Google Trends: {e}")
            raise TrendFetchError(
                "Failed to fetch Google Trends",
                details={"geo": self.geo, "error": str(e)},
            ) from e

        return trends

    def fetch_related_topics(self, query: str, limit: int = 5) -> list[Trend]:
        """Fetch topics related to a search query.

        Args:
            query: Search query to find related topics for.
            limit: Maximum number of related topics to return.

        Returns:
            List of Trend objects for related topics.
        """
        trends: list[Trend] = []

        try:
            self.pytrends.build_payload([query], geo=self.geo)
            related_topics = self.pytrends.related_topics()

            if not related_topics or query not in related_topics:
                return []

            topics_df = related_topics[query].get("top", [])
            if topics_df is None or (hasattr(topics_df, 'empty') and topics_df.empty):
                return []

            for idx, row in topics_df.head(limit).iterrows():
                topic_title = row.get("topic_title", str(row.iloc[0]))
                trend = Trend(
                    id=self._generate_id(f"{query}-{topic_title}"),
                    title=topic_title,
                    source="google_trends_related",
                    url=f"https://trends.google.com/trends/explore?q={topic_title}&geo={self.geo}",
                    score=limit - idx,
                    fetched_at=datetime.now(timezone.utc),
                    keywords=[query] + self._extract_keywords(topic_title),
                )
                trends.append(trend)

        except Exception as e:
            logger.warning(f"Failed to fetch related topics for '{query}': {e}")

        return trends
