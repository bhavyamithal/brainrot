"""Command-line interface for the brainrot platform.

Provides commands for running the content pipeline, managing uploads,
viewing trends, and launching the analytics dashboard.

Usage:
    brainrot run [--dry-run] [--verbose]
    brainrot trends [--limit N]
    brainrot generate [--trend-id ID]
    brainrot upload [--max N]
    brainrot status
    brainrot dashboard
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

import click

# Configure logging for CLI
logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    """Configure logging level based on verbosity.

    Args:
        verbose: If True, set DEBUG level; otherwise INFO.
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def print_json(data: dict[str, Any] | list[Any]) -> None:
    """Pretty print JSON data.

    Args:
        data: Data to print as JSON.
    """
    click.echo(json.dumps(data, indent=2, default=str))


def print_error(message: str) -> None:
    """Print error message in red.

    Args:
        message: Error message to print.
    """
    click.secho(f"Error: {message}", fg="red", err=True)


def print_success(message: str) -> None:
    """Print success message in green.

    Args:
        message: Success message to print.
    """
    click.secho(f"✓ {message}", fg="green")


def print_info(message: str) -> None:
    """Print info message in cyan.

    Args:
        message: Info message to print.
    """
    click.secho(f"ℹ {message}", fg="cyan")


def print_warning(message: str) -> None:
    """Print warning message in yellow.

    Args:
        message: Warning message to print.
    """
    click.secho(f"⚠ {message}", fg="yellow")


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output.")
@click.pass_context
def cli(ctx: click.Context, verbose: bool) -> None:
    """Brainrot: AI-powered viral content generation platform.

    Generate engaging short-form video content from trending topics
    using AI-powered script generation, text-to-speech, and video assembly.

    \b
    Commands:
        run        Run the full content pipeline
        trends     Fetch and display current trends
        generate   Generate a single video from a trend
        upload     Process the upload queue
        status     Show current pipeline state
        dashboard  Launch the analytics dashboard

    Use 'brainrot <command> --help' for command-specific options.
    """
    ctx.ensure_object(dict)
    ctx.obj["VERBOSE"] = verbose
    setup_logging(verbose)


@cli.command()
@click.option("--dry-run", is_flag=True, help="Run without uploading videos.")
@click.option("--max-trends", type=int, default=10, help="Maximum trends to fetch.")
@click.option("--max-videos", type=int, default=3, help="Maximum videos to generate.")
@click.option("--max-uploads", type=int, default=5, help="Maximum uploads per run.")
@click.pass_context
def run(
    ctx: click.Context,
    dry_run: bool,
    max_trends: int,
    max_videos: int,
    max_uploads: int,
) -> None:
    """Run the full content pipeline.

    Executes the complete workflow:
    1. Fetch trending topics from configured sources
    2. Generate scripts from trending content
    3. Synthesize audio narration
    4. Assemble videos with templates
    5. Upload to YouTube (unless --dry-run)

    \b
    Examples:
        brainrot run
        brainrot run --dry-run
        brainrot run --max-videos 5 --verbose
    """
    verbose = ctx.obj.get("VERBOSE", False)

    if dry_run:
        print_info("Running in dry-run mode (no uploads)")

    try:
        from brainrot.pipeline import Pipeline, PipelineConfig

        config = PipelineConfig(
            max_trends_per_run=max_trends,
            max_videos_per_run=max_videos,
            max_uploads_per_run=max_uploads,
        )

        pipeline = Pipeline(config=config)

        print_info(f"Starting pipeline run (max_trends={max_trends}, max_videos={max_videos})")

        if dry_run:
            # Run fetch and video gen, skip upload
            trends = pipeline.run_trend_fetch(limit=max_trends)
            print_success(f"Fetched {len(trends)} trends")

            if trends:
                videos = pipeline.run_video_gen(trends=trends, limit=max_videos)
                print_success(f"Generated {len(videos)} videos")

            print_info("Dry-run complete: skipped upload step")
            return

        result = pipeline.run_daily()

        if result.status.value == "completed":
            print_success(f"Pipeline completed: {result.items_produced} items produced")
            print_info(f"Steps completed: {', '.join(result.completed_steps)}")
        else:
            print_warning(f"Pipeline finished with status: {result.status.value}")
            if result.error_message:
                print_error(result.error_message)

        if verbose:
            click.echo("\nPipeline State:")
            print_json(pipeline.get_status())

    except ImportError as e:
        print_error(f"Failed to import required module: {e}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Pipeline failed: {e}")
        if verbose:
            logger.exception("Pipeline error")
        sys.exit(1)


@cli.command()
@click.option("--limit", "-l", type=int, default=10, help="Number of trends to show.")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON.")
@click.pass_context
def trends(ctx: click.Context, limit: int, json_output: bool) -> None:
    """Fetch and display current trending topics.

    Aggregates trends from configured sources (Reddit, Google Trends)
    and displays them with scores and sources.

    \b
    Examples:
        brainrot trends
        brainrot trends --limit 20
        brainrot trends --json-output
    """
    verbose = ctx.obj.get("VERBOSE", False)

    try:
        from brainrot.trends import GoogleTrendsSource, RedditTrendSource, TrendAggregator

        print_info(f"Fetching trends from all sources (limit={limit})...")

        sources = [
            RedditTrendSource(),
            GoogleTrendsSource(),
        ]
        aggregator = TrendAggregator(sources=sources)

        fetched_trends = aggregator.get_trends(limit=limit, exclude_processed=False)

        if not fetched_trends:
            print_warning("No trends found")
            return

        if json_output:
            output = [
                {
                    "id": t.id,
                    "title": t.title,
                    "source": t.source,
                    "score": t.score,
                    "url": t.url,
                    "keywords": t.keywords,
                }
                for t in fetched_trends
            ]
            print_json(output)
            return

        click.echo(f"\n📊 Found {len(fetched_trends)} trending topics:\n")

        for i, trend in enumerate(fetched_trends, 1):
            score_str = click.style(f"[{trend.score}]", fg="yellow")
            source_str = click.style(f"({trend.source})", fg="cyan")
            click.echo(f"  {i:2d}. {score_str} {source_str} {trend.title[:70]}")

            if verbose:
                click.secho(f"      ID: {trend.id}", dim=True)
                if trend.keywords:
                    click.secho(f"      Keywords: {', '.join(trend.keywords[:5])}", dim=True)

        click.echo()

    except ImportError as e:
        print_error(f"Failed to import required module: {e}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Failed to fetch trends: {e}")
        if verbose:
            logger.exception("Trend fetch error")
        sys.exit(1)


@cli.command()
@click.option("--trend-id", "-t", help="Specific trend ID to generate from.")
@click.option("--template", "-T", default="tech_news", help="Video template to use.")
@click.option("--voice", "-V", default="default", help="Voice profile for TTS.")
@click.option("--output", "-o", type=click.Path(), help="Output directory for video.")
@click.pass_context
def generate(
    ctx: click.Context,
    trend_id: str | None,
    template: str,
    voice: str,
    output: str | None,
) -> None:
    """Generate a single video from a trend.

    Executes the video generation pipeline for a single trend:
    1. Fetch trend (or use latest if no ID specified)
    2. Generate script from trend
    3. Synthesize audio narration
    4. Assemble video with specified template

    \b
    Examples:
        brainrot generate
        brainrot generate --trend-id reddit-abc123
        brainrot generate --template explainer --voice energetic
    """
    verbose = ctx.obj.get("VERBOSE", False)

    try:
        from brainrot.audio import TTSClient
        from brainrot.content import ScriptGenerator
        from brainrot.templates import TemplateRenderer
        from brainrot.trends import GoogleTrendsSource, RedditTrendSource, TrendAggregator
        from brainrot.video import VideoBuilder

        print_info("Fetching trend...")

        sources = [
            RedditTrendSource(),
            GoogleTrendsSource(),
        ]
        aggregator = TrendAggregator(sources=sources)

        trends_list = aggregator.get_trends(limit=1, exclude_processed=False)

        if not trends_list:
            print_error("No trends available")
            sys.exit(1)

        trend = trends_list[0]

        if trend_id:
            # Find specific trend
            all_trends = aggregator.get_trends(limit=50, exclude_processed=False)
            for t in all_trends:
                if t.id == trend_id:
                    trend = t
                    break
            else:
                print_error(f"Trend not found: {trend_id}")
                sys.exit(1)

        print_info(f"Using trend: {trend.title[:60]}...")

        # Generate script
        print_info("Generating script...")
        script_gen = ScriptGenerator()
        script = script_gen.generate(trend=trend, template=template)
        print_success(f"Generated script ({script.word_count} words)")

        if verbose:
            click.secho(f"\nScript preview:\n{script.text[:200]}...\n", dim=True)

        # Synthesize audio
        print_info("Synthesizing audio...")
        tts = TTSClient()
        audio_path = tts.synthesize(text=script.text, voice=voice)
        print_success(f"Audio saved: {audio_path}")

        # Generate video
        print_info("Assembling video...")
        output_dir = Path(output) if output else None
        builder = VideoBuilder(output_dir=output_dir)
        renderer = TemplateRenderer(template)

        duration = builder._get_audio_duration(audio_path)
        bg_color = renderer.config.background.color
        builder.add_background(bg_color, duration)

        renderer.apply_to_builder(builder, script, audio_path, duration)

        video_path = builder.render()
        print_success(f"Video generated: {video_path}")

        # Mark trend as processed
        aggregator.mark_trends_processed([trend])

        click.echo(f"\n🎬 Video created successfully!")
        click.echo(f"   Path: {video_path}")
        click.echo(f"   Template: {template}")
        click.echo(f"   Voice: {voice}")

    except ImportError as e:
        print_error(f"Failed to import required module: {e}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Video generation failed: {e}")
        if verbose:
            logger.exception("Generation error")
        sys.exit(1)


@cli.command()
@click.option("--max", "-m", "max_uploads", type=int, default=5, help="Maximum uploads to process.")
@click.option("--human-review", is_flag=True, help="Enable human review checkpoint.")
@click.option("--dry-run", is_flag=True, help="Show what would be uploaded without uploading.")
@click.pass_context
def upload(
    ctx: click.Context,
    max_uploads: int,
    human_review: bool,
    dry_run: bool,
) -> None:
    """Process the upload queue.

    Uploads queued videos to YouTube, respecting daily limits
    and quota constraints.

    \b
    Examples:
        brainrot upload
        brainrot upload --max 3
        brainrot upload --human-review
        brainrot upload --dry-run
    """
    verbose = ctx.obj.get("VERBOSE", False)

    if dry_run:
        print_info("Dry-run mode: showing queue status only")

    try:
        from brainrot.pipeline.uploader import UploadOrchestrator

        orchestrator = UploadOrchestrator()

        # Show current queue status
        status = orchestrator.get_queue_status()
        print_info(f"Queue status: {status['pending']} pending, {status['failed']} failed")

        if dry_run:
            click.echo("\nQueue Status:")
            print_json(status)
            return

        if status["pending"] == 0 and status["failed"] == 0:
            print_warning("No videos in queue")
            return

        print_info(f"Processing up to {max_uploads} uploads...")

        results = orchestrator.process_queue(
            human_review=human_review,
            max_uploads=max_uploads,
        )

        if not results:
            print_warning("No videos uploaded (check quota or daily limits)")
            return

        click.echo(f"\n📤 Upload Results:\n")

        for result in results:
            if result.status == "success":
                print_success(f"{result.video_id} -> {result.external_id}")
            else:
                print_error(f"{result.video_id}: {result.error}")

        # Show updated status
        final_status = orchestrator.get_queue_status()
        print_info(f"Remaining quota: {final_status['remaining_quota']} units")
        print_info(f"Uploads remaining today: {final_status['uploads_remaining']}")

    except ImportError as e:
        print_error(f"Failed to import required module: {e}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Upload failed: {e}")
        if verbose:
            logger.exception("Upload error")
        sys.exit(1)


@cli.command()
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON.")
@click.pass_context
def status(ctx: click.Context, json_output: bool) -> None:
    """Show current pipeline state.

    Displays information about:
    - Last run time and status
    - Number of processed trends
    - Generated videos
    - Pending uploads
    - Step completion status

    \b
    Examples:
        brainrot status
        brainrot status --json-output
    """
    verbose = ctx.obj.get("VERBOSE", False)

    try:
        from brainrot.pipeline import Pipeline

        pipeline = Pipeline()
        state = pipeline.get_status()

        if json_output:
            print_json(state)
            return

        # Format status display
        click.echo("\n📈 Pipeline Status\n")
        click.echo(f"  Run ID:        {state.get('run_id', 'N/A')}")
        click.echo(f"  Status:        ", nl=False)

        status_val = state.get("status", "pending")
        if status_val == "completed":
            click.secho(status_val, fg="green")
        elif status_val in ("partial", "failed"):
            click.secho(status_val, fg="red")
        else:
            click.secho(status_val, fg="yellow")

        last_run = state.get("last_run")
        if last_run:
            click.echo(f"  Last Run:      {last_run}")

        click.echo("\n  📊 Statistics\n")
        click.echo(f"    Trends Processed:  {state.get('processed_trends', 0)}")
        click.echo(f"    Videos Generated:  {state.get('generated_videos', 0)}")
        click.echo(f"    Pending Uploads:   {state.get('pending_videos', 0)}")
        click.echo(f"    Videos Uploaded:   {state.get('uploaded_videos', 0)}")
        click.echo(f"    Errors:            {state.get('errors', 0)}")

        steps = state.get("steps", {})
        if steps:
            click.echo("\n  🔄 Step Status\n")
            for step_name, step_status in steps.items():
                if step_status == "completed":
                    icon = click.style("✓", fg="green")
                elif step_status == "failed":
                    icon = click.style("✗", fg="red")
                elif step_status == "running":
                    icon = click.style("⟳", fg="yellow")
                else:
                    icon = click.style("○", dim=True)
                click.echo(f"    {icon} {step_name}: {step_status}")

        click.echo()

    except ImportError as e:
        print_error(f"Failed to import required module: {e}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Failed to get status: {e}")
        if verbose:
            logger.exception("Status error")
        sys.exit(1)


@cli.command()
@click.option("--port", "-p", type=int, default=8501, help="Dashboard port.")
@click.option("--no-browser", is_flag=True, help="Don't open browser automatically.")
@click.pass_context
def dashboard(ctx: click.Context, port: int, no_browser: bool) -> None:
    """Launch the analytics dashboard.

    Opens a Streamlit-based web interface for viewing
    channel and video performance metrics.

    \b
    Examples:
        brainrot dashboard
        brainrot dashboard --port 8080
        brainrot dashboard --no-browser
    """
    verbose = ctx.obj.get("VERBOSE", False)

    try:
        import subprocess
        import sys

        from brainrot.dashboard import run_dashboard

        print_info(f"Launching dashboard on port {port}...")

        app_path = Path(__file__).parent / "dashboard" / "app.py"

        cmd = [sys.executable, "-m", "streamlit", "run", str(app_path), "--server.port", str(port)]

        if no_browser:
            cmd.append("--server.headless=true")

        if verbose:
            click.echo(f"Running: {' '.join(cmd)}")

        subprocess.run(cmd, check=False)

    except ImportError as e:
        print_error(f"Failed to import required module: {e}")
        print_info("Make sure streamlit is installed: pip install streamlit")
        sys.exit(1)
    except Exception as e:
        print_error(f"Failed to launch dashboard: {e}")
        if verbose:
            logger.exception("Dashboard error")
        sys.exit(1)


def main() -> None:
    """Entry point for the brainrot CLI."""
    cli()


if __name__ == "__main__":
    main()
