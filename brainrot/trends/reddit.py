"""Reddit trend source implementation using PRAW.

Fetches trending posts from configured subreddits and converts them
to Trend objects for use in the trend aggregation pipeline.
"""

from __future__ import annotations

import logging
import hashlib
from datetime import datetime, timezone
from typing import Any

import praw
from praw.models import Submission

from brainrot.config import settings
from brainrot.exceptions import TrendFetchError
from brainrot.types import Trend

logger = logging.getLogger(__name__)

DEFAULT_SUBREDDITS = [
    "technology",
    "programming",
    "artificial",
    "MachineLearning",
]


class RedditTrendSource:
    """Fetches trending posts from Reddit using PRAW.

    Uses Reddit API credentials from settings to fetch hot posts
    from configured subreddits.

    Attributes:
        subreddits: List of subreddit names to fetch from.
        reddit: PRAW Reddit instance.

    Example:
        >>> source = RedditTrendSource(subreddits=["technology", "programming"])
        >>> trends = source.fetch(limit=10)
    """

    def __init__(self, subreddits: list[str] | None = None) -> None:
        """Initialize the Reddit trend source.

        Args:
            subreddits: List of subreddit names to fetch from.
                        Defaults to tech/AI focused subreddits.
        """
        self.subreddits = subreddits or DEFAULT_SUBREDDITS.copy()
        self._reddit: praw.Reddit | None = None

    @property
    def reddit(self) -> praw.Reddit:
        """Lazy initialization of PRAW Reddit instance.

        Returns:
            Configured PRAW Reddit instance.

        Raises:
            TrendFetchError: If credentials are not configured.
        """
        if self._reddit is None:
            try:
                self._reddit = praw.Reddit(
                    client_id=settings.reddit_client_id,
                    client_secret=settings.reddit_client_secret,
                    user_agent=settings.reddit_user_agent,
                )
                logger.debug("PRAW Reddit client initialized")
            except Exception as e:
                raise TrendFetchError(
                    "Failed to initialize Reddit client",
                    details={"error": str(e)},
                ) from e
        return self._reddit

    def _generate_id(self, post_id: str) -> str:
        """Generate a unique trend ID from Reddit post ID.

        Args:
            post_id: Reddit post ID.

        Returns:
            Unique trend ID prefixed with 'reddit-'.
        """
        return f"reddit-{post_id}"

    def _extract_keywords(self, post: Submission) -> list[str]:
        """Extract keywords from post title and flair.

        Args:
            post: PRAW Submission object.

        Returns:
            List of extracted keywords.
        """
        keywords: list[str] = []

        if post.link_flair_text:
            keywords.append(post.link_flair_text)

        title_words = [
            word.strip(".,!?\"'()[]{}")
            for word in post.title.lower().split()
            if len(word) > 3 and word.isalnum()
        ]
        keywords.extend(title_words[:5])

        return keywords

    def _post_to_trend(self, post: Submission) -> Trend:
        """Convert a Reddit Submission to a Trend object.

        Args:
            post: PRAW Submission object.

        Returns:
            Trend object with post data.
        """
        return Trend(
            id=self._generate_id(post.id),
            title=post.title,
            source="reddit",
            url=f"https://reddit.com{post.permalink}",
            score=post.score,
            fetched_at=datetime.now(timezone.utc),
            keywords=self._extract_keywords(post),
        )

    def _is_valid_post(self, post: Submission) -> bool:
        """Check if a post is valid for trending.

        Filters out:
        - Stickied posts (announcements)
        - NSFW content
        - Posts with too low score

        Args:
            post: PRAW Submission object.

        Returns:
            True if post should be included.
        """
        if post.stickied:
            return False

        if post.over_18:
            return False

        if post.score < 100:
            return False

        return True

    def fetch(self, limit: int = 10) -> list[Trend]:
        """Fetch trending posts from configured subreddits.

        Fetches hot posts from each configured subreddit and returns
        the top posts by score.

        Args:
            limit: Maximum number of trends to return per subreddit.
                   Defaults to 10.

        Returns:
            List of Trend objects from Reddit.

        Raises:
            TrendFetchError: If fetching fails.

        Example:
            >>> source = RedditTrendSource()
            >>> trends = source.fetch(limit=20)
            >>> print(len(trends))
            20
        """
        trends: list[Trend] = []

        for subreddit_name in self.subreddits:
            try:
                logger.debug(f"Fetching from r/{subreddit_name}")
                subreddit = self.reddit.subreddit(subreddit_name)

                posts_fetched = 0
                for post in subreddit.hot(limit=limit * 2):
                    if self._is_valid_post(post):
                        trends.append(self._post_to_trend(post))
                        posts_fetched += 1
                        if posts_fetched >= limit:
                            break

                logger.info(
                    f"Fetched {posts_fetched} trends from r/{subreddit_name}"
                )

            except Exception as e:
                logger.warning(
                    f"Failed to fetch from r/{subreddit_name}: {e}"
                )
                continue

        trends.sort(key=lambda t: t.score, reverse=True)

        if not trends:
            raise TrendFetchError(
                "No trends fetched from any subreddit",
                details={"subreddits": self.subreddits},
            )

        return trends[:limit * len(self.subreddits)]
