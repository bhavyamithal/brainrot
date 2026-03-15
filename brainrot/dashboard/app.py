"""Streamlit dashboard for visualizing YouTube analytics data.

Displays channel metrics, video performance trends, and engagement analytics
with filtering capabilities by date range and content type.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st


def _get_db_path() -> Path:
    """Lazily get database path to avoid triggering Settings validation."""
    from brainrot.config import settings

    return settings.cache_dir / "analytics.db"


def _get_analytics_fetcher() -> Any:
    """Lazily create AnalyticsFetcher instance."""
    from brainrot.analytics.fetcher import AnalyticsFetcher

    return AnalyticsFetcher(db_path=_get_db_path())


@dataclass
class DashboardStats:
    """Aggregated statistics for dashboard display."""

    total_views: int = 0
    total_likes: int = 0
    total_comments: int = 0
    video_count: int = 0
    avg_engagement_rate: float = 0.0
    top_videos: list[dict[str, Any]] | None = None
    views_over_time: list[dict[str, Any]] | None = None


async def _fetch_dashboard_data(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    content_type: str = "All",
) -> DashboardStats:
    """Fetch all data needed for dashboard display.

    Args:
        start_date: Filter start date.
        end_date: Filter end date.
        content_type: Content type filter (placeholder for future use).

    Returns:
        DashboardStats with aggregated metrics.
    """
    fetcher = _get_analytics_fetcher()
    await fetcher._ensure_db()

    import aiosqlite

    db_path = _get_db_path()
    if not db_path.exists():
        return DashboardStats()

    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row

        if start_date is None:
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
        if end_date is None:
            end_date = datetime.now(timezone.utc)

        cursor = await db.execute(
            """
            SELECT
                SUM(views) as total_views,
                SUM(likes) as total_likes,
                SUM(comments) as total_comments,
                COUNT(DISTINCT video_id) as video_count
            FROM video_analytics
            WHERE fetched_at >= ? AND fetched_at <= ?
            """,
            (start_date.isoformat(), end_date.isoformat()),
        )
        summary = await cursor.fetchone()

        cursor = await db.execute(
            """
            SELECT
                video_id,
                MAX(views) as views,
                MAX(likes) as likes,
                MAX(comments) as comments,
                MAX(fetched_at) as fetched_at
            FROM video_analytics
            WHERE fetched_at >= ? AND fetched_at <= ?
            GROUP BY video_id
            ORDER BY views DESC
            LIMIT 10
            """,
            (start_date.isoformat(), end_date.isoformat()),
        )
        top_videos = await cursor.fetchall()

        cursor = await db.execute(
            """
            SELECT
                DATE(fetched_at) as date,
                SUM(views) as views,
                SUM(likes) as likes,
                SUM(comments) as comments
            FROM video_analytics
            WHERE fetched_at >= ? AND fetched_at <= ?
            GROUP BY DATE(fetched_at)
            ORDER BY date ASC
            """,
            (start_date.isoformat(), end_date.isoformat()),
        )
        views_over_time = await cursor.fetchall()

    total_views = summary["total_views"] or 0 if summary else 0
    total_likes = summary["total_likes"] or 0 if summary else 0
    total_comments = summary["total_comments"] or 0 if summary else 0
    video_count = summary["video_count"] or 0 if summary else 0

    engagement_rate = 0.0
    if total_views > 0:
        engagement_rate = ((total_likes + total_comments) / total_views) * 100

    return DashboardStats(
        total_views=total_views,
        total_likes=total_likes,
        total_comments=total_comments,
        video_count=video_count,
        avg_engagement_rate=round(engagement_rate, 2),
        top_videos=[
            {
                "video_id": row["video_id"],
                "views": row["views"],
                "likes": row["likes"],
                "comments": row["comments"],
                "engagement_rate": round(
                    ((row["likes"] + row["comments"]) / row["views"] * 100) if row["views"] > 0 else 0,
                    2,
                ),
                "fetched_at": row["fetched_at"],
            }
            for row in (top_videos or [])
        ],
        views_over_time=[
            {
                "date": row["date"],
                "views": row["views"],
                "likes": row["likes"],
                "comments": row["comments"],
            }
            for row in (views_over_time or [])
        ],
    )


async def _fetch_trending_videos(limit: int = 10) -> list[dict[str, Any]]:
    """Fetch trending videos with growth scores.

    Args:
        limit: Maximum number of videos to return.

    Returns:
        List of trending video dictionaries.
    """
    fetcher = _get_analytics_fetcher()
    trending = await fetcher.get_trending_videos(limit=limit)
    return [
        {
            "video_id": v.video_id,
            "views_growth": round(v.views_growth * 100, 2),
            "likes_growth": round(v.likes_growth * 100, 2),
            "growth_score": round(v.growth_score * 100, 2),
            "current_views": v.latest_analytics.views if v.latest_analytics else 0,
            "current_likes": v.latest_analytics.likes if v.latest_analytics else 0,
        }
        for v in trending
    ]


def _run_async(coro: Any) -> Any:
    """Run async function in Streamlit context."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result()
    else:
        return asyncio.run(coro)


def _apply_dark_theme() -> None:
    """Apply custom dark theme styling to the dashboard."""
    st.markdown(
        """
        <style>
        /* Dark theme base */
        .stApp {
            background-color: #0d1117;
            color: #e6edf3;
        }

        /* Main content area */
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }

        /* Metrics styling */
        [data-testid="stMetricValue"] {
            font-size: 2rem;
            font-weight: 700;
            color: #58a6ff;
        }
        [data-testid="stMetricLabel"] {
            color: #8b949e;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        [data-testid="stMetricDelta"] {
            color: #3fb950;
        }

        /* Dataframe styling */
        .stDataFrame {
            background-color: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
        }
        .stDataFrame th {
            background-color: #21262d !important;
            color: #e6edf3 !important;
        }
        .stDataFrame td {
            background-color: #0d1117 !important;
            color: #e6edf3 !important;
        }

        /* Chart styling */
        .stLineChart, .stBarChart {
            background-color: #161b22;
            border-radius: 8px;
            padding: 1rem;
        }

        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background-color: #161b22;
        }
        [data-testid="stSidebar"] .stSelectbox label,
        [data-testid="stSidebar"] .stDateInput label {
            color: #e6edf3;
        }

        /* Headers */
        h1, h2, h3 {
            color: #e6edf3;
            border-bottom: 1px solid #30363d;
            padding-bottom: 0.5rem;
        }

        /* Tabs styling */
        .stTabs [data-baseweb="tab-list"] {
            background-color: #161b22;
            border-radius: 8px 8px 0 0;
        }
        .stTabs [data-baseweb="tab"] {
            color: #8b949e;
        }
        .stTabs [aria-selected="true"] {
            background-color: #21262d !important;
            color: #e6edf3 !important;
        }

        /* Info/warning boxes */
        .stAlert {
            background-color: #161b22;
            border: 1px solid #30363d;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    """Main entry point for the Streamlit dashboard."""
    st.set_page_config(
        page_title="Brainrot Analytics Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    _apply_dark_theme()

    st.title("📊 Brainrot Analytics Dashboard")
    st.markdown("Performance metrics for your content channel")

    st.sidebar.header("Filters")

    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=datetime.now(timezone.utc).date() - timedelta(days=30),
            max_value=datetime.now(timezone.utc).date(),
        )
    with col2:
        end_date = st.date_input(
            "End Date",
            value=datetime.now(timezone.utc).date(),
            max_value=datetime.now(timezone.utc).date(),
        )

    content_type = st.sidebar.selectbox(
        "Content Type",
        options=["All", "Shorts", "Long-form"],
        index=0,
    )

    if start_date > end_date:
        st.error("Start date must be before end date")
        return

    start_dt = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
    end_dt = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=timezone.utc)

    with st.spinner("Loading analytics data..."):
        stats = _run_async(_fetch_dashboard_data(start_dt, end_dt, content_type))

    if stats.video_count == 0:
        st.info(
            "No analytics data found for the selected date range. "
            "Run the analytics fetcher to collect data first."
        )
        return

    st.markdown("---")

    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    with metric_col1:
        st.metric(
            label="Total Views",
            value=f"{stats.total_views:,}",
        )
    with metric_col2:
        st.metric(
            label="Total Videos",
            value=f"{stats.video_count:,}",
        )
    with metric_col3:
        st.metric(
            label="Avg Engagement",
            value=f"{stats.avg_engagement_rate:.2f}%",
        )
    with metric_col4:
        st.metric(
            label="Total Likes",
            value=f"{stats.total_likes:,}",
        )

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["📈 Performance Trends", "🏆 Top Videos", "🔥 Trending"])

    with tab1:
        st.subheader("Views Over Time")

        if stats.views_over_time:
            views_df = pd.DataFrame(stats.views_over_time)
            views_df["date"] = pd.to_datetime(views_df["date"])
            views_df = views_df.set_index("date")

            st.line_chart(views_df[["views"]], use_container_width=True)

            st.subheader("Engagement Over Time")
            st.line_chart(views_df[["likes", "comments"]], use_container_width=True)
        else:
            st.info("No time-series data available for the selected period.")

    with tab2:
        st.subheader("Top 10 Performing Videos")

        if stats.top_videos:
            top_df = pd.DataFrame(stats.top_videos)
            top_df = top_df.rename(
                columns={
                    "video_id": "Video ID",
                    "views": "Views",
                    "likes": "Likes",
                    "comments": "Comments",
                    "engagement_rate": "Engagement %",
                }
            )
            st.dataframe(
                top_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Views": st.column_config.NumberColumn(format="%d"),
                    "Likes": st.column_config.NumberColumn(format="%d"),
                    "Comments": st.column_config.NumberColumn(format="%d"),
                    "Engagement %": st.column_config.NumberColumn(format="%.2f%%"),
                },
            )

            st.subheader("Views Distribution")
            chart_df = top_df[["Video ID", "Views"]].set_index("Video ID")
            st.bar_chart(chart_df, use_container_width=True)
        else:
            st.info("No top videos data available.")

    with tab3:
        st.subheader("Videos with Highest Growth")

        with st.spinner("Calculating growth trends..."):
            trending = _run_async(_fetch_trending_videos(limit=10))

        if trending:
            trending_df = pd.DataFrame(trending)
            trending_df = trending_df.rename(
                columns={
                    "video_id": "Video ID",
                    "views_growth": "Views Growth %",
                    "likes_growth": "Likes Growth %",
                    "growth_score": "Growth Score",
                    "current_views": "Current Views",
                    "current_likes": "Current Likes",
                }
            )
            st.dataframe(
                trending_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Views Growth %": st.column_config.NumberColumn(format="%.2f%%"),
                    "Likes Growth %": st.column_config.NumberColumn(format="%.2f%%"),
                    "Growth Score": st.column_config.NumberColumn(format="%.2f"),
                    "Current Views": st.column_config.NumberColumn(format="%d"),
                    "Current Likes": st.column_config.NumberColumn(format="%d"),
                },
            )

            st.subheader("Growth Score Distribution")
            growth_chart_df = trending_df[["Video ID", "Growth Score"]].set_index("Video ID")
            st.bar_chart(growth_chart_df, use_container_width=True)
        else:
            st.info(
                "No trending videos found. Growth calculation requires at least 2 "
                "analytics snapshots per video within the last 7 days."
            )

    st.markdown("---")
    st.caption(
        f"Data refreshes on each load. Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
    )


if __name__ == "__main__":
    main()
