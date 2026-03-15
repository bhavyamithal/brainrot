"""Shared pytest fixtures for brainrot tests.

Provides mock fixtures for all external dependencies:
- Reddit API (PRAW)
- YouTube Data API
- Pexels/Pixabay APIs
- LLM (Ollama/Groq)
- edge-tts
- FFmpeg (for video generation)
"""

from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from brainrot.types import Script, Trend


# ============================================================================
# Sample Data Fixtures
# ============================================================================


@pytest.fixture
def sample_trends() -> list[Trend]:
    """Sample trend data for testing."""
    return [
        Trend(
            id="reddit-test123",
            title="New AI breakthrough enables real-time language translation",
            source="reddit",
            url="https://reddit.com/r/technology/comments/test123",
            score=1500,
            fetched_at=datetime.now(timezone.utc),
            keywords=["AI", "language", "translation", "technology"],
        ),
        Trend(
            id="gt-test456",
            title="Quantum computing milestone achieved by research team",
            source="google_trends",
            url="https://trends.google.com/story/test456",
            score=2500,
            fetched_at=datetime.now(timezone.utc),
            keywords=["quantum", "computing", "research"],
        ),
        Trend(
            id="reddit-test789",
            title="Open source project reaches 1 million stars on GitHub",
            source="reddit",
            url="https://reddit.com/r/programming/comments/test789",
            score=3000,
            fetched_at=datetime.now(timezone.utc),
            keywords=["opensource", "github", "programming"],
        ),
    ]


@pytest.fixture
def sample_script() -> Script:
    """Sample script data for testing."""
    return Script(
        id="script-test001",
        trend_id="reddit-test123",
        text="Did you know AI can now translate languages in real-time? "
        "This breakthrough is changing how we communicate globally. "
        "Imagine having a conversation with someone who speaks a completely different language, "
        "and understanding each other instantly. This technology uses advanced neural networks "
        "to process speech and translate it within milliseconds. The implications are enormous "
        "for business, travel, and connecting cultures. Major tech companies are racing to "
        "integrate this into their platforms. The future of communication is here, and it speaks "
        "every language. What would you do with a universal translator in your pocket?",
        hook="Did you know AI can now translate languages in real-time?",
        word_count=95,
        template="news_synthesis",
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_video_analytics() -> dict[str, Any]:
    """Sample video analytics data."""
    return {
        "views": 15000,
        "likes": 850,
        "comments": 120,
        "title": "Test Video Title",
        "published_at": datetime.now(timezone.utc).isoformat(),
    }


@pytest.fixture
def sample_channel_info() -> dict[str, Any]:
    """Sample channel info data."""
    return {
        "id": "test_channel_123",
        "title": "Test Channel",
        "subscriber_count": 50000,
        "video_count": 100,
    }


@pytest.fixture
def sample_pexels_response() -> dict[str, Any]:
    """Sample Pexels API response for video search."""
    return {
        "videos": [
            {
                "id": 12345,
                "url": "https://www.pexels.com/video/test-video-12345/",
                "image": "https://images.pexels.com/videos/thumbnail.jpg",
                "duration": 30,
                "video_files": [
                    {
                        "id": 1,
                        "quality": "hd",
                        "file_type": "video/mp4",
                        "width": 1920,
                        "height": 1080,
                        "link": "https://player.vimeo.com/external/test.mp4",
                    }
                ],
            }
        ]
    }


@pytest.fixture
def sample_pixabay_response() -> dict[str, Any]:
    """Sample Pixabay API response for video search."""
    return {
        "hits": [
            {
                "id": 67890,
                "pageURL": "https://pixabay.com/videos/test-video-67890/",
                "type": "film",
                "duration": 25,
                "videos": {
                    "large": {"url": "https://cdn.pixabay.com/test_large.mp4"},
                    "medium": {"url": "https://cdn.pixabay.com/test_medium.mp4"},
                    "small": {"url": "https://cdn.pixabay.com/test_small.mp4"},
                },
            }
        ]
    }


# ============================================================================
# Directory and File Fixtures
# ============================================================================


@pytest.fixture
def temp_cache_dir(tmp_path: Path) -> Path:
    """Create a temporary cache directory for tests."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Path:
    """Create a temporary output directory for videos."""
    output_dir = tmp_path / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


@pytest.fixture
def temp_state_file(tmp_path: Path) -> Path:
    """Create a temporary state file path."""
    return tmp_path / "pipeline_state.json"


@pytest.fixture
def temp_audio_file(tmp_path: Path) -> Path:
    """Create a temporary audio file for testing."""
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    audio_path = audio_dir / "test_audio.mp3"
    # Create a minimal valid MP3-like file (not a real MP3, but enough for path testing)
    audio_path.write_bytes(b"ID3" + b"\x00" * 100)
    return audio_path


@pytest.fixture
def temp_video_file(tmp_path: Path) -> Path:
    """Create a temporary video file for testing."""
    video_dir = tmp_path / "videos"
    video_dir.mkdir(parents=True, exist_ok=True)
    video_path = video_dir / "test_video.mp4"
    # Create a minimal file
    video_path.write_bytes(b"\x00" * 100)
    return video_path


# ============================================================================
# Mock Fixtures for External APIs
# ============================================================================


@pytest.fixture
def mock_reddit():
    """Mock PRAW Reddit client."""
    with patch("brainrot.trends.reddit.praw.Reddit") as mock_reddit_class:
        mock_instance = MagicMock()
        mock_reddit_class.return_value = mock_instance

        # Create mock subreddit with sample submissions
        mock_subreddit = MagicMock()
        mock_instance.subreddit.return_value = mock_subreddit

        # Create mock submissions
        mock_submissions = []
        for i in range(5):
            mock_submission = MagicMock()
            mock_submission.id = f"test{i}"
            mock_submission.title = f"Test Reddit Post {i}"
            mock_submission.url = f"https://reddit.com/post/{i}"
            mock_submission.score = 1000 + i * 100
            mock_submission.stickied = False
            mock_submission.over_18 = False
            mock_submission.subreddit.display_name = "technology"
            mock_submissions.append(mock_submission)

        mock_subreddit.hot.return_value = mock_submissions
        mock_subreddit.new.return_value = mock_submissions
        mock_subreddit.top.return_value = mock_submissions

        yield mock_reddit_class


@pytest.fixture
def mock_google_trends():
    """Mock pytrends TrendReq client."""
    with patch("brainrot.trends.google_trends.TrendReq") as mock_trendreq_class:
        mock_instance = MagicMock()
        mock_trendreq_class.return_value = mock_instance

        # Mock trending searches
        mock_instance.trending_searches.return_value = [
            "AI Technology",
            "Quantum Computing",
            "Open Source Software",
        ]

        # Mock related topics
        mock_instance.related_topics.return_value = {
            "rising": {
                "test_topic": {"topic_title": "Test Topic", "value": "100%"}
            }
        }

        yield mock_trendreq_class


@pytest.fixture
def mock_youtube_client(sample_video_analytics, sample_channel_info):
    """Mock YouTubeClient for upload and analytics."""
    with patch("brainrot.youtube_client.YouTubeClient") as mock_client_class:
        mock_instance = MagicMock()
        mock_client_class.return_value = mock_instance

        # Mock authenticate
        mock_instance.authenticate.return_value = None

        # Mock upload_video - return success without actual upload
        from brainrot.types import UploadResult
        mock_instance.upload_video.return_value = UploadResult(
            video_id="test_video_001",
            platform="youtube",
            external_id="yt_external_123",
            status="success",
            uploaded_at=datetime.now(timezone.utc),
        )

        # Mock get_video_analytics
        mock_instance.get_video_analytics.return_value = sample_video_analytics

        # Mock get_channel_info
        mock_instance.get_channel_info.return_value = sample_channel_info

        yield mock_client_class


@pytest.fixture
def mock_quota_manager():
    """Mock QuotaManager for quota tracking."""
    with patch("brainrot.youtube_client.QuotaManager") as mock_quota_class:
        mock_instance = MagicMock()
        mock_quota_class.return_value = mock_instance

        mock_instance.can_upload.return_value = True
        mock_instance.remaining_quota.return_value = 10000
        mock_instance.record_upload.return_value = None
        mock_instance.uploads_remaining.return_value = 5

        yield mock_quota_class


@pytest.fixture
def mock_pexels_api(sample_pexels_response):
    """Mock Pexels API for stock footage search."""
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_pexels_response
        mock_get.return_value = mock_response
        yield mock_get


@pytest.fixture
def mock_pixabay_api(sample_pixabay_response):
    """Mock Pixabay API for stock footage search."""
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_pixabay_response
        mock_get.return_value = mock_response
        yield mock_get


@pytest.fixture
def mock_llm_client():
    """Mock LLMClient for script generation."""
    sample_script_text = (
        "Did you know AI is transforming how we live and work? "
        "This breakthrough technology is revolutionizing industries from healthcare to entertainment. "
        "Neural networks can now process information faster than ever before, enabling real-time "
        "decision making and predictions. The implications are staggering - imagine AI assistants "
        "that truly understand context and nuance. Major tech companies are investing billions "
        "into this research, and the results are already visible in our daily lives. From "
        "smartphone cameras to recommendation systems, AI is everywhere. But what does this mean "
        "for the future of work? Experts predict both disruption and opportunity. The key is "
        "adaptation and continuous learning. What's your take on the AI revolution?"
    )

    with patch("brainrot.llm_client.LLMClient") as mock_llm_class:
        mock_instance = MagicMock()
        mock_llm_class.return_value = mock_instance
        mock_instance.generate.return_value = sample_script_text
        mock_instance.provider = "groq"
        yield mock_llm_class


@pytest.fixture
def mock_tts(temp_audio_file):
    """Mock TTSClient for text-to-speech synthesis."""
    with patch("brainrot.audio.tts.TTSClient") as mock_tts_class:
        mock_instance = MagicMock()
        mock_tts_class.return_value = mock_instance

        # Mock synthesize to return a path to our temp audio file
        mock_instance.synthesize.return_value = temp_audio_file

        yield mock_tts_class


@pytest.fixture
def mock_ffmpeg():
    """Mock FFmpeg subprocess calls for video generation."""
    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Duration: 00:00:30.00"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        yield mock_run

    # Also need to mock the Popen for progress tracking
    with patch("subprocess.Popen") as mock_popen:
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stderr = iter([])
        mock_process.stdout = iter([])
        mock_popen.return_value = mock_process
        yield mock_popen


@pytest.fixture
def mock_video_builder(temp_video_file):
    """Mock VideoBuilder for video assembly."""
    with patch("brainrot.video.assembly.VideoBuilder") as mock_builder_class:
        mock_instance = MagicMock()
        mock_builder_class.return_value = mock_instance

        # Mock methods
        mock_instance.add_background.return_value = None
        mock_instance.add_captions.return_value = None
        mock_instance.add_audio.return_value = None
        mock_instance._get_audio_duration.return_value = 30.0
        mock_instance.render.return_value = temp_video_file

        yield mock_builder_class


@pytest.fixture
def mock_analytics_fetcher(sample_video_analytics):
    """Mock AnalyticsFetcher for performance tracking."""
    with patch("brainrot.analytics.fetcher.AnalyticsFetcher") as mock_fetcher_class:
        mock_instance = MagicMock()
        mock_fetcher_class.return_value = mock_instance

        # Mock fetch methods
        from brainrot.analytics.fetcher import VideoAnalytics
        mock_instance.fetch_video.return_value = VideoAnalytics(
            video_id="test_video_001",
            views=sample_video_analytics["views"],
            likes=sample_video_analytics["likes"],
            comments=sample_video_analytics["comments"],
            avg_view_duration=25.5,
            fetched_at=datetime.now(timezone.utc),
        )

        # Mock async methods
        mock_instance.store_video_analytics = AsyncMock(return_value=None)
        mock_instance.get_trending_videos = AsyncMock(return_value=[])

        yield mock_fetcher_class


@pytest.fixture
def mock_performance_agent():
    """Mock PerformanceAgent for analysis."""
    with patch("brainrot.agents.performance_agent.PerformanceAgent") as mock_agent_class:
        mock_instance = MagicMock()
        mock_agent_class.return_value = mock_instance

        from brainrot.agents.performance_agent import PerformanceReport
        mock_instance.generate_report.return_value = PerformanceReport(
            total_videos=1,
            total_views=15000,
            total_likes=850,
            avg_engagement_rate=0.065,
        )

        yield mock_agent_class


# ============================================================================
# Settings Fixture
# ============================================================================


@pytest.fixture
def mock_settings(temp_cache_dir):
    """Mock settings for testing without environment variables."""
    with patch("brainrot.config.settings") as mock_settings:
        mock_settings.cache_dir = temp_cache_dir
        mock_settings.youtube_api_key = "test_api_key"
        mock_settings.youtube_client_secrets_file = temp_cache_dir / "client_secrets.json"
        mock_settings.youtube_credentials_file = temp_cache_dir / "credentials.json"
        mock_settings.reddit_client_id = "test_client_id"
        mock_settings.reddit_client_secret = "test_client_secret"
        mock_settings.reddit_user_agent = "test_agent"
        mock_settings.groq_api_key = "test_groq_key"
        mock_settings.ollama_host = "http://localhost:11434"
        mock_settings.pexels_api_key = "test_pexels_key"
        mock_settings.pixabay_api_key = "test_pixabay_key"
        yield mock_settings


# ============================================================================
# Pipeline Fixtures
# ============================================================================


@pytest.fixture
def pipeline_config(temp_cache_dir, temp_output_dir, temp_state_file):
    """Create a pipeline config for testing."""
    from brainrot.pipeline.orchestrator import PipelineConfig
    return PipelineConfig(
        max_trends_per_run=3,
        max_videos_per_run=2,
        max_uploads_per_run=2,
        template="news_synthesis",
        voice="default",
        resume_on_failure=True,
        skip_completed_steps=True,
    )


@pytest.fixture
def pipeline(pipeline_config, temp_cache_dir, temp_output_dir, temp_state_file):
    """Create a Pipeline instance for testing."""
    from brainrot.pipeline.orchestrator import Pipeline
    return Pipeline(
        config=pipeline_config,
        state_file=temp_state_file,
        output_dir=temp_output_dir,
    )


# ============================================================================
# Integration Test Configuration
# ============================================================================


@pytest.fixture
def integration_test_mode():
    """Enable integration test mode to skip actual uploads."""
    return {
        "skip_upload": True,
        "skip_video_generation": True,
        "mock_all_apis": True,
    }


@pytest.fixture(autouse=True)
def setup_test_env(mock_settings, tmp_path):
    """Automatically set up test environment for all tests."""
    (tmp_path / "cache").mkdir(parents=True, exist_ok=True)
    yield
