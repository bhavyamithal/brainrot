"""Performance tracking agent for content optimization.

Analyzes video performance data to identify patterns, detect viral content,
and generate actionable recommendations for content strategy.
"""

from __future__ import annotations

import asyncio
import json
import logging
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class RecommendationType(Enum):
    """Types of recommendations the agent can generate."""

    INCREASE_TOPIC = "increase_topic"
    DECREASE_TOPIC = "decrease_topic"
    TEMPLATE_CHANGE = "template_change"
    POSTING_TIME = "posting_time"
    CONTENT_LENGTH = "content_length"
    VIRAL_OPPORTUNITY = "viral_opportunity"
    GENERAL = "general"


@dataclass
class ContentScore:
    """Scoring result for content success evaluation.

    Formula: views_weight * 0.5 + engagement_weight * 0.3 + growth_weight * 0.2
    """

    video_id: str
    views_score: float = 0.0
    engagement_score: float = 0.0
    growth_score: float = 0.0
    total_score: float = 0.0
    rank: str = "average"

    def calculate_total(self) -> float:
        """Calculate weighted total score."""
        self.total_score = (
            self.views_score * 0.5 + self.engagement_score * 0.3 + self.growth_score * 0.2
        )
        if self.total_score >= 0.8:
            self.rank = "excellent"
        elif self.total_score >= 0.6:
            self.rank = "good"
        elif self.total_score >= 0.4:
            self.rank = "average"
        else:
            self.rank = "below_average"
        return self.total_score


@dataclass
class ViralAlert:
    """Alert for viral video detection.

    Triggered when a video exceeds 2x average views within 24 hours.
    """

    video_id: str
    current_views: int
    average_views: float
    view_ratio: float
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    acknowledged: bool = False


@dataclass
class ContentPattern:
    """Identified content performance pattern."""

    pattern_type: str
    description: str
    supporting_videos: list[str]
    avg_score: float
    recommendation: str


@dataclass
class Recommendation:
    """Actionable recommendation for content strategy."""

    type: RecommendationType
    title: str
    description: str
    confidence: float
    supporting_data: dict[str, Any] = field(default_factory=dict)
    priority: int = 1


@dataclass
class PerformanceReport:
    """Comprehensive performance analysis report."""

    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    period_days: int = 7
    total_videos: int = 0
    total_views: int = 0
    total_likes: int = 0
    total_comments: int = 0
    avg_engagement_rate: float = 0.0
    top_performers: list[ContentScore] = field(default_factory=list)
    underperformers: list[ContentScore] = field(default_factory=list)
    viral_alerts: list[ViralAlert] = field(default_factory=list)
    patterns: list[ContentPattern] = field(default_factory=list)
    recommendations: list[Recommendation] = field(default_factory=list)


@dataclass
class WeeklySummary:
    """Weekly performance summary for reporting."""

    week_start: datetime
    week_end: datetime
    videos_published: int
    total_views: int
    total_likes: int
    views_change_percent: float = 0.0
    likes_change_percent: float = 0.0
    top_video_id: str = ""
    top_video_views: int = 0
    best_template: str = ""
    best_topic_keywords: list[str] = field(default_factory=list)
    key_insights: list[str] = field(default_factory=list)
    next_week_focus: list[str] = field(default_factory=list)


class PerformanceAgent:
    """Analyzes video performance and generates content recommendations.

    This agent integrates with AnalyticsFetcher and Script history to:
    - Analyze video performance daily
    - Identify top-performing content patterns
    - Detect underperforming content types
    - Generate actionable recommendations
    - Alert on viral videos (view spike detection)
    - Create weekly summaries

    Example:
        >>> agent = PerformanceAgent()
        >>> report = agent.generate_report()
        >>> print(len(report.recommendations))
        5
    """

    VIRAL_THRESHOLD = 2.0

    def __init__(
        self,
        analytics_fetcher: Any = None,
        script_history_path: Path | None = None,
        reports_dir: Path | None = None,
    ) -> None:
        """Initialize the performance agent.

        Args:
            analytics_fetcher: AnalyticsFetcher instance (created lazily if not provided).
            script_history_path: Path to script history JSON file.
            reports_dir: Directory for storing reports and alerts.
        """
        self._analytics_fetcher = analytics_fetcher
        self._script_history_path = script_history_path
        self._reports_dir = reports_dir
        self._script_history: list[dict[str, Any]] | None = None

    def _get_analytics_fetcher(self) -> Any:
        """Get or create AnalyticsFetcher lazily."""
        if self._analytics_fetcher is None:
            from brainrot.analytics.fetcher import AnalyticsFetcher

            self._analytics_fetcher = AnalyticsFetcher()
        return self._analytics_fetcher

    def _get_script_history_path(self) -> Path:
        """Get script history path with lazy settings import."""
        if self._script_history_path is not None:
            return self._script_history_path
        from brainrot.config import settings

        return settings.cache_dir / "script_history.json"

    def _get_reports_dir(self) -> Path:
        """Get reports directory with lazy settings import."""
        if self._reports_dir is not None:
            return self._reports_dir
        from brainrot.config import settings

        return settings.cache_dir / "reports"

    def _load_script_history(self) -> list[dict[str, Any]]:
        """Load script history from cache file."""
        if self._script_history is not None:
            return self._script_history

        history_path = self._get_script_history_path()
        if history_path.exists():
            try:
                with open(history_path) as f:
                    self._script_history = json.load(f)
                    return self._script_history
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"Failed to load script history: {e}")
        return []

    def _get_video_script(self, video_id: str) -> dict[str, Any] | None:
        """Find script data associated with a video ID."""
        history = self._load_script_history()
        for entry in history:
            if entry.get("id") == video_id or entry.get("video_id") == video_id:
                return entry
        return None

    def analyze(self, days: int = 7) -> PerformanceReport:
        """Analyze video performance for the specified period.

        Args:
            days: Number of days to analyze (default: 7).

        Returns:
            PerformanceReport with analysis results.
        """
        logger.info(f"Analyzing performance for last {days} days")

        report = PerformanceReport(period_days=days)
        fetcher = self._get_analytics_fetcher()

        trending = asyncio.run(fetcher.get_trending_videos(limit=50))

        if not trending:
            logger.warning("No analytics data available for analysis")
            report.recommendations.append(
                Recommendation(
                    type=RecommendationType.GENERAL,
                    title="Insufficient Data",
                    description="Not enough analytics data available. "
                    "Continue collecting data by publishing content regularly.",
                    confidence=1.0,
                    priority=1,
                )
            )
            return report

        scores = self._calculate_content_scores(trending)

        if scores:
            avg_views = statistics.mean([s.views_score for s in scores])
            report.total_videos = len(scores)
            report.total_views = sum(
                t.latest_analytics.views for t in trending if t.latest_analytics
            )
            report.total_likes = sum(
                t.latest_analytics.likes for t in trending if t.latest_analytics
            )
            report.total_comments = sum(
                t.latest_analytics.comments for t in trending if t.latest_analytics
            )

            total_engagement = report.total_likes + report.total_comments
            report.avg_engagement_rate = (
                total_engagement / report.total_views if report.total_views > 0 else 0.0
            )

            sorted_scores = sorted(scores, key=lambda x: x.total_score, reverse=True)
            report.top_performers = sorted_scores[:5]
            report.underperformers = sorted_scores[-3:] if len(sorted_scores) > 3 else []

            report.viral_alerts = self._detect_viral_videos(trending, avg_views)

            report.patterns = self._identify_patterns(trending, scores)

            report.recommendations = self._generate_recommendations(report)

        logger.info(
            f"Analysis complete: {report.total_videos} videos, "
            f"{len(report.recommendations)} recommendations"
        )
        return report

    def _calculate_content_scores(self, trending: list[Any]) -> list[ContentScore]:
        """Calculate content scores for trending videos."""
        scores = []

        if not trending:
            return scores

        all_views = [t.latest_analytics.views for t in trending if t.latest_analytics]
        all_likes = [t.latest_analytics.likes for t in trending if t.latest_analytics]
        max_views = max(all_views) if all_views else 1
        max_likes = max(all_likes) if all_likes else 1

        for video in trending:
            if not video.latest_analytics:
                continue

            score = ContentScore(video_id=video.video_id)

            if max_views > 0:
                score.views_score = video.latest_analytics.views / max_views

            engagement = video.latest_analytics.likes + video.latest_analytics.comments
            max_engagement = max_likes + max(
                [t.latest_analytics.comments for t in trending if t.latest_analytics]
            )
            if max_engagement > 0:
                score.engagement_score = engagement / max_engagement

            score.growth_score = min(1.0, max(0.0, video.growth_score))

            score.calculate_total()
            scores.append(score)

        return scores

    def detect_viral(self) -> list[ViralAlert]:
        """Detect videos that have gone viral (2x average views in 24h).

        Returns:
            List of ViralAlert for videos exceeding viral threshold.
        """
        fetcher = self._get_analytics_fetcher()
        trending = asyncio.run(fetcher.get_trending_videos(limit=50))

        if not trending:
            return []

        all_views = [t.latest_analytics.views for t in trending if t.latest_analytics]
        avg_views = statistics.mean(all_views) if all_views else 0

        return self._detect_viral_videos(trending, avg_views)

    def _detect_viral_videos(
        self, trending: list[Any], avg_views: float
    ) -> list[ViralAlert]:
        """Detect viral videos from trending data."""
        alerts = []

        for video in trending:
            if not video.latest_analytics:
                continue

            current_views = video.latest_analytics.views
            if avg_views > 0:
                view_ratio = current_views / avg_views
            else:
                view_ratio = 1.0

            if view_ratio >= self.VIRAL_THRESHOLD:
                alert = ViralAlert(
                    video_id=video.video_id,
                    current_views=current_views,
                    average_views=avg_views,
                    view_ratio=view_ratio,
                )
                alerts.append(alert)
                logger.info(
                    f"Viral alert: {video.video_id} has {view_ratio:.1f}x average views"
                )

        return alerts

    def _identify_patterns(
        self, trending: list[Any], scores: list[ContentScore]
    ) -> list[ContentPattern]:
        """Identify content performance patterns from data."""
        patterns = []

        template_scores: dict[str, list[float]] = {}
        for score in scores:
            script = self._get_video_script(score.video_id)
            if script:
                template = script.get("template", "unknown")
                if template not in template_scores:
                    template_scores[template] = []
                template_scores[template].append(score.total_score)

        for template, score_list in template_scores.items():
            if len(score_list) >= 2:
                avg_score = statistics.mean(score_list)
                video_ids = [
                    s.video_id for s in scores if self._get_video_script(s.video_id)
                ]
                video_ids = [
                    vid
                    for vid in video_ids
                    if self._get_video_script(vid)
                    and self._get_video_script(vid).get("template") == template
                ]

                if avg_score >= 0.6:
                    patterns.append(
                        ContentPattern(
                            pattern_type="template_success",
                            description=f"Template '{template}' performing well",
                            supporting_videos=video_ids[:5],
                            avg_score=avg_score,
                            recommendation=f"Continue using '{template}' template for similar content",
                        )
                    )
                elif avg_score < 0.4:
                    patterns.append(
                        ContentPattern(
                            pattern_type="template_underperform",
                            description=f"Template '{template}' underperforming",
                            supporting_videos=video_ids[:5],
                            avg_score=avg_score,
                            recommendation=f"Consider revising or replacing '{template}' template",
                        )
                    )

        growth_rates = [t.growth_score for t in trending]
        if growth_rates:
            avg_growth = statistics.mean(growth_rates)
            if avg_growth > 0.5:
                patterns.append(
                    ContentPattern(
                        pattern_type="channel_growth",
                        description="Channel experiencing strong growth",
                        supporting_videos=[t.video_id for t in trending[:5]],
                        avg_score=avg_growth,
                        recommendation="Maintain current content strategy; growth momentum is strong",
                    )
                )

        return patterns

    def _generate_recommendations(self, report: PerformanceReport) -> list[Recommendation]:
        """Generate actionable recommendations from analysis."""
        recommendations = []

        for alert in report.viral_alerts:
            script = self._get_video_script(alert.video_id)
            topic_info = ""
            if script:
                keywords = script.get("keywords", [])
                if keywords:
                    topic_info = f" Keywords: {', '.join(keywords[:3])}"

            recommendations.append(
                Recommendation(
                    type=RecommendationType.VIRAL_OPPORTUNITY,
                    title=f"Viral Video: {alert.video_id}",
                    description=f"This video has {alert.view_ratio:.1f}x average views. "
                    f"Consider creating follow-up content.{topic_info}",
                    confidence=0.9,
                    supporting_data={
                        "video_id": alert.video_id,
                        "view_ratio": alert.view_ratio,
                        "current_views": alert.current_views,
                    },
                    priority=1,
                )
            )

        if report.top_performers:
            top = report.top_performers[0]
            script = self._get_video_script(top.video_id)
            if script:
                template = script.get("template", "unknown")
                recommendations.append(
                    Recommendation(
                        type=RecommendationType.TEMPLATE_CHANGE,
                        title="Top Template Identified",
                        description=f"'{template}' template shows highest performance. "
                        f"Prioritize this style for new content.",
                        confidence=0.8,
                        supporting_data={"template": template, "score": top.total_score},
                        priority=2,
                    )
                )

        for underperf in report.underperformers:
            script = self._get_video_script(underperf.video_id)
            if script:
                template = script.get("template", "unknown")
                recommendations.append(
                    Recommendation(
                        type=RecommendationType.DECREASE_TOPIC,
                        title="Underperforming Content",
                        description=f"'{template}' template underperforming (score: {underperf.total_score:.2f}). "
                        f"Review and adjust content approach.",
                        confidence=0.7,
                        supporting_data={"template": template, "score": underperf.total_score},
                        priority=3,
                    )
                )

        for pattern in report.patterns:
            if pattern.pattern_type == "template_success" and pattern.avg_score >= 0.7:
                recommendations.append(
                    Recommendation(
                        type=RecommendationType.INCREASE_TOPIC,
                        title="Strong Pattern Detected",
                        description=pattern.recommendation,
                        confidence=0.75,
                        supporting_data={"pattern": pattern.pattern_type, "avg_score": pattern.avg_score},
                        priority=2,
                    )
                )

        if report.avg_engagement_rate < 0.02:
            recommendations.append(
                Recommendation(
                    type=RecommendationType.CONTENT_LENGTH,
                    title="Low Engagement Rate",
                    description=f"Engagement rate ({report.avg_engagement_rate:.2%}) is below optimal. "
                    f"Consider shorter hooks, stronger CTAs, or trending topics.",
                    confidence=0.65,
                    supporting_data={"engagement_rate": report.avg_engagement_rate},
                    priority=2,
                )
            )

        recommendations.sort(key=lambda r: r.priority)
        return recommendations

    def generate_report(self, days: int = 7) -> PerformanceReport:
        """Generate a comprehensive performance report.

        Args:
            days: Number of days to include in report.

        Returns:
            PerformanceReport with all analysis data.
        """
        return self.analyze(days)

    def generate_weekly_summary(self) -> WeeklySummary:
        """Generate a weekly performance summary.

        Returns:
            WeeklySummary with key metrics and insights.
        """
        now = datetime.now(timezone.utc)
        week_start = now - timedelta(days=7)

        report = self.analyze(days=7)

        summary = WeeklySummary(
            week_start=week_start,
            week_end=now,
            videos_published=report.total_videos,
            total_views=report.total_views,
            total_likes=report.total_likes,
        )

        if report.top_performers:
            top = report.top_performers[0]
            summary.top_video_id = top.video_id
            script = self._get_video_script(top.video_id)
            if script:
                summary.best_template = script.get("template", "")
                summary.best_topic_keywords = script.get("keywords", [])[:5]
            for video in report.top_performers:
                if video.video_id == top.video_id:
                    for t in self._get_trending_for_video(top.video_id):
                        if t.latest_analytics:
                            summary.top_video_views = t.latest_analytics.views
                            break

        insights = []
        if report.viral_alerts:
            insights.append(f"{len(report.viral_alerts)} viral video(s) detected this week")

        if report.avg_engagement_rate > 0.05:
            insights.append("Strong engagement rate above 5%")
        elif report.avg_engagement_rate < 0.02:
            insights.append("Engagement rate below 2% - needs attention")

        if report.patterns:
            success_patterns = [p for p in report.patterns if "success" in p.pattern_type]
            if success_patterns:
                insights.append(f"{len(success_patterns)} successful content patterns identified")

        summary.key_insights = insights

        focus_areas = []
        for rec in report.recommendations[:3]:
            focus_areas.append(rec.title)

        if not focus_areas:
            focus_areas = [
                "Continue consistent posting schedule",
                "Monitor trending topics for content ideas",
            ]

        summary.next_week_focus = focus_areas

        self._save_weekly_summary(summary)

        return summary

    def _get_trending_for_video(self, video_id: str) -> list[Any]:
        """Get trending data for a specific video."""
        fetcher = self._get_analytics_fetcher()
        trending = asyncio.run(fetcher.get_trending_videos(limit=50))
        return [t for t in trending if t.video_id == video_id]

    def _save_weekly_summary(self, summary: WeeklySummary) -> None:
        """Save weekly summary to reports directory."""
        reports_dir = self._get_reports_dir()
        reports_dir.mkdir(parents=True, exist_ok=True)

        filename = f"weekly_summary_{summary.week_start.strftime('%Y%m%d')}.json"
        output_path = reports_dir / filename

        data = {
            "week_start": summary.week_start.isoformat(),
            "week_end": summary.week_end.isoformat(),
            "videos_published": summary.videos_published,
            "total_views": summary.total_views,
            "total_likes": summary.total_likes,
            "views_change_percent": summary.views_change_percent,
            "likes_change_percent": summary.likes_change_percent,
            "top_video_id": summary.top_video_id,
            "top_video_views": summary.top_video_views,
            "best_template": summary.best_template,
            "best_topic_keywords": summary.best_topic_keywords,
            "key_insights": summary.key_insights,
            "next_week_focus": summary.next_week_focus,
        }

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved weekly summary to {output_path}")

    def acknowledge_viral_alert(self, video_id: str) -> None:
        """Mark a viral alert as acknowledged.

        Args:
            video_id: Video ID to acknowledge.
        """
        reports_dir = self._get_reports_dir()
        reports_dir.mkdir(parents=True, exist_ok=True)

        alerts_file = reports_dir / "viral_alerts.json"

        alerts_data: list[dict[str, Any]] = []
        if alerts_file.exists():
            try:
                with open(alerts_file) as f:
                    alerts_data = json.load(f)
            except (json.JSONDecodeError, OSError):
                pass

        for alert in alerts_data:
            if alert.get("video_id") == video_id:
                alert["acknowledged"] = True
                break
        else:
            alerts_data.append(
                {
                    "video_id": video_id,
                    "acknowledged": True,
                    "acknowledged_at": datetime.now(timezone.utc).isoformat(),
                }
            )

        with open(alerts_file, "w") as f:
            json.dump(alerts_data, f, indent=2)

        logger.info(f"Acknowledged viral alert for {video_id}")


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
