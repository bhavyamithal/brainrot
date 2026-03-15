"""Main orchestration pipeline for the brainrot platform.

Coordinates all components for end-to-end video production:
- Trend fetching and aggregation
- Script generation
- Text-to-speech synthesis
- Video assembly with templates
- YouTube upload with quota management
- Analytics fetching and performance analysis

Provides state management for resume-from-failure capability.
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_TEMPLATE = "tech_news"
DEFAULT_VOICE = "default"


class PipelineStatus(str, Enum):
    """Status of pipeline execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


class StepStatus(str, Enum):
    """Status of individual pipeline steps."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass
class StepResult:
    """Result of a single pipeline step.

    Attributes:
        name: Step name identifier.
        status: Current status of the step.
        started_at: When the step started.
        completed_at: When the step completed.
        items_processed: Number of items processed.
        error: Error message if failed.
        details: Additional step details.
    """

    name: str
    status: StepStatus = StepStatus.PENDING
    started_at: datetime | None = None
    completed_at: datetime | None = None
    items_processed: int = 0
    error: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "items_processed": self.items_processed,
            "error": self.error,
            "details": self.details,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StepResult:
        """Create from dictionary."""
        return cls(
            name=data["name"],
            status=StepStatus(data.get("status", "pending")),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            items_processed=data.get("items_processed", 0),
            error=data.get("error"),
            details=data.get("details", {}),
        )


@dataclass
class PipelineState:
    """State tracking for pipeline execution.

    Persists to JSON file for resume-from-failure capability.

    Attributes:
        last_run: Timestamp of last pipeline run.
        run_id: Unique identifier for current run.
        status: Overall pipeline status.
        steps: Results for each pipeline step.
        processed_trends: IDs of processed trends.
        generated_videos: Paths to generated video files.
        pending_videos: Videos waiting to be uploaded.
        uploaded_videos: IDs of uploaded videos.
        errors: Accumulated errors during execution.
    """

    last_run: datetime | None = None
    run_id: str = ""
    status: PipelineStatus = PipelineStatus.PENDING
    steps: dict[str, StepResult] = field(default_factory=dict)
    processed_trends: list[str] = field(default_factory=list)
    generated_videos: list[str] = field(default_factory=list)
    pending_videos: list[str] = field(default_factory=list)
    uploaded_videos: list[str] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "run_id": self.run_id,
            "status": self.status.value,
            "steps": {k: v.to_dict() for k, v in self.steps.items()},
            "processed_trends": self.processed_trends,
            "generated_videos": self.generated_videos,
            "pending_videos": self.pending_videos,
            "uploaded_videos": self.uploaded_videos,
            "errors": self.errors,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PipelineState:
        """Create from dictionary."""
        steps = {}
        for k, v in data.get("steps", {}).items():
            steps[k] = StepResult.from_dict(v)

        return cls(
            last_run=datetime.fromisoformat(data["last_run"]) if data.get("last_run") else None,
            run_id=data.get("run_id", ""),
            status=PipelineStatus(data.get("status", "pending")),
            steps=steps,
            processed_trends=data.get("processed_trends", []),
            generated_videos=data.get("generated_videos", []),
            pending_videos=data.get("pending_videos", []),
            uploaded_videos=data.get("uploaded_videos", []),
            errors=data.get("errors", []),
        )


@dataclass
class PipelineResult:
    """Result of a pipeline execution.

    Attributes:
        status: Overall execution status.
        run_id: Unique identifier for this run.
        completed_steps: List of successfully completed steps.
        failed_step: Name of the step that failed (if any).
        error_message: Error message if failed.
        items_produced: Count of items produced (trends, videos, uploads).
        state: Final pipeline state.
    """

    status: PipelineStatus
    run_id: str
    completed_steps: list[str] = field(default_factory=list)
    failed_step: str | None = None
    error_message: str | None = None
    items_produced: int = 0
    state: PipelineState | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status.value,
            "run_id": self.run_id,
            "completed_steps": self.completed_steps,
            "failed_step": self.failed_step,
            "error_message": self.error_message,
            "items_produced": self.items_produced,
        }


@dataclass
class PipelineConfig:
    """Configuration for pipeline behavior.

    Attributes:
        max_trends_per_run: Maximum trends to fetch per run.
        max_videos_per_run: Maximum videos to generate per run.
        max_uploads_per_run: Maximum uploads per run (quota protection).
        template: Default template for video generation.
        voice: Default voice profile for TTS.
        resume_on_failure: Whether to resume from failure point.
        skip_completed_steps: Skip already completed steps on resume.
    """

    max_trends_per_run: int = 10
    max_videos_per_run: int = 3
    max_uploads_per_run: int = 5
    template: str = DEFAULT_TEMPLATE
    voice: str = DEFAULT_VOICE
    resume_on_failure: bool = True
    skip_completed_steps: bool = True


def _get_default_state_file() -> Path:
    """Get default state file path with lazy settings import."""
    from brainrot.config import settings

    return settings.cache_dir / "pipeline_state.json"


def _get_default_output_dir() -> Path:
    """Get default output directory for videos."""
    from brainrot.config import settings

    output_dir = settings.cache_dir / "videos"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


class Pipeline:
    """Main orchestration pipeline for video content production.

    Coordinates all components in sequence:
    1. TrendAggregator - Fetch trending content
    2. ScriptGenerator - Generate scripts from trends
    3. TTSClient - Synthesize audio narration
    4. AssetManager - Get background footage
    5. VideoBuilder - Assemble final video
    6. UploadOrchestrator - Upload to YouTube
    7. AnalyticsFetcher - Fetch performance data
    8. PerformanceAgent - Analyze and recommend

    Attributes:
        config: Pipeline configuration.
        state: Current pipeline state.
        state_file: Path to state persistence file.
    """

    def __init__(
        self,
        config: PipelineConfig | None = None,
        state_file: Path | None = None,
        output_dir: Path | None = None,
    ) -> None:
        """Initialize the pipeline.

        Args:
            config: Pipeline configuration options.
            state_file: Path to state persistence file.
            output_dir: Directory for generated videos.
        """
        self.config = config or PipelineConfig()
        self.state_file = state_file or _get_default_state_file()
        self.output_dir = output_dir or _get_default_output_dir()
        self.state = self._load_state()

        self._trend_aggregator = None
        self._script_generator = None
        self._tts_client = None
        self._asset_manager = None
        self._upload_orchestrator = None
        self._analytics_fetcher = None
        self._performance_agent = None

    def _load_state(self) -> PipelineState:
        """Load state from persistence file."""
        if self.state_file.exists():
            try:
                with open(self.state_file) as f:
                    data = json.load(f)
                logger.info(f"Loaded pipeline state from {self.state_file}")
                return PipelineState.from_dict(data)
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to load state: {e}")
        return PipelineState()

    def _save_state(self) -> None:
        """Persist state to file."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, "w") as f:
            json.dump(self.state.to_dict(), f, indent=2)
        logger.debug(f"Saved pipeline state to {self.state_file}")

    def _get_trend_aggregator(self):
        """Get or create TrendAggregator lazily."""
        if self._trend_aggregator is None:
            from brainrot.trends import GoogleTrendsSource, RedditTrendSource, TrendAggregator

            sources = [
                RedditTrendSource(),
                GoogleTrendsSource(),
            ]
            self._trend_aggregator = TrendAggregator(sources=sources)
        return self._trend_aggregator

    def _get_script_generator(self):
        """Get or create ScriptGenerator lazily."""
        if self._script_generator is None:
            from brainrot.content import ScriptGenerator

            self._script_generator = ScriptGenerator()
        return self._script_generator

    def _get_tts_client(self):
        """Get or create TTSClient lazily."""
        if self._tts_client is None:
            from brainrot.audio import TTSClient

            self._tts_client = TTSClient()
        return self._tts_client

    def _get_asset_manager(self):
        """Get or create AssetManager lazily."""
        if self._asset_manager is None:
            from brainrot.assets import AssetManager

            self._asset_manager = AssetManager()
        return self._asset_manager

    def _get_upload_orchestrator(self):
        """Get or create UploadOrchestrator lazily."""
        if self._upload_orchestrator is None:
            from brainrot.pipeline.uploader import UploadOrchestrator

            self._upload_orchestrator = UploadOrchestrator()
        return self._upload_orchestrator

    def _get_analytics_fetcher(self):
        """Get or create AnalyticsFetcher lazily."""
        if self._analytics_fetcher is None:
            from brainrot.analytics import AnalyticsFetcher

            self._analytics_fetcher = AnalyticsFetcher()
        return self._analytics_fetcher

    def _get_performance_agent(self):
        """Get or create PerformanceAgent lazily."""
        if self._performance_agent is None:
            from brainrot.agents import PerformanceAgent

            self._performance_agent = PerformanceAgent()
        return self._performance_agent

    def _should_skip_step(self, step_name: str) -> bool:
        """Check if a step should be skipped (already completed)."""
        if not self.config.skip_completed_steps:
            return False

        step = self.state.steps.get(step_name)
        return step is not None and step.status == StepStatus.COMPLETED

    def _start_step(self, step_name: str) -> StepResult:
        """Mark a step as started."""
        step = StepResult(
            name=step_name,
            status=StepStatus.RUNNING,
            started_at=datetime.now(timezone.utc),
        )
        self.state.steps[step_name] = step
        self._save_state()
        logger.info(f"Starting step: {step_name}")
        return step

    def _complete_step(
        self, step_name: str, items_processed: int = 0, details: dict[str, Any] | None = None
    ) -> None:
        """Mark a step as completed."""
        step = self.state.steps.get(step_name)
        if step:
            step.status = StepStatus.COMPLETED
            step.completed_at = datetime.now(timezone.utc)
            step.items_processed = items_processed
            if details:
                step.details = details
        self._save_state()
        logger.info(f"Completed step: {step_name} ({items_processed} items)")

    def _fail_step(self, step_name: str, error: str) -> None:
        """Mark a step as failed."""
        step = self.state.steps.get(step_name)
        if step:
            step.status = StepStatus.FAILED
            step.completed_at = datetime.now(timezone.utc)
            step.error = error

        self.state.errors.append({
            "step": step_name,
            "error": error,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        self.state.status = PipelineStatus.PARTIAL
        self._save_state()
        logger.error(f"Step failed: {step_name} - {error}")

    def _start_run(self) -> str:
        """Initialize a new pipeline run."""
        run_id = str(uuid.uuid4())[:8]

        # Reset state if not resuming
        if not self.config.resume_on_failure or self.state.status == PipelineStatus.COMPLETED:
            self.state = PipelineState()

        self.state.run_id = run_id
        self.state.status = PipelineStatus.RUNNING
        self.state.last_run = datetime.now(timezone.utc)
        self._save_state()

        logger.info(f"Starting pipeline run: {run_id}")
        return run_id

    def run_trend_fetch(self, limit: int | None = None) -> list[Any]:
        """Execute the trend fetching step.

        Fetches trends from all configured sources, deduplicates,
        and returns unprocessed trends.

        Args:
            limit: Maximum trends to fetch. Uses config default if None.

        Returns:
            List of Trend objects ready for script generation.
        """
        step_name = "trend_fetch"
        if self._should_skip_step(step_name):
            logger.info(f"Skipping completed step: {step_name}")
            return []

        self._start_step(step_name)

        try:
            limit = limit or self.config.max_trends_per_run
            aggregator = self._get_trend_aggregator()

            trends = aggregator.get_trends(
                limit=limit,
                exclude_processed=True,
            )

            unprocessed = [
                t for t in trends
                if t.id not in self.state.processed_trends
            ]

            self._complete_step(step_name, items_processed=len(unprocessed))
            return unprocessed

        except Exception as e:
            self._fail_step(step_name, str(e))
            raise

    def run_video_gen(
        self,
        trends: list[Any] | None = None,
        limit: int | None = None,
    ) -> list[Path]:
        """Execute the video generation pipeline.

        For each trend:
        1. Generate script using ScriptGenerator
        2. Synthesize audio using TTSClient
        3. Get background footage using AssetManager
        4. Assemble video using VideoBuilder with TemplateRenderer

        Args:
            trends: Trends to process. Fetched if None.
            limit: Maximum videos to generate. Uses config default if None.

        Returns:
            List of paths to generated video files.
        """
        step_name = "video_gen"
        if self._should_skip_step(step_name):
            logger.info(f"Skipping completed step: {step_name}")
            return [Path(p) for p in self.state.generated_videos]

        self._start_step(step_name)
        generated_videos: list[Path] = []

        try:
            if trends is None:
                trends = self.run_trend_fetch()

            limit = limit or self.config.max_videos_per_run
            trends_to_process = trends[:limit]

            script_gen = self._get_script_generator()
            tts_client = self._get_tts_client()
            asset_manager = self._get_asset_manager()

            for trend in trends_to_process:
                try:
                    if trend.id in self.state.processed_trends:
                        logger.debug(f"Skipping processed trend: {trend.id}")
                        continue

                    logger.info(f"Processing trend: {trend.title[:50]}...")

                    script = script_gen.generate(
                        trend=trend,
                        template=self.config.template,
                    )
                    logger.debug(f"Generated script: {script.id}")

                    audio_path = tts_client.synthesize(
                        text=script.text,
                        voice=self.config.voice,
                    )
                    logger.debug(f"Synthesized audio: {audio_path}")

                    keywords = trend.keywords[:3] if trend.keywords else ["technology"]
                    search_query = " ".join(keywords)

                    try:
                        assets = asset_manager.search_all_sources(search_query, limit_per_source=2)
                        if assets:
                            unused = asset_manager.get_unused_assets(assets)
                            background_source = unused[0] if unused else assets[0]
                        else:
                            background_source = {"url": None, "id": "default"}
                    except Exception as e:
                        logger.warning(f"Asset search failed, using solid color: {e}")
                        background_source = {"url": None, "id": "default"}

                    from brainrot.templates import TemplateRenderer
                    from brainrot.video import VideoBuilder

                    builder = VideoBuilder(output_dir=self.output_dir)
                    renderer = TemplateRenderer(self.config.template)

                    if background_source.get("url"):
                        try:
                            bg_path = asset_manager.download(
                                background_source["url"],
                                f"bg_{trend.id[:8]}.mp4",
                            )
                            duration = builder._get_audio_duration(audio_path)
                            builder.add_background(bg_path, duration)
                        except Exception as e:
                            logger.warning(f"Background download failed: {e}")
                            bg_color = renderer.config.background.color
                            duration = builder._get_audio_duration(audio_path)
                            builder.add_background(bg_color, duration)
                    else:
                        bg_color = renderer.config.background.color
                        duration = builder._get_audio_duration(audio_path)
                        builder.add_background(bg_color, duration)

                    renderer.apply_to_builder(builder, script, audio_path, duration)

                    video_path = builder.render()
                    generated_videos.append(video_path)

                    self.state.processed_trends.append(trend.id)
                    self.state.generated_videos.append(str(video_path))
                    self._save_state()

                    if background_source.get("id"):
                        asset_manager.track_usage(
                            background_source["id"],
                            context=trend.title,
                        )

                    logger.info(f"Generated video: {video_path}")

                except Exception as e:
                    logger.error(f"Failed to process trend {trend.id}: {e}")
                    self.state.errors.append({
                        "trend_id": trend.id,
                        "error": str(e),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
                    continue

            self._complete_step(step_name, items_processed=len(generated_videos))
            return generated_videos

        except Exception as e:
            self._fail_step(step_name, str(e))
            raise

    def run_upload(self, video_paths: list[Path] | None = None) -> list[Any]:
        """Execute the upload step.

        Queues generated videos and processes the upload queue.
        Respects daily upload limits and YouTube quota.

        Args:
            video_paths: Videos to upload. Uses pending videos if None.

        Returns:
            List of UploadResult objects.
        """
        step_name = "upload"
        if self._should_skip_step(step_name):
            logger.info(f"Skipping completed step: {step_name}")
            return []

        self._start_step(step_name)

        try:
            orchestrator = self._get_upload_orchestrator()
            script_gen = self._get_script_generator()

            if video_paths is None:
                video_paths = [Path(p) for p in self.state.generated_videos]

            results = []

            for video_path in video_paths:
                if str(video_path) in self.state.uploaded_videos:
                    logger.debug(f"Skipping uploaded video: {video_path}")
                    continue

                scripts = script_gen.get_history(limit=50)
                script = scripts[-1] if scripts else None

                if script is None:
                    logger.warning(f"No script found for video: {video_path}")
                    continue

                orchestrator.queue_video(video_path, script)
                self.state.pending_videos.append(str(video_path))
                self._save_state()

            upload_results = orchestrator.process_queue(
                human_review=False,
                max_uploads=self.config.max_uploads_per_run,
            )

            for result in upload_results:
                if result.status == "success" and result.video_id:
                    self.state.uploaded_videos.append(result.video_id)
                    if str(result.video_id) in self.state.pending_videos:
                        self.state.pending_videos.remove(str(result.video_id))

            self._save_state()
            self._complete_step(step_name, items_processed=len(upload_results))
            return upload_results

        except Exception as e:
            self._fail_step(step_name, str(e))
            raise

    def run_analytics(self, video_ids: list[str] | None = None) -> dict[str, Any]:
        """Execute the analytics fetching and analysis step.

        Fetches performance data for uploaded videos and generates
        recommendations using the PerformanceAgent.

        Args:
            video_ids: Video IDs to analyze. Uses uploaded videos if None.

        Returns:
            Dictionary with analytics results and recommendations.
        """
        step_name = "analytics"
        if self._should_skip_step(step_name):
            logger.info(f"Skipping completed step: {step_name}")
            return {}

        self._start_step(step_name)

        try:
            fetcher = self._get_analytics_fetcher()
            agent = self._get_performance_agent()

            if video_ids is None:
                video_ids = self.state.uploaded_videos

            if not video_ids:
                logger.info("No videos to analyze")
                self._complete_step(step_name, items_processed=0)
                return {"status": "no_videos"}

            analytics_data = []
            for video_id in video_ids:
                try:
                    analytics = fetcher.fetch_video(video_id)
                    asyncio.run(fetcher.store_video_analytics(analytics))
                    analytics_data.append(analytics)
                except Exception as e:
                    logger.warning(f"Failed to fetch analytics for {video_id}: {e}")

            report = agent.generate_report(days=7)

            result = {
                "videos_analyzed": len(analytics_data),
                "total_views": report.total_views,
                "total_likes": report.total_likes,
                "avg_engagement_rate": report.avg_engagement_rate,
                "viral_alerts": len(report.viral_alerts),
                "recommendations": [
                    {
                        "type": r.type.value,
                        "title": r.title,
                        "description": r.description,
                        "confidence": r.confidence,
                    }
                    for r in report.recommendations[:5]
                ],
            }

            self._complete_step(
                step_name,
                items_processed=len(analytics_data),
                details=result,
            )
            return result

        except Exception as e:
            self._fail_step(step_name, str(e))
            raise

    def run_daily(self) -> PipelineResult:
        """Execute the full daily pipeline.

    Full pipeline execution sequence:
    1. Fetch trends
    2. Generate videos from trends
    3. Upload generated videos
    4. Fetch and analyze analytics

    State is persisted after each step for resume capability.

    Returns:
        PipelineResult with execution status and details.
    """
        run_id = self._start_run()
        completed_steps: list[str] = []
        items_produced = 0
        failed_step = None
        error_message = None

        try:
            trends = self.run_trend_fetch()
            completed_steps.append("trend_fetch")
            items_produced += len(trends)
        except Exception as e:
            failed_step = "trend_fetch"
            error_message = str(e)
            self.state.status = PipelineStatus.PARTIAL
            self._save_state()

            return PipelineResult(
                status=PipelineStatus.PARTIAL,
                run_id=run_id,
                completed_steps=completed_steps,
                failed_step=failed_step,
                error_message=error_message,
                items_produced=items_produced,
                state=self.state,
            )

        try:
            video_paths = self.run_video_gen(trends=trends)
            completed_steps.append("video_gen")
            items_produced += len(video_paths)
        except Exception as e:
            failed_step = "video_gen"
            error_message = str(e)
            self.state.status = PipelineStatus.PARTIAL
            self._save_state()

            return PipelineResult(
                status=PipelineStatus.PARTIAL,
                run_id=run_id,
                completed_steps=completed_steps,
                failed_step=failed_step,
                error_message=error_message,
                items_produced=items_produced,
                state=self.state,
            )

        try:
            upload_results = self.run_upload(video_paths=video_paths)
            completed_steps.append("upload")
            items_produced += len(upload_results)
        except Exception as e:
            failed_step = "upload"
            error_message = str(e)
            self.state.status = PipelineStatus.PARTIAL
            self._save_state()

            return PipelineResult(
                status=PipelineStatus.PARTIAL,
                run_id=run_id,
                completed_steps=completed_steps,
                failed_step=failed_step,
                error_message=error_message,
                items_produced=items_produced,
                state=self.state,
            )

        try:
            analytics_result = self.run_analytics()
            completed_steps.append("analytics")
        except Exception as e:
            logger.warning(f"Analytics step failed: {e}")
            self.state.errors.append({
                "step": "analytics",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

        self.state.status = PipelineStatus.COMPLETED
        self._save_state()

        logger.info(
            f"Pipeline run {run_id} completed: "
            f"{len(completed_steps)} steps, {items_produced} items produced"
        )

        return PipelineResult(
            status=PipelineStatus.COMPLETED,
            run_id=run_id,
            completed_steps=completed_steps,
            failed_step=failed_step,
            error_message=error_message,
            items_produced=items_produced,
            state=self.state,
        )

    def get_status(self) -> dict[str, Any]:
        """Get current pipeline status.

        Returns:
            Dictionary with pipeline status information.
        """
        return {
            "run_id": self.state.run_id,
            "status": self.state.status.value,
            "last_run": self.state.last_run.isoformat() if self.state.last_run else None,
            "processed_trends": len(self.state.processed_trends),
            "generated_videos": len(self.state.generated_videos),
            "pending_videos": len(self.state.pending_videos),
            "uploaded_videos": len(self.state.uploaded_videos),
            "errors": len(self.state.errors),
            "steps": {
                name: step.status.value
                for name, step in self.state.steps.items()
            },
        }

    def reset_state(self) -> None:
        """Reset pipeline state to initial state."""
        self.state = PipelineState()
        self._save_state()
        logger.info("Pipeline state reset")

    def resume(self) -> PipelineResult:
        """Resume from last failure point.

    Continues execution from the step that failed.
    Already completed steps are skipped.

    Returns:
        PipelineResult with execution status.
    """
        if self.state.status not in (PipelineStatus.PARTIAL, PipelineStatus.FAILED):
            logger.info("No failed run to resume from")
            return PipelineResult(
                status=self.state.status,
                run_id=self.state.run_id,
                state=self.state,
            )

        logger.info(f"Resuming from run: {self.state.run_id}")

        failed_step_name = None
        for name, step in self.state.steps.items():
            if step.status == StepStatus.FAILED:
                failed_step_name = name
                break

        run_id = self.state.run_id
        completed_steps = [
            name for name, step in self.state.steps.items()
            if step.status == StepStatus.COMPLETED
        ]

        items_produced = len(self.state.generated_videos) + len(self.state.uploaded_videos)

        if failed_step_name == "trend_fetch" or not completed_steps:
            return self.run_daily()
        elif failed_step_name == "video_gen":
            try:
                video_paths = self.run_video_gen()
                completed_steps.append("video_gen")
                items_produced += len(video_paths)

                upload_results = self.run_upload(video_paths=video_paths)
                completed_steps.append("upload")
                items_produced += len(upload_results)

                self.run_analytics()
                completed_steps.append("analytics")

                self.state.status = PipelineStatus.COMPLETED
                self._save_state()

                return PipelineResult(
                    status=PipelineStatus.COMPLETED,
                    run_id=run_id,
                    completed_steps=completed_steps,
                    items_produced=items_produced,
                    state=self.state,
                )
            except Exception as e:
                return PipelineResult(
                    status=PipelineStatus.PARTIAL,
                    run_id=run_id,
                    completed_steps=completed_steps,
                    failed_step="video_gen",
                    error_message=str(e),
                    items_produced=items_produced,
                    state=self.state,
                )
        else:
            return self.run_daily()


__all__ = [
    "Pipeline",
    "PipelineConfig",
    "PipelineResult",
    "PipelineState",
    "PipelineStatus",
    "StepResult",
    "StepStatus",
]
