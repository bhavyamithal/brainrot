"""Trend Detection Engine for the brainrot platform.

This package provides multiple trend sources and aggregation capabilities:
- RedditTrendSource: Fetches trending posts from Reddit via PRAW
- GoogleTrendsSource: Fetches trending searches via pytrends
- TrendAggregator: Combines and deduplicates trends from multiple sources
- TrendCache: Persists processed trends to avoid reprocessing

Example:
    >>> from brainrot.trends import TrendAggregator, RedditTrendSource, GoogleTrendsSource
    >>> sources = [RedditTrendSource(), GoogleTrendsSource()]
    >>> aggregator = TrendAggregator(sources=sources)
    >>> trends = aggregator.get_trends(limit=10)
"""

from __future__ import annotations

from brainrot.trends.aggregator import TrendAggregator, TrendCache
from brainrot.trends.google_trends import GoogleTrendsSource
from brainrot.trends.reddit import RedditTrendSource

__all__ = [
    "RedditTrendSource",
    "GoogleTrendsSource",
    "TrendAggregator",
    "TrendCache",
]
