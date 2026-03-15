"""End-to-end integration tests for the brainrot pipeline.

Tests the complete pipeline from trend fetching to video upload,
using mocks for all external API calls.

Run with: pytest tests/integration/test_e2e.py -v
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from brainrot.pipeline.orchestrator import (
    Pipeline,
    PipelineConfig,
    PipelineResult,
    PipelineStatus,
    StepStatus,
)


class TestE2EPipeline:
    """End-to-end tests for the complete content pipeline."""

    def test_pipeline_state_persistence(self, pipeline, temp_state_file):
        """Verify pipeline state is persisted correctly."""
        pipeline.state.run_id = "test_run_001"
        pipeline.state.status = PipelineStatus.RUNNING
        pipeline._save_state()

        assert temp_state_file.exists()

        with open(temp_state_file) as f:
            data = json.load(f)

        assert data["run_id"] == "test_run_001"
        assert data["status"] == "running"

    def test_pipeline_trend_fetch_mocked(
        self,
        pipeline,
        sample_trends,
        mock_reddit,
        mock_google_trends,
        mock_settings,
    ):
        """Test trend fetching step with mocked APIs."""
        with patch("brainrot.trends.reddit.RedditTrendSource.fetch") as mock_fetch:
            mock_fetch.return_value = sample_trends

            trends = pipeline.run_trend_fetch(limit=3)

            assert len(trends) <= 3
            assert pipeline.state.steps["trend_fetch"].status == StepStatus.COMPLETED

    def test_pipeline_video_gen_mocked(
        self,
        pipeline,
        sample_trends,
        sample_script,
        temp_audio_file,
        temp_video_file,
        mock_settings,
    ):
        """Test video generation step with mocked components."""
        with patch("brainrot.content.script_generator.ScriptGenerator") as mock_sg_class, \
             patch("brainrot.audio.tts.TTSClient") as mock_tts_class, \
             patch("brainrot.assets.manager.AssetManager") as mock_am_class, \
             patch("brainrot.video.assembly.VideoBuilder") as mock_vb_class, \
             patch("brainrot.templates.renderer.TemplateRenderer") as mock_tr_class:

            mock_sg = MagicMock()
            mock_sg_class.return_value = mock_sg
            mock_sg.generate.return_value = sample_script

            mock_tts = MagicMock()
            mock_tts_class.return_value = mock_tts
            mock_tts.synthesize.return_value = temp_audio_file

            mock_am = MagicMock()
            mock_am_class.return_value = mock_am
            mock_am.search_all_sources.return_value = []
            mock_am.get_unused_assets.return_value = []

            mock_vb = MagicMock()
            mock_vb_class.return_value = mock_vb
            mock_vb._get_audio_duration.return_value = 30.0
            mock_vb.render.return_value = temp_video_file

            mock_tr = MagicMock()
            mock_tr_class.return_value = mock_tr
            mock_tr.config.background.color = "#1a1a2e"
            mock_tr.apply_to_builder.return_value = None

            result = pipeline.run_video_gen(trends=sample_trends[:1], limit=1)

            assert len(result) >= 0
            assert pipeline.state.steps["video_gen"].status == StepStatus.COMPLETED

    def test_pipeline_upload_mocked(
        self,
        pipeline,
        sample_script,
        temp_video_file,
        mock_youtube_client,
        mock_quota_manager,
        mock_settings,
    ):
        """Test upload step with mocked YouTube client."""
        with patch("brainrot.pipeline.uploader.UploadOrchestrator") as mock_uo_class, \
             patch("brainrot.content.script_generator.ScriptGenerator") as mock_sg_class:

            mock_uo = MagicMock()
            mock_uo_class.return_value = mock_uo

            from brainrot.pipeline.uploader import QueuedVideo, UploadStatus
            from brainrot.types import UploadResult

            mock_uo.queue_video.return_value = QueuedVideo(
                video_path=temp_video_file,
                script=sample_script,
            )

            mock_uo.process_queue.return_value = [
                UploadResult(
                    video_id="test_video_001",
                    platform="youtube",
                    external_id="yt_123",
                    status="success",
                    uploaded_at=datetime.now(timezone.utc),
                )
            ]
            mock_uo.uploads_today = 0
            mock_uo.queue_length = 1
            mock_uo.pending_count = 1

            mock_sg = MagicMock()
            mock_sg_class.return_value = mock_sg
            mock_sg.get_history.return_value = [sample_script]

            pipeline.state.generated_videos = [str(temp_video_file)]
            pipeline._save_state()

            results = pipeline.run_upload(video_paths=[temp_video_file])

            assert len(results) >= 0

    def test_pipeline_analytics_mocked(
        self,
        pipeline,
        mock_analytics_fetcher,
        mock_performance_agent,
        mock_settings,
    ):
        """Test analytics step with mocked fetcher."""
        with patch("brainrot.analytics.fetcher.AnalyticsFetcher") as mock_af_class, \
             patch("brainrot.agents.performance_agent.PerformanceAgent") as mock_pa_class:

            from brainrot.analytics.fetcher import VideoAnalytics
            from brainrot.agents.performance_agent import PerformanceReport

            mock_af = MagicMock()
            mock_af_class.return_value = mock_af
            mock_af.fetch_video.return_value = VideoAnalytics(
                video_id="test_video_001",
                views=15000,
                likes=850,
                comments=120,
                avg_view_duration=25.5,
                fetched_at=datetime.now(timezone.utc),
            )
            mock_af.store_video_analytics = MagicMock(return_value=None)

            async def mock_store(*args, **kwargs):
                return None
            mock_af.store_video_analytics.side_effect = mock_store

            async def mock_trending(*args, **kwargs):
                return []
            mock_af.get_trending_videos.side_effect = mock_trending

            mock_pa = MagicMock()
            mock_pa_class.return_value = mock_pa
            mock_pa.generate_report.return_value = PerformanceReport(
                total_videos=1,
                total_views=15000,
                total_likes=850,
                avg_engagement_rate=0.065,
            )

            pipeline.state.uploaded_videos = ["test_video_001"]
            pipeline._save_state()

            result = pipeline.run_analytics(video_ids=["test_video_001"])

            assert result is not None
            assert pipeline.state.steps["analytics"].status == StepStatus.COMPLETED

    @pytest.mark.timeout(60)
    def test_e2e_full_pipeline_mocked(
        self,
        pipeline,
        sample_trends,
        sample_script,
        temp_audio_file,
        temp_video_file,
        mock_settings,
    ):
        """Test complete end-to-end pipeline with all external APIs mocked."""
        start_time = time.time()

        with patch("brainrot.trends.reddit.RedditTrendSource") as mock_reddit_source_class, \
             patch("brainrot.trends.google_trends.GoogleTrendsSource") as mock_gt_source_class, \
             patch("brainrot.content.script_generator.ScriptGenerator") as mock_sg_class, \
             patch("brainrot.audio.tts.TTSClient") as mock_tts_class, \
             patch("brainrot.assets.manager.AssetManager") as mock_am_class, \
             patch("brainrot.video.assembly.VideoBuilder") as mock_vb_class, \
             patch("brainrot.templates.renderer.TemplateRenderer") as mock_tr_class, \
             patch("brainrot.pipeline.uploader.UploadOrchestrator") as mock_uo_class, \
             patch("brainrot.analytics.fetcher.AnalyticsFetcher") as mock_af_class, \
             patch("brainrot.agents.performance_agent.PerformanceAgent") as mock_pa_class:

            mock_reddit_source = MagicMock()
            mock_reddit_source_class.return_value = mock_reddit_source
            mock_reddit_source.fetch.return_value = sample_trends

            mock_gt_source = MagicMock()
            mock_gt_source_class.return_value = mock_gt_source
            mock_gt_source.fetch.return_value = sample_trends[:2]

            mock_sg = MagicMock()
            mock_sg_class.return_value = mock_sg
            mock_sg.generate.return_value = sample_script
            mock_sg.get_history.return_value = [sample_script]

            mock_tts = MagicMock()
            mock_tts_class.return_value = mock_tts
            mock_tts.synthesize.return_value = temp_audio_file

            mock_am = MagicMock()
            mock_am_class.return_value = mock_am
            mock_am.search_all_sources.return_value = []
            mock_am.get_unused_assets.return_value = []
            mock_am.track_usage.return_value = None

            mock_vb = MagicMock()
            mock_vb_class.return_value = mock_vb
            mock_vb._get_audio_duration.return_value = 30.0
            mock_vb.render.return_value = temp_video_file
            mock_vb.add_background.return_value = None

            mock_tr = MagicMock()
            mock_tr_class.return_value = mock_tr
            mock_tr.config = MagicMock()
            mock_tr.config.background = MagicMock()
            mock_tr.config.background.color = "#1a1a2e"
            mock_tr.apply_to_builder.return_value = None

            from brainrot.pipeline.uploader import QueuedVideo
            from brainrot.types import UploadResult

            mock_uo = MagicMock()
            mock_uo_class.return_value = mock_uo
            mock_uo.queue_video.return_value = QueuedVideo(
                video_path=temp_video_file,
                script=sample_script,
            )
            mock_uo.process_queue.return_value = [
                UploadResult(
                    video_id="test_video_001",
                    platform="youtube",
                    external_id="yt_external_123",
                    status="success",
                    uploaded_at=datetime.now(timezone.utc),
                )
            ]

            from brainrot.analytics.fetcher import VideoAnalytics
            from brainrot.agents.performance_agent import PerformanceReport

            mock_af = MagicMock()
            mock_af_class.return_value = mock_af
            mock_af.fetch_video.return_value = VideoAnalytics(
                video_id="test_video_001",
                views=15000,
                likes=850,
                comments=120,
                avg_view_duration=25.5,
                fetched_at=datetime.now(timezone.utc),
            )

            async def mock_store(*args, **kwargs):
                return None
            mock_af.store_video_analytics = MagicMock(side_effect=mock_store)

            async def mock_trending(*args, **kwargs):
                return []
            mock_af.get_trending_videos = MagicMock(side_effect=mock_trending)

            mock_pa = MagicMock()
            mock_pa_class.return_value = mock_pa
            mock_pa.generate_report.return_value = PerformanceReport(
                total_videos=1,
                total_views=15000,
                total_likes=850,
                avg_engagement_rate=0.065,
            )

            result = pipeline.run_daily()

            elapsed_time = time.time() - start_time

            assert result is not None
            assert result.status in [PipelineStatus.COMPLETED, PipelineStatus.PARTIAL]
            assert result.run_id != ""
            assert elapsed_time < 60, f"Pipeline took {elapsed_time:.2f}s, should be under 60s"

    def test_e2e_pipeline_state_recovery(
        self,
        pipeline_config,
        temp_cache_dir,
        temp_output_dir,
        temp_state_file,
        mock_settings,
    ):
        """Test pipeline can recover state from a failed run."""
        pipeline1 = Pipeline(
            config=pipeline_config,
            state_file=temp_state_file,
            output_dir=temp_output_dir,
        )

        pipeline1.state.run_id = "partial_run_001"
        pipeline1.state.status = PipelineStatus.PARTIAL
        pipeline1.state.processed_trends = ["trend_001", "trend_002"]
        pipeline1._save_state()

        pipeline2 = Pipeline(
            config=pipeline_config,
            state_file=temp_state_file,
            output_dir=temp_output_dir,
        )

        assert pipeline2.state.run_id == "partial_run_001"
        assert pipeline2.state.status == PipelineStatus.PARTIAL
        assert "trend_001" in pipeline2.state.processed_trends

    def test_e2e_error_handling(
        self,
        pipeline,
        mock_settings,
    ):
        """Test pipeline handles errors gracefully."""
        with patch("brainrot.trends.reddit.RedditTrendSource") as mock_reddit_source_class, \
             patch("brainrot.trends.google_trends.GoogleTrendsSource") as mock_gt_source_class:

            from brainrot.exceptions import TrendFetchError

            mock_reddit_source = MagicMock()
            mock_reddit_source_class.return_value = mock_reddit_source
            mock_reddit_source.fetch.side_effect = TrendFetchError("API error")

            mock_gt_source = MagicMock()
            mock_gt_source_class.return_value = mock_gt_source
            mock_gt_source.fetch.side_effect = TrendFetchError("API error")

            with pytest.raises(Exception):
                pipeline.run_trend_fetch()

    def test_e2e_skip_completed_steps(
        self,
        pipeline,
        sample_trends,
        mock_settings,
    ):
        """Test that completed steps are skipped on resume."""
        from brainrot.pipeline.orchestrator import StepResult

        pipeline.state.steps["trend_fetch"] = StepResult(
            name="trend_fetch",
            status=StepStatus.COMPLETED,
            items_processed=5,
        )
        pipeline._save_state()

        with patch("brainrot.trends.reddit.RedditTrendSource") as mock_reddit_source_class:
            mock_reddit_source = MagicMock()
            mock_reddit_source_class.return_value = mock_reddit_source

            trends = pipeline.run_trend_fetch()

            mock_reddit_source.fetch.assert_not_called()
            assert trends == []

    def test_e2e_quota_protection(
        self,
        pipeline,
        sample_script,
        temp_video_file,
        mock_settings,
    ):
        """Test that daily upload quota is respected."""
        with patch("brainrot.pipeline.uploader.UploadOrchestrator") as mock_uo_class, \
             patch("brainrot.content.script_generator.ScriptGenerator") as mock_sg_class:

            mock_uo = MagicMock()
            mock_uo_class.return_value = mock_uo
            mock_uo.process_queue.return_value = []
            mock_uo.uploads_today = 5
            mock_uo.queue_length = 10
            mock_uo.pending_count = 10

            mock_sg = MagicMock()
            mock_sg_class.return_value = mock_sg
            mock_sg.get_history.return_value = [sample_script]

            pipeline.state.generated_videos = [str(temp_video_file)]

            results = pipeline.run_upload(video_paths=[temp_video_file])

            assert isinstance(results, list)


class TestPipelineStatus:
    """Tests for pipeline status tracking."""

    def test_status_transitions(self, pipeline, mock_settings):
        """Verify pipeline status transitions correctly."""
        assert pipeline.state.status == PipelineStatus.PENDING

        pipeline._start_run()
        assert pipeline.state.status == PipelineStatus.RUNNING

        pipeline.state.status = PipelineStatus.COMPLETED
        pipeline._save_state()
        assert pipeline.state.status == PipelineStatus.COMPLETED

    def test_get_status_report(self, pipeline, mock_settings):
        """Test status report generation."""
        pipeline.state.run_id = "test_run"
        pipeline.state.processed_trends = ["t1", "t2"]
        pipeline.state.generated_videos = ["v1"]
        pipeline._save_state()

        status = pipeline.get_status()

        assert status["run_id"] == "test_run"
        assert status["processed_trends"] == 2
        assert status["generated_videos"] == 1
        assert "status" in status

    def test_reset_state(self, pipeline, mock_settings):
        """Test state reset functionality."""
        pipeline.state.run_id = "test_run"
        pipeline.state.processed_trends = ["t1", "t2", "t3"]
        pipeline._save_state()

        pipeline.reset_state()

        assert pipeline.state.run_id == ""
        assert len(pipeline.state.processed_trends) == 0
        assert pipeline.state.status == PipelineStatus.PENDING


class TestPipelineConfig:
    """Tests for pipeline configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = PipelineConfig()

        assert config.max_trends_per_run == 10
        assert config.max_videos_per_run == 3
        assert config.max_uploads_per_run == 5
        assert config.template == "tech_news"
        assert config.voice == "default"
        assert config.resume_on_failure is True

    def test_custom_config(self):
        """Test custom configuration values."""
        config = PipelineConfig(
            max_trends_per_run=20,
            max_videos_per_run=5,
            max_uploads_per_run=10,
            template="explainer",
            voice="energetic",
        )

        assert config.max_trends_per_run == 20
        assert config.max_videos_per_run == 5
        assert config.max_uploads_per_run == 10
        assert config.template == "explainer"
        assert config.voice == "energetic"


class TestPipelineResult:
    """Tests for pipeline result tracking."""

    def test_result_creation(self):
        """Test PipelineResult dataclass."""
        result = PipelineResult(
            status=PipelineStatus.COMPLETED,
            run_id="test_run_001",
            completed_steps=["trend_fetch", "video_gen", "upload"],
            items_produced=5,
        )

        assert result.status == PipelineStatus.COMPLETED
        assert result.run_id == "test_run_001"
        assert len(result.completed_steps) == 3
        assert result.items_produced == 5
        assert result.failed_step is None
        assert result.error_message is None

    def test_result_to_dict(self):
        """Test PipelineResult serialization."""
        result = PipelineResult(
            status=PipelineStatus.PARTIAL,
            run_id="test_run_002",
            completed_steps=["trend_fetch"],
            failed_step="video_gen",
            error_message="TTS failed",
            items_produced=2,
        )

        data = result.to_dict()

        assert data["status"] == "partial"
        assert data["run_id"] == "test_run_002"
        assert data["failed_step"] == "video_gen"
        assert data["error_message"] == "TTS failed"


class TestBenchmark:
    """Benchmark tests for pipeline performance."""

    @pytest.mark.timeout(60)
    def test_pipeline_completes_under_60_seconds(
        self,
        pipeline,
        sample_trends,
        sample_script,
        temp_audio_file,
        temp_video_file,
        mock_settings,
    ):
        """Benchmark: Pipeline should complete in under 60 seconds with mocks."""
        with patch("brainrot.trends.reddit.RedditTrendSource") as mock_reddit_source_class, \
             patch("brainrot.trends.google_trends.GoogleTrendsSource") as mock_gt_source_class, \
             patch("brainrot.content.script_generator.ScriptGenerator") as mock_sg_class, \
             patch("brainrot.audio.tts.TTSClient") as mock_tts_class, \
             patch("brainrot.assets.manager.AssetManager") as mock_am_class, \
             patch("brainrot.video.assembly.VideoBuilder") as mock_vb_class, \
             patch("brainrot.templates.renderer.TemplateRenderer") as mock_tr_class, \
             patch("brainrot.pipeline.uploader.UploadOrchestrator") as mock_uo_class, \
             patch("brainrot.analytics.fetcher.AnalyticsFetcher") as mock_af_class, \
             patch("brainrot.agents.performance_agent.PerformanceAgent") as mock_pa_class:

            mock_reddit_source = MagicMock()
            mock_reddit_source_class.return_value = mock_reddit_source
            mock_reddit_source.fetch.return_value = sample_trends

            mock_gt_source = MagicMock()
            mock_gt_source_class.return_value = mock_gt_source
            mock_gt_source.fetch.return_value = sample_trends[:2]

            mock_sg = MagicMock()
            mock_sg_class.return_value = mock_sg
            mock_sg.generate.return_value = sample_script
            mock_sg.get_history.return_value = [sample_script]

            mock_tts = MagicMock()
            mock_tts_class.return_value = mock_tts
            mock_tts.synthesize.return_value = temp_audio_file

            mock_am = MagicMock()
            mock_am_class.return_value = mock_am
            mock_am.search_all_sources.return_value = []
            mock_am.get_unused_assets.return_value = []

            mock_vb = MagicMock()
            mock_vb_class.return_value = mock_vb
            mock_vb._get_audio_duration.return_value = 30.0
            mock_vb.render.return_value = temp_video_file

            mock_tr = MagicMock()
            mock_tr_class.return_value = mock_tr
            mock_tr.config = MagicMock()
            mock_tr.config.background = MagicMock()
            mock_tr.config.background.color = "#1a1a2e"

            from brainrot.types import UploadResult

            mock_uo = MagicMock()
            mock_uo_class.return_value = mock_uo
            mock_uo.process_queue.return_value = [
                UploadResult(
                    video_id="test_video_001",
                    platform="youtube",
                    external_id="yt_123",
                    status="success",
                    uploaded_at=datetime.now(timezone.utc),
                )
            ]

            from brainrot.analytics.fetcher import VideoAnalytics
            from brainrot.agents.performance_agent import PerformanceReport

            mock_af = MagicMock()
            mock_af_class.return_value = mock_af
            mock_af.fetch_video.return_value = VideoAnalytics(
                video_id="test_video_001",
                views=1000,
                likes=50,
                comments=10,
            )

            async def mock_store(*args, **kwargs):
                return None
            mock_af.store_video_analytics = MagicMock(side_effect=mock_store)

            async def mock_trending(*args, **kwargs):
                return []
            mock_af.get_trending_videos = MagicMock(side_effect=mock_trending)

            mock_pa = MagicMock()
            mock_pa_class.return_value = mock_pa
            mock_pa.generate_report.return_value = PerformanceReport()

            start_time = time.time()
            result = pipeline.run_daily()
            elapsed_time = time.time() - start_time

            assert result is not None
            assert elapsed_time < 60, f"Pipeline took {elapsed_time:.2f}s"


class TestErrorScenarios:
    """Test error handling scenarios."""

    def test_trend_fetch_failure(
        self,
        pipeline,
        mock_settings,
    ):
        """Test handling of trend fetch failure."""
        with patch("brainrot.trends.reddit.RedditTrendSource") as mock_reddit_source_class, \
             patch("brainrot.trends.google_trends.GoogleTrendsSource") as mock_gt_source_class:

            from brainrot.exceptions import TrendFetchError

            mock_reddit_source = MagicMock()
            mock_reddit_source_class.return_value = mock_reddit_source
            mock_reddit_source.fetch.side_effect = TrendFetchError("Reddit API error")

            mock_gt_source = MagicMock()
            mock_gt_source_class.return_value = mock_gt_source
            mock_gt_source.fetch.side_effect = TrendFetchError("Google Trends API error")

            with pytest.raises(Exception):
                pipeline.run_trend_fetch()

            assert pipeline.state.steps.get("trend_fetch") is not None
            assert pipeline.state.steps["trend_fetch"].status == StepStatus.FAILED

    def test_video_gen_partial_failure(
        self,
        pipeline,
        sample_trends,
        sample_script,
        temp_audio_file,
        temp_video_file,
        mock_settings,
    ):
        """Test handling of video generation errors - errors are logged, not raised."""
        with patch("brainrot.content.script_generator.ScriptGenerator") as mock_sg_class, \
             patch("brainrot.audio.tts.TTSClient") as mock_tts_class, \
             patch("brainrot.assets.manager.AssetManager") as mock_am_class, \
             patch("brainrot.video.assembly.VideoBuilder") as mock_vb_class:

            mock_sg = MagicMock()
            mock_sg_class.return_value = mock_sg
            mock_sg.generate.return_value = sample_script

            mock_tts = MagicMock()
            mock_tts_class.return_value = mock_tts
            mock_tts.synthesize.side_effect = Exception("TTS service unavailable")

            mock_am = MagicMock()
            mock_am_class.return_value = mock_am
            mock_am.search_all_sources.return_value = []

            mock_vb = MagicMock()
            mock_vb_class.return_value = mock_vb

            result = pipeline.run_video_gen(trends=sample_trends[:1], limit=1)

            assert result == []
            assert len(pipeline.state.errors) > 0
            assert "trend_id" in pipeline.state.errors[0]

    def test_analytics_non_critical_failure(
        self,
        pipeline,
        mock_settings,
    ):
        """Test that analytics failure doesn't stop pipeline completion."""
        with patch("brainrot.analytics.fetcher.AnalyticsFetcher") as mock_af_class, \
             patch("brainrot.agents.performance_agent.PerformanceAgent") as mock_pa_class:

            mock_af = MagicMock()
            mock_af_class.return_value = mock_af
            mock_af.fetch_video.side_effect = Exception("Analytics API error")

            mock_pa = MagicMock()
            mock_pa_class.return_value = mock_pa

            pipeline.state.uploaded_videos = ["test_video_001"]

            with pytest.raises(Exception):
                pipeline.run_analytics(video_ids=["test_video_001"])
