"""Scheduling system for timed task execution.

This module provides cron-based scheduling for:
- Trend fetching (every 4 hours)
- Video generation (based on queue)
- Upload posting (optimal times per platform)
"""

from __future__ import annotations

from brainrot.scheduler.scheduler import ScheduledJob, Scheduler

__all__ = [
    "Scheduler",
    "ScheduledJob",
]
