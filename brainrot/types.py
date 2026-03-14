"""Core type definitions and interfaces for the brainrot platform.

This module defines all core data models using Pydantic for validation,
and Protocol classes for interface contracts between components.

Data Models:
    - Trend: Trending content from external sources
    - Script: Generated script content
    - Video: Assembled video metadata
    - Channel: Platform channel configuration
    - Analytics: Video performance metrics
    - UploadResult: Upload operation result
    - ContentTemplate: Video styling configuration

Protocols:
    - TrendSource: Interface for trend fetching
    - ScriptGenerator: Interface for script generation
    - VideoAssembler: Interface for video assembly
    - Publisher: Interface for content publishing
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from pydantic import BaseModel, Field


# Type aliases for commonly used types
JSONDict = Dict[str, Any]
StringList = List[str]
OptionalStr = Optional[str]
OptionalPath = Optional[Path]


# ============================================================================
# DATA MODELS
# ============================================================================


class Trend(BaseModel):
    """Trending content from external sources (Reddit, YouTube, etc.).

    Represents a piece of trending content that has been fetched from
    an external source and can be used for script generation.

    Attributes:
        id: Unique identifier for the trend.
        title: Title or headline of the trending content.
        source: Source platform (e.g., 'reddit', 'youtube', 'tiktok').
        url: Original URL of the content.
        score: Popularity score (upvotes, views, etc.).
        fetched_at: Timestamp when the trend was fetched.
        keywords: Extracted keywords for the content.
    """

    id: str = Field(..., description="Unique identifier for the trend")
    title: str = Field(..., description="Title or headline of the trending content")
    source: str = Field(..., description="Source platform (e.g., 'reddit', 'youtube')")
    url: str = Field(..., description="Original URL of the content")
    score: int = Field(default=0, description="Popularity score (upvotes, views, etc.)")
    fetched_at: datetime = Field(
        default_factory=datetime.utcnow, description="Timestamp when fetched"
    )
    keywords: StringList = Field(
        default_factory=list, description="Extracted keywords for the content"
    )


class Script(BaseModel):
    """Generated script content for video production.

    Represents a script that has been generated from a trend,
    ready to be converted into a video.

    Attributes:
        id: Unique identifier for the script.
        trend_id: ID of the source trend.
        text: Full script text content.
        hook: Opening hook/catchphrase for engagement.
        word_count: Number of words in the script.
        template: Template name used for generation.
        created_at: Timestamp when script was created.
    """

    id: str = Field(..., description="Unique identifier for the script")
    trend_id: str = Field(..., description="ID of the source trend")
    text: str = Field(..., description="Full script text content")
    hook: str = Field(..., description="Opening hook/catchphrase for engagement")
    word_count: int = Field(default=0, description="Number of words in the script")
    template: str = Field(default="default", description="Template name used")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Timestamp when created"
    )


class Video(BaseModel):
    """Assembled video metadata.

    Represents a video that has been assembled from a script,
    ready for publishing to platforms.

    Attributes:
        id: Unique identifier for the video.
        script_id: ID of the source script.
        path: File path to the video file.
        duration: Video duration in seconds.
        thumbnail_path: Path to the thumbnail image.
        created_at: Timestamp when video was created.
    """

    id: str = Field(..., description="Unique identifier for the video")
    script_id: str = Field(..., description="ID of the source script")
    path: Path = Field(..., description="File path to the video file")
    duration: float = Field(..., description="Video duration in seconds")
    thumbnail_path: OptionalPath = Field(
        default=None, description="Path to the thumbnail image"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Timestamp when created"
    )


class Channel(BaseModel):
    """Platform channel configuration.

    Represents a publishing channel on a platform (YouTube, TikTok, etc.)
    with its associated credentials and settings.

    Attributes:
        id: Unique identifier for the channel.
        name: Display name of the channel.
        platform: Platform name (e.g., 'youtube', 'tiktok').
        credentials_path: Path to credentials file.
        is_active: Whether the channel is active for publishing.
    """

    id: str = Field(..., description="Unique identifier for the channel")
    name: str = Field(..., description="Display name of the channel")
    platform: str = Field(..., description="Platform name (e.g., 'youtube', 'tiktok')")
    credentials_path: Path = Field(..., description="Path to credentials file")
    is_active: bool = Field(default=True, description="Whether channel is active")


class Analytics(BaseModel):
    """Video performance metrics.

    Represents analytics data for a published video,
    including views, engagement, and retention metrics.

    Attributes:
        video_id: ID of the video being tracked.
        views: Total view count.
        likes: Total like count.
        comments: Total comment count.
        avg_view_duration: Average view duration in seconds.
        fetched_at: Timestamp when analytics were fetched.
    """

    video_id: str = Field(..., description="ID of the video being tracked")
    views: int = Field(default=0, description="Total view count")
    likes: int = Field(default=0, description="Total like count")
    comments: int = Field(default=0, description="Total comment count")
    avg_view_duration: float = Field(
        default=0.0, description="Average view duration in seconds"
    )
    fetched_at: datetime = Field(
        default_factory=datetime.utcnow, description="Timestamp when fetched"
    )


class UploadResult(BaseModel):
    """Result of a content upload operation.

    Represents the outcome of attempting to publish content
    to a platform.

    Attributes:
        video_id: ID of the video that was uploaded.
        platform: Target platform name.
        external_id: Platform's ID for the uploaded content.
        status: Upload status ('success', 'failed', 'pending').
        uploaded_at: Timestamp when upload completed.
        error: Error message if upload failed.
    """

    video_id: str = Field(..., description="ID of the video uploaded")
    platform: str = Field(..., description="Target platform name")
    external_id: OptionalStr = Field(
        default=None, description="Platform's ID for the content"
    )
    status: str = Field(
        default="pending", description="Upload status ('success', 'failed', 'pending')"
    )
    uploaded_at: Optional[datetime] = Field(
        default=None, description="Timestamp when upload completed"
    )
    error: OptionalStr = Field(default=None, description="Error message if failed")


class ContentTemplate(BaseModel):
    """Video styling configuration template.

    Represents a template for styling video content,
    including visual and textual styling options.

    Attributes:
        name: Template name identifier.
        style_config: Dictionary of style configuration options.
        caption_style: Style name for captions.
        font_family: Font family for text elements.
        colors: Color configuration dictionary.
    """

    name: str = Field(..., description="Template name identifier")
    style_config: JSONDict = Field(
        default_factory=dict, description="Style configuration options"
    )
    caption_style: str = Field(default="default", description="Caption style name")
    font_family: str = Field(default="Arial", description="Font family for text")
    colors: JSONDict = Field(
        default_factory=lambda: {
            "primary": "#FFFFFF",
            "secondary": "#000000",
            "accent": "#FF0000",
        },
        description="Color configuration dictionary",
    )


# ============================================================================
# PROTOCOL CLASSES (Interfaces)
# ============================================================================


@runtime_checkable
class TrendSource(Protocol):
    """Protocol for trend fetching components.

    Defines the interface for components that fetch trending content
    from external sources like Reddit or YouTube.
    """

    def fetch(self, limit: int = 10, **kwargs: Any) -> List[Trend]:
        """Fetch trending content from the source.

        Args:
            limit: Maximum number of trends to fetch.
            **kwargs: Additional source-specific parameters.

        Returns:
            List of Trend objects.
        """
        ...


@runtime_checkable
class ScriptGenerator(Protocol):
    """Protocol for script generation components.

    Defines the interface for components that generate scripts
    from trending content using AI/LLM or templates.
    """

    def generate(self, trend: Trend, template: Optional[ContentTemplate] = None) -> Script:
        """Generate a script from a trend.

        Args:
            trend: The source trend to generate from.
            template: Optional template for styling.

        Returns:
            Generated Script object.
        """
        ...


@runtime_checkable
class VideoAssembler(Protocol):
    """Protocol for video assembly components.

    Defines the interface for components that assemble videos
    from scripts, including audio, visuals, and effects.
    """

    def assemble(self, script: Script, template: Optional[ContentTemplate] = None) -> Video:
        """Assemble a video from a script.

        Args:
            script: The script to assemble into a video.
            template: Optional template for styling.

        Returns:
            Assembled Video object.
        """
        ...


@runtime_checkable
class Publisher(Protocol):
    """Protocol for content publishing components.

    Defines the interface for components that publish videos
    to platforms like YouTube or TikTok.
    """

    def publish(self, video: Video, channel: Channel) -> UploadResult:
        """Publish a video to a channel.

        Args:
            video: The video to publish.
            channel: The channel to publish to.

        Returns:
            UploadResult with publication status.
        """
        ...


# ============================================================================
# MODULE EXPORTS
# ============================================================================

__all__ = [
    # Type aliases
    "JSONDict",
    "StringList",
    "OptionalStr",
    "OptionalPath",
    # Data models
    "Trend",
    "Script",
    "Video",
    "Channel",
    "Analytics",
    "UploadResult",
    "ContentTemplate",
    # Protocols
    "TrendSource",
    "ScriptGenerator",
    "VideoAssembler",
    "Publisher",
]
