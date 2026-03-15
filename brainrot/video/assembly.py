"""FFmpeg-based video assembly with template-driven generation."""

from __future__ import annotations

import logging
import re
import shutil
import subprocess
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from brainrot.exceptions import VideoGenerationError
from brainrot.video.captions import CaptionGenerator, CaptionStyle

logger = logging.getLogger(__name__)

__all__ = ["VideoBuilder", "ConcatDemuxer", "BackgroundConfig", "AudioConfig"]


@dataclass
class BackgroundConfig:
    source: str
    duration: float
    is_color: bool = False


@dataclass
class AudioConfig:
    main_audio: Path
    music: Path | None = None
    music_volume: float = 0.3


class ConcatDemuxer:
    """Handles FFmpeg concat demuxer file generation.

    CRITICAL: FFmpeg concat demuxer has a known bug where the duration
    of the last entry is not honored. This class works around it by
    repeating the last entry.
    """

    def __init__(self, output_dir: Path | None = None) -> None:
        self.output_dir = output_dir or Path(tempfile.mkdtemp())
        self.entries: list[tuple[str, float]] = []
        self._concat_file: Path | None = None

    def add_entry(self, source: str, duration: float) -> None:
        self.entries.append((source, duration))

    def add_color(self, color: str, duration: float) -> None:
        self.add_entry(f"color=c={color}:s=1080x1920:d={duration}", duration)

    def build(self) -> Path:
        if not self.entries:
            raise VideoGenerationError("No entries added to concat demuxer")

        self._concat_file = self.output_dir / f"concat_{uuid.uuid4().hex[:8]}.txt"

        lines = []
        for source, duration in self.entries:
            lines.append(f"file '{source}'")
            lines.append(f"duration {duration}")

        last_source, _ = self.entries[-1]
        lines.append(f"file '{last_source}'")

        self._concat_file.write_text("\n".join(lines))
        logger.debug(f"Created concat file: {self._concat_file}")
        return self._concat_file

    def cleanup(self) -> None:
        if self._concat_file and self._concat_file.exists():
            self._concat_file.unlink()
            self._concat_file = None


class VideoBuilder:
    """Main video assembly class using FFmpeg.

    Orchestrates the video creation process including:
    - Background footage or solid colors
    - Caption/subtitle overlay
    - Audio track mixing (TTS + optional music)
    - Output rendering with progress tracking
    """

    def __init__(
        self,
        output_dir: Path | None = None,
        resolution: tuple[int, int] = (1080, 1920),
    ) -> None:
        self.output_dir = Path(output_dir) if output_dir else Path.cwd()
        self.resolution = resolution
        self._background: BackgroundConfig | None = None
        self._caption_text: str | None = None
        self._caption_style: CaptionStyle | None = None
        self._audio: AudioConfig | None = None
        self._duration: float = 0.0
        self._temp_dir: Path | None = None

    def add_background(
        self,
        source: Path | str,
        duration: float,
    ) -> None:
        source_str = str(source)
        is_color = source_str.startswith("#") or source_str.startswith("color=")

        if is_color and source_str.startswith("#"):
            source_str = source_str[1:]

        self._background = BackgroundConfig(
            source=source_str,
            duration=duration,
            is_color=is_color,
        )
        self._duration = duration
        logger.debug(f"Added background: {source_str} ({duration}s)")

    def add_captions(
        self,
        text: str,
        style: CaptionStyle | None = None,
    ) -> None:
        self._caption_text = text
        self._caption_style = style
        logger.debug(f"Added captions: {len(text)} characters")

    def add_audio(
        self,
        audio_path: Path,
        music_path: Path | None = None,
        music_volume: float = 0.3,
    ) -> None:
        self._audio = AudioConfig(
            main_audio=Path(audio_path),
            music=Path(music_path) if music_path else None,
            music_volume=music_volume,
        )

        if self._duration == 0.0:
            audio_duration = self._get_audio_duration(audio_path)
            self._duration = audio_duration
            if self._background:
                self._background.duration = audio_duration

        logger.debug(f"Added audio: {audio_path}")

    def render(
        self,
        output_path: Path | None = None,
        progress_callback: callable | None = None,
    ) -> Path:
        self._validate_configuration()

        output_path = self._resolve_output_path(output_path)
        self._temp_dir = Path(tempfile.mkdtemp())

        try:
            caption_file = None
            if self._caption_text:
                caption_file = self._generate_captions()

            cmd = self._build_ffmpeg_command(caption_file)
            self._execute_ffmpeg(cmd, progress_callback)

            logger.info(f"Video rendered successfully: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Video rendering failed: {e}")
            raise VideoGenerationError(
                f"Failed to render video: {e}",
                {"output_path": str(output_path)},
            ) from e
        finally:
            self._cleanup_temp_files()

    def _validate_configuration(self) -> None:
        if not self._background:
            raise VideoGenerationError("No background configured")
        if not self._audio:
            raise VideoGenerationError("No audio configured")

    def _resolve_output_path(self, output_path: Path | None) -> Path:
        if output_path:
            return Path(output_path)
        filename = f"video_{uuid.uuid4().hex[:8]}.mp4"
        return self.output_dir / filename

    def _generate_captions(self) -> Path:
        generator = CaptionGenerator(self._caption_style)
        caption_file = self._temp_dir / "captions.ass"
        generator.generate_ass_to_file(
            text=self._caption_text,
            duration=self._duration,
            output_path=caption_file,
        )
        return caption_file

    def _build_ffmpeg_command(
        self,
        caption_file: Path | None,
    ) -> list[str]:
        cmd = ["ffmpeg", "-y"]
        width, height = self.resolution

        if self._background.is_color:
            cmd.extend([
                "-f", "lavfi",
                "-i", f"color=c={self._background.source}:s={width}x{height}:d={self._duration}:r=30",
            ])
        else:
            concat_file = self._create_concat_file()
            cmd.extend(["-f", "concat", "-safe", "0", "-i", str(concat_file)])

        cmd.extend(["-i", str(self._audio.main_audio)])

        audio_filter = None
        if self._audio.music:
            cmd.extend(["-i", str(self._audio.music)])
            audio_filter = (
                f"[1:a]volume=1.0[tts];"
                f"[2:a]volume={self._audio.music_volume}[music];"
                f"[tts][music]amix=inputs=2:duration=first:dropout_transition=2[aout]"
            )

        video_filters = []

        if not self._background.is_color:
            video_filters.append(
                f"scale={width}:{height}:force_original_aspect_ratio=increase"
            )
            video_filters.append(f"crop={width}:{height}")

        if caption_file:
            escaped_path = str(caption_file).replace(":", "\\:")
            video_filters.append(f"ass='{escaped_path}'")

        filter_parts = []
        if video_filters:
            filter_parts.append(f"[0:v]{''.join(video_filters)}[vout]")
        if audio_filter:
            filter_parts.append(audio_filter)

        if filter_parts:
            cmd.extend(["-filter_complex", ";".join(filter_parts)])

        if video_filters:
            cmd.extend(["-map", "[vout]"])
        else:
            cmd.extend(["-map", "0:v"])

        if audio_filter:
            cmd.extend(["-map", "[aout]"])
        else:
            cmd.extend(["-map", "1:a"])

        cmd.extend([
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            "-t", str(self._duration),
            str(self._resolve_output_path(None)),
        ])

        return cmd

    def _create_concat_file(self) -> Path:
        demuxer = ConcatDemuxer(self._temp_dir)
        demuxer.add_entry(self._background.source, self._background.duration)
        return demuxer.build()

    def _execute_ffmpeg(
        self,
        cmd: list[str],
        progress_callback: callable | None = None,
    ) -> None:
        logger.debug(f"Executing FFmpeg: {' '.join(cmd)}")

        process = subprocess.Popen(
            cmd,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            universal_newlines=True,
        )

        duration_pattern = re.compile(r"Duration: (\d+):(\d+):(\d+)\.(\d+)")
        time_pattern = re.compile(r"time=(\d+):(\d+):(\d+)\.(\d+)")
        total_duration = None

        for line in process.stderr:
            if total_duration is None:
                match = duration_pattern.search(line)
                if match:
                    h, m, s, ms = map(int, match.groups())
                    total_duration = h * 3600 + m * 60 + s + ms / 100

            if total_duration and progress_callback:
                match = time_pattern.search(line)
                if match:
                    h, m, s, ms = map(int, match.groups())
                    current_time = h * 3600 + m * 60 + s + ms / 100
                    percent = min(100, int((current_time / total_duration) * 100))
                    progress_callback(percent)

        process.wait()

        if process.returncode != 0:
            raise VideoGenerationError(
                f"FFmpeg failed with exit code {process.returncode}",
                {"exit_code": process.returncode},
            )

    def _get_audio_duration(self, audio_path: Path) -> float:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(audio_path),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise VideoGenerationError(
                f"Failed to get audio duration: {result.stderr}",
                {"audio_path": str(audio_path)},
            )

        return float(result.stdout.strip())

    def _cleanup_temp_files(self) -> None:
        if self._temp_dir and self._temp_dir.exists():
            shutil.rmtree(self._temp_dir, ignore_errors=True)
            self._temp_dir = None


def check_ffmpeg_available() -> bool:
    """Check if FFmpeg is available on the system.

    Returns:
        True if ffmpeg is found in PATH, False otherwise.
    """
    return shutil.which("ffmpeg") is not None
