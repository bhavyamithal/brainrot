"""Dashboard package for visualizing analytics data.

This module provides a Streamlit-based web dashboard for displaying
channel and video performance metrics.

Usage:
    streamlit run brainrot/dashboard/app.py
"""

from __future__ import annotations

__all__ = [
    "run_dashboard",
]


def run_dashboard() -> None:
    """Entry point to run the Streamlit dashboard.

    This function is provided for programmatic access to start
    the dashboard. Typically, you would run the dashboard via:
        streamlit run brainrot/dashboard/app.py
    """
    import subprocess
    import sys
    from pathlib import Path

    app_path = Path(__file__).parent / "app.py"
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", str(app_path)],
        check=False,
    )
