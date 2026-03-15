"""Agents package for autonomous content optimization.

This module provides intelligent agents that analyze performance data
and generate actionable recommendations for content strategy.

Classes:
    PerformanceAgent: Analyzes video performance and generates recommendations.
    PerformanceReport: Structured report with metrics and recommendations.
    ContentScore: Scoring system for content success evaluation.
    ViralAlert: Alert data for viral video detection.
"""

from brainrot.agents.performance_agent import (
    ContentPattern,
    ContentScore,
    PerformanceAgent,
    PerformanceReport,
    Recommendation,
    RecommendationType,
    ViralAlert,
    WeeklySummary,
)

__all__ = [
    "PerformanceAgent",
    "PerformanceReport",
    "ContentScore",
    "ViralAlert",
    "WeeklySummary",
    "Recommendation",
    "RecommendationType",
    "ContentPattern",
]
