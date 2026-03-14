"""Video assembly package for FFmpeg-based video generation.

This package provides tools for assembling videos from scripts,
including background footage, captions, and audio tracks.

Classes:
    - CaptionStyle: Configuration for caption appearance
    - CaptionGenerator: Generates ASS format subtitles
    - ConcatDemuxer: Handles FFmpeg concat demuxer files
    - VideoBuilder: Main video assembly class
"""

from brainrot.video.assembly import ConcatDemuxer, VideoBuilder
from brainrot.video.captions import CaptionGenerator, CaptionStyle

__all__ = [
    "CaptionStyle",
    "CaptionGenerator",
    "ConcatDemuxer",
    "VideoBuilder",
]
