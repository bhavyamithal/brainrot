"""Caption generation for ASS format subtitles with kinetic typography support.

This module provides tools for generating styled subtitles in ASS format,
supporting custom fonts, colors, positioning, and timing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path
from typing import Literal

__all__ = ["CaptionStyle", "CaptionGenerator"]


@dataclass
class CaptionStyle:
    """Configuration for caption appearance in ASS format.

    Attributes:
        font_family: Font name (e.g., 'Arial', 'Montserrat Bold').
        font_size: Font size in pixels (for 1080p height reference).
        color: Primary text color in ASS format (&HAABBGGRR).
        outline_color: Border/outline color in ASS format.
        outline_width: Border thickness in pixels.
        shadow_color: Drop shadow color in ASS format.
        shadow_depth: Shadow offset in pixels.
        position: Vertical position ('top', 'center', 'bottom').
        margin_v: Vertical margin from edge in pixels.
        alignment: ASS alignment value (1-9 numpad layout).
        bold: Whether text is bold.
        italic: Whether text is italic.
    """

    font_family: str = "Montserrat Bold"
    font_size: int = 72
    color: str = "&H00FFFFFF"  # White (ASS format: &HAABBGGRR)
    outline_color: str = "&H00000000"  # Black
    outline_width: int = 4
    shadow_color: str = "&H80000000"  # Semi-transparent black
    shadow_depth: int = 2
    position: Literal["top", "center", "bottom"] = "bottom"
    margin_v: int = 80
    alignment: int = 2  # Bottom center (ASS numpad: 1-9)
    bold: bool = True
    italic: bool = False

    def to_ass_style(self) -> str:
        """Convert style to ASS format style line.

        Returns:
            ASS style definition string.
        """
        # ASS alignment mapping: bottom=2, center=5, top=8 (centered horizontally)
        alignment_map = {"bottom": 2, "center": 5, "top": 8}
        align = alignment_map.get(self.position, 2)

        # Bold: -1 = true, 0 = false
        bold_flag = -1 if self.bold else 0
        italic_flag = -1 if self.italic else 0

        # ASS style format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour,
        # OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut,
        # ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow,
        # Alignment, MarginL, MarginR, MarginV, Encoding
        return (
            f"Style: Default,{self.font_family},{self.font_size},"
            f"{self.color},&H000000FF,{self.outline_color},{self.shadow_color},"
            f"{bold_flag},{italic_flag},0,0,100,100,0,0,1,"
            f"{self.outline_width},{self.shadow_depth},{align},"
            f"10,10,{self.margin_v},1"
        )


@dataclass
class CaptionLine:
    """A single caption line with timing information.

    Attributes:
        text: The caption text content.
        start_time: Start time in seconds.
        end_time: End time in seconds.
        effect: Optional ASS effect tags.
    """

    text: str
    start_time: float
    end_time: float
    effect: str = ""


class CaptionGenerator:
    """Generates ASS format subtitles with styling.

    Creates Advanced SubStation Alpha (ASS) subtitle files with
    support for custom fonts, colors, positioning, and timing.
    """

    def __init__(self, style: CaptionStyle | None = None) -> None:
        """Initialize caption generator.

        Args:
            style: Caption style configuration. Uses defaults if None.
        """
        self.style = style or CaptionStyle()

    def generate_ass(
        self,
        text: str,
        duration: float,
        words_per_line: int = 6,
        words_per_second: float = 2.5,
    ) -> str:
        """Generate ASS format subtitle content.

        Creates an ASS subtitle file with the given text, automatically
        split into lines and timed for the specified duration.

        Args:
            text: The full text to caption.
            duration: Total duration in seconds.
            words_per_line: Maximum words per caption line.
            words_per_second: Reading speed for timing calculations.

        Returns:
            Complete ASS file content as string.
        """
        lines = self._split_into_lines(text, words_per_line)
        caption_lines = self._time_lines(lines, duration, words_per_second)
        return self._build_ass_file(caption_lines)

    def generate_ass_to_file(
        self,
        text: str,
        duration: float,
        output_path: Path | str,
        **kwargs,
    ) -> Path:
        """Generate ASS file and save to disk.

        Args:
            text: The full text to caption.
            duration: Total duration in seconds.
            output_path: Path to save the ASS file.
            **kwargs: Additional arguments passed to generate_ass.

        Returns:
            Path to the saved ASS file.
        """
        output_path = Path(output_path)
        ass_content = self.generate_ass(text, duration, **kwargs)
        output_path.write_text(ass_content, encoding="utf-8")
        return output_path

    def _split_into_lines(self, text: str, words_per_line: int) -> list[str]:
        """Split text into caption lines.

        Args:
            text: Full text to split.
            words_per_line: Maximum words per line.

        Returns:
            List of caption line strings.
        """
        words = text.split()
        lines = []

        for i in range(0, len(words), words_per_line):
            line_words = words[i : i + words_per_line]
            lines.append(" ".join(line_words))

        return lines

    def _time_lines(
        self,
        lines: list[str],
        duration: float,
        words_per_second: float,
    ) -> list[CaptionLine]:
        """Assign timing to caption lines.

        Distributes timing across lines based on word count and reading speed.

        Args:
            lines: List of caption text lines.
            duration: Total duration in seconds.
            words_per_second: Reading speed for timing.

        Returns:
            List of CaptionLine objects with timing.
        """
        total_words = sum(len(line.split()) for line in lines)
        time_per_word = duration / max(total_words, 1)

        caption_lines = []
        current_time = 0.0

        for line in lines:
            word_count = len(line.split())
            line_duration = word_count * time_per_word
            end_time = min(current_time + line_duration, duration)

            caption_lines.append(
                CaptionLine(
                    text=line,
                    start_time=current_time,
                    end_time=end_time,
                )
            )
            current_time = end_time

        # Extend last line to match total duration
        if caption_lines:
            caption_lines[-1].end_time = duration

        return caption_lines

    def _build_ass_file(self, caption_lines: list[CaptionLine]) -> str:
        """Build complete ASS file content.

        Args:
            caption_lines: List of timed caption lines.

        Returns:
            Complete ASS file content as string.
        """
        header = self._build_ass_header()
        events = self._build_ass_events(caption_lines)
        return header + events

    def _build_ass_header(self) -> str:
        """Build ASS file header section.

        Returns:
            ASS header string with script info and styles.
        """
        return (
            "[Script Info]\n"
            "Title: Generated Captions\n"
            "ScriptType: v4.00+\n"
            "WrapStyle: 0\n"
            "ScaledBorderAndShadow: yes\n"
            "YCbCr Matrix: TV.709\n"
            "PlayResX: 1080\n"
            "PlayResY: 1920\n"
            "\n"
            "[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
            "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
            "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
            "Alignment, MarginL, MarginR, MarginV, Encoding\n"
            f"{self.style.to_ass_style()}\n"
            "\n"
            "[Events]\n"
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, "
            "Effect, Text\n"
        )

    def _build_ass_events(self, caption_lines: list[CaptionLine]) -> str:
        """Build ASS events section.

        Args:
            caption_lines: List of timed caption lines.

        Returns:
            ASS events string with dialogue lines.
        """
        events = []
        for line in caption_lines:
            start = self._format_time(line.start_time)
            end = self._format_time(line.end_time)
            effect = f"{{{line.effect}}}" if line.effect else ""
            text = line.text.replace("\n", "\\N")  # ASS line break
            events.append(
                f"Dialogue: 0,{start},{end},Default,,0,0,0,{effect}{text}"
            )
        return "\n".join(events)

    def _format_time(self, seconds: float) -> str:
        """Format time in ASS format (H:MM:SS.CS).

        Args:
            seconds: Time in seconds.

        Returns:
            ASS formatted time string.
        """
        td = timedelta(seconds=seconds)
        total_seconds = int(td.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, secs = divmod(remainder, 60)
        centiseconds = int((seconds - int(seconds)) * 100)
        return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"
