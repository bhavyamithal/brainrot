"""Scheduler implementation using APScheduler for task orchestration."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)


@dataclass
class ScheduledJob:
    """Data class representing a scheduled job's state."""

    name: str
    func: Callable[..., Any]
    trigger_type: str
    trigger_config: dict[str, Any]
    last_run: datetime | None = None
    next_run: datetime | None = None
    is_running: bool = False


@dataclass
class DefaultJobConfig:
    """Configuration for default scheduled jobs."""

    trend_fetch_hours: int = 4
    video_generation_hours: int = 1
    upload_times: list[str] = field(default_factory=lambda: ["09:00", "12:00", "18:00"])


class Scheduler:
    """Orchestrates all timed tasks with timezone-aware scheduling.

    Supports three trigger types:
    - interval: Run at fixed intervals (e.g., every 4 hours)
    - cron: Run at specific times (e.g., 9am daily)
    - date: Run once at a specific datetime
    """

    def __init__(self, timezone: str = "UTC", default_config: DefaultJobConfig | None = None):
        self._timezone = ZoneInfo(timezone)
        self._scheduler = BackgroundScheduler(timezone=self._timezone)
        self._jobs: dict[str, ScheduledJob] = {}
        self._default_config = default_config or DefaultJobConfig()
        self._is_running = False

    def add_job(
        self,
        name: str,
        func: Callable[..., Any],
        trigger: str = "interval",
        **kwargs: Any,
    ) -> None:
        """Add a job to the scheduler.

        Args:
            name: Unique identifier for the job.
            func: Callable to execute when the job runs.
            trigger: Trigger type - "interval", "cron", or "date".
            **kwargs: Trigger-specific configuration:
                - interval: hours, minutes, seconds
                - cron: hour, minute, day_of_week, etc.
                - date: run_date (datetime)

        Raises:
            ValueError: If trigger type is invalid or job name already exists.
        """
        if name in self._jobs:
            raise ValueError(f"Job '{name}' already exists")

        trigger_type = trigger.lower()
        if trigger_type not in ("interval", "cron", "date"):
            raise ValueError(f"Invalid trigger type: {trigger}. Must be 'interval', 'cron', or 'date'")

        job = ScheduledJob(
            name=name,
            func=func,
            trigger_type=trigger_type,
            trigger_config=kwargs,
        )
        self._jobs[name] = job

        ap_trigger = self._build_trigger(trigger_type, kwargs)

        self._scheduler.add_job(
            func=self._wrap_job(name, func),
            trigger=ap_trigger,
            id=name,
            name=name,
        )

        logger.info(f"Added job '{name}' with trigger '{trigger_type}': {kwargs}")

    def remove_job(self, name: str) -> None:
        """Remove a job from the scheduler.

        Args:
            name: Unique identifier of the job to remove.

        Raises:
            KeyError: If job does not exist.
        """
        if name not in self._jobs:
            raise KeyError(f"Job '{name}' not found")

        self._scheduler.remove_job(name)
        del self._jobs[name]
        logger.info(f"Removed job '{name}'")

    def start(self) -> None:
        """Start the scheduler.

        Does nothing if already running.
        """
        if self._is_running:
            logger.warning("Scheduler is already running")
            return

        self._scheduler.start()
        self._is_running = True
        self._update_job_times()
        logger.info(f"Scheduler started with timezone: {self._timezone}")

    def stop(self, wait: bool = True) -> None:
        """Stop the scheduler gracefully.

        Args:
            wait: If True, wait for running jobs to complete before stopping.
        """
        if not self._is_running:
            logger.warning("Scheduler is not running")
            return

        self._scheduler.shutdown(wait=wait)
        self._is_running = False
        logger.info(f"Scheduler stopped (wait={wait})")

    def trigger_now(self, name: str) -> Any:
        """Manually trigger a job immediately for testing.

        Args:
            name: Unique identifier of the job to trigger.

        Returns:
            The result of the job function.

        Raises:
            KeyError: If job does not exist.
        """
        if name not in self._jobs:
            raise KeyError(f"Job '{name}' not found")

        job = self._jobs[name]
        logger.info(f"Manually triggering job '{name}'")

        job.is_running = True
        try:
            result = job.func()
            job.last_run = datetime.now(self._timezone)
            return result
        finally:
            job.is_running = False
            self._update_job_times()

    def get_jobs(self) -> list[ScheduledJob]:
        """Get list of all scheduled jobs with their current state."""
        self._update_job_times()
        return list(self._jobs.values())

    def get_next_run(self, name: str) -> datetime | None:
        job_state = self._scheduler.get_job(name)
        if job_state:
            return getattr(job_state, "next_run_time", None)
        return None

    def setup_default_jobs(
        self,
        trend_fetch_func: Callable[..., Any] | None = None,
        video_generation_func: Callable[..., Any] | None = None,
        upload_func: Callable[..., Any] | None = None,
    ) -> None:
        """Set up default scheduled jobs.

        Args:
            trend_fetch_func: Function to fetch trends (every 4 hours).
            video_generation_func: Function to generate videos (every hour).
            upload_func: Function to upload content (at optimal times).
        """
        config = self._default_config

        if trend_fetch_func:
            self.add_job(
                name="trend_fetch",
                func=trend_fetch_func,
                trigger="interval",
                hours=config.trend_fetch_hours,
            )

        if video_generation_func:
            self.add_job(
                name="video_generation",
                func=video_generation_func,
                trigger="interval",
                hours=config.video_generation_hours,
            )

        if upload_func:
            for i, time_str in enumerate(config.upload_times):
                hour, minute = time_str.split(":")
                self.add_job(
                    name=f"upload_{i + 1}",
                    func=upload_func,
                    trigger="cron",
                    hour=int(hour),
                    minute=int(minute),
                )

        logger.info(f"Default jobs configured: trend_fetch, video_generation, {len(config.upload_times)} upload slots")

    def _build_trigger(self, trigger_type: str, config: dict[str, Any]) -> Any:
        """Build an APScheduler trigger from configuration."""
        if trigger_type == "interval":
            return IntervalTrigger(**config, timezone=self._timezone)
        elif trigger_type == "cron":
            return CronTrigger(**config, timezone=self._timezone)
        elif trigger_type == "date":
            run_date = config.get("run_date")
            if run_date:
                from apscheduler.triggers.date import DateTrigger

                return DateTrigger(run_date=run_date, timezone=self._timezone)
            raise ValueError("date trigger requires 'run_date' parameter")
        raise ValueError(f"Unknown trigger type: {trigger_type}")

    def _wrap_job(self, name: str, func: Callable[..., Any]) -> Callable[..., Any]:
        """Wrap a job function with logging and state tracking."""

        def wrapped() -> Any:
            job = self._jobs.get(name)
            if job:
                job.is_running = True
                logger.info(f"Starting job '{name}'")

            try:
                result = func()
                if job:
                    job.last_run = datetime.now(self._timezone)
                logger.info(f"Completed job '{name}'")
                return result
            except Exception as e:
                logger.error(f"Job '{name}' failed: {e}")
                raise
            finally:
                if job:
                    job.is_running = False
                    self._update_job_times()

        return wrapped

    def _update_job_times(self) -> None:
        for name, job in self._jobs.items():
            aps_job = self._scheduler.get_job(name)
            if aps_job and hasattr(aps_job, "next_run_time"):
                job.next_run = aps_job.next_run_time

    def __enter__(self) -> "Scheduler":
        """Context manager entry - starts the scheduler."""
        self.start()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit - stops the scheduler gracefully."""
        self.stop(wait=True)
