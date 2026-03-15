"""Analytics package for tracking video and channel performance.

This module provides tools for fetching, storing, and analyzing
YouTube analytics data.

Classes:
    VideoAnalytics: Per-video performance metrics.
    ChannelAnalytics: Channel-level statistics.
    AnalyticsFetcher: Main class for fetching and storing analytics.
"""

from brainrot.analytics.fetcher import (
    AnalyticsFetcher,
    ChannelAnalytics,
    VideoAnalytics,
)

__all__ = [
    "VideoAnalytics",
    "ChannelAnalytics",
    "AnalyticsFetcher",
]
