"""Template configuration and rendering system.

Provides TemplateConfig for defining video styling templates
and TemplateRenderer for applying templates to VideoBuilder.
"""

from __future__ import annotations

import json
import logging
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from brainrot.types import ContentTemplate, Script
from brainrot.video.assembly import VideoBuilder
from brainrot.video.captions import CaptionStyle

logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).parent


@dataclass
class BackgroundStyle:
    """Background configuration for a template.
    
    Attributes:
        type: Background type ('solid', 'gradient', 'video').
        color: Primary color (hex format like '#1a1a2e').
        secondary_color: Secondary color for gradients.
        gradient_direction: Gradient angle in degrees.
        opacity: Background opacity (0.0 to 1.0).
    """
    type: Literal["solid", "gradient", "video"] = "solid"
    color: str = "#000000"
    secondary_color: str | None = None
    gradient_direction: int = 180
    opacity: float = 1.0


@dataclass
class TransitionConfig:
    """Transition effect configuration.
    
    Attributes:
        type: Transition type ('fade', 'slide', 'zoom', 'wipe', 'none').
        duration: Duration in seconds.
        easing: Easing function name.
    """
    type: Literal["fade", "slide", "zoom", "wipe", "none"] = "fade"
    duration: float = 0.5
    easing: str = "ease-out"


@dataclass
class TypographyConfig:
    """Typography configuration for a template.
    
    Attributes:
        primary_font: Main font family name.
        secondary_font: Accent/secondary font family.
        primary_size: Base font size in pixels.
        secondary_size: Secondary text size.
        line_height: Line height multiplier.
        letter_spacing: Letter spacing in pixels.
    """
    primary_font: str = "Montserrat Bold"
    secondary_font: str = "Montserrat"
    primary_size: int = 72
    secondary_size: int = 48
    line_height: float = 1.2
    letter_spacing: float = 0.0


@dataclass
class ColorPalette:
    """Color palette for a template.
    
    Attributes:
        primary: Primary/accent color.
        secondary: Secondary color.
        background: Background color.
        text: Main text color.
        text_secondary: Secondary/muted text color.
        accent: Highlight/accent color.
        outline: Caption outline color.
    """
    primary: str = "#FFFFFF"
    secondary: str = "#888888"
    background: str = "#000000"
    text: str = "#FFFFFF"
    text_secondary: str = "#CCCCCC"
    accent: str = "#FF0000"
    outline: str = "#000000"


@dataclass
class TemplateConfig:
    """Complete template configuration for video styling.
    
    A template defines all visual aspects of a video including
    background, captions, colors, fonts, and transitions.
    
    Attributes:
        name: Unique template identifier.
        display_name: Human-readable template name.
        description: Template description.
        background: Background style configuration.
        caption: Caption style configuration.
        transition: Transition effect configuration.
        typography: Typography/font configuration.
        colors: Color palette.
        animation_style: Animation approach ('static', 'kinetic', 'smooth').
        caption_position: Default caption position.
        version: Template version number.
    """
    name: str
    display_name: str = ""
    description: str = ""
    background: BackgroundStyle = field(default_factory=BackgroundStyle)
    caption: dict[str, Any] = field(default_factory=dict)
    transition: TransitionConfig = field(default_factory=TransitionConfig)
    typography: TypographyConfig = field(default_factory=TypographyConfig)
    colors: ColorPalette = field(default_factory=ColorPalette)
    animation_style: Literal["static", "kinetic", "smooth"] = "smooth"
    caption_position: Literal["top", "center", "bottom"] = "bottom"
    version: str = "1.0.0"
    
    @classmethod
    def from_json(cls, path: Path | str) -> "TemplateConfig":
        """Load template configuration from JSON file.
        
        Args:
            path: Path to JSON template file.
            
        Returns:
            TemplateConfig instance.
            
        Raises:
            FileNotFoundError: If template file doesn't exist.
            ValueError: If JSON is malformed or missing required fields.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Template file not found: {path}")
        
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        return cls.from_dict(data)
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TemplateConfig":
        """Create TemplateConfig from dictionary.
        
        Args:
            data: Dictionary with template configuration.
            
        Returns:
            TemplateConfig instance.
        """
        bg_data = data.get("background_style", data.get("background", {}))
        background = BackgroundStyle(
            type=bg_data.get("type", "solid"),
            color=bg_data.get("color", "#000000"),
            secondary_color=bg_data.get("secondary_color"),
            gradient_direction=bg_data.get("gradient_direction", 180),
            opacity=bg_data.get("opacity", 1.0),
        )
        
        trans_data = data.get("transition", {})
        transition = TransitionConfig(
            type=trans_data.get("type", "fade"),
            duration=trans_data.get("duration", 0.5),
            easing=trans_data.get("easing", "ease-out"),
        )
        
        font_data = data.get("fonts", {})
        typography = TypographyConfig(
            primary_font=font_data.get("primary", "Montserrat Bold"),
            secondary_font=font_data.get("secondary", "Montserrat"),
            primary_size=font_data.get("primary_size", 72),
            secondary_size=font_data.get("secondary_size", 48),
            line_height=font_data.get("line_height", 1.2),
            letter_spacing=font_data.get("letter_spacing", 0.0),
        )
        
        colors_data = data.get("colors", {})
        colors = ColorPalette(
            primary=colors_data.get("primary", "#FFFFFF"),
            secondary=colors_data.get("secondary", "#888888"),
            background=colors_data.get("background", "#000000"),
            text=colors_data.get("text", "#FFFFFF"),
            text_secondary=colors_data.get("text_secondary", "#CCCCCC"),
            accent=colors_data.get("accent", "#FF0000"),
            outline=colors_data.get("outline", "#000000"),
        )
        
        return cls(
            name=data["name"],
            display_name=data.get("display_name", data["name"]),
            description=data.get("description", ""),
            background=background,
            caption=data.get("caption_style", data.get("caption", {})),
            transition=transition,
            typography=typography,
            colors=colors,
            animation_style=data.get("animation_style", "smooth"),
            caption_position=data.get("caption_position", "bottom"),
            version=data.get("version", "1.0.0"),
        )
    
    def to_content_template(self) -> ContentTemplate:
        """Convert to ContentTemplate for type compatibility.
        
        Returns:
            ContentTemplate instance with this template's settings.
        """
        return ContentTemplate(
            name=self.name,
            style_config={
                "background": {
                    "type": self.background.type,
                    "color": self.background.color,
                },
                "transition": {
                    "type": self.transition.type,
                    "duration": self.transition.duration,
                },
                "animation_style": self.animation_style,
            },
            caption_style=self.caption_position,
            font_family=self.typography.primary_font,
            colors={
                "primary": self.colors.primary,
                "secondary": self.colors.secondary,
                "background": self.colors.background,
                "text": self.colors.text,
                "accent": self.colors.accent,
            },
        )


class TemplateRenderer:
    """Applies template styling to VideoBuilder for video production.
    
    The TemplateRenderer bridges the gap between template configuration
    and the VideoBuilder, translating template settings into concrete
    VideoBuilder method calls.
    
    Example:
        >>> renderer = TemplateRenderer("tech_news")
        >>> builder = VideoBuilder()
        >>> renderer.apply_to_builder(builder, script)
        >>> video_path = builder.render("output.mp4")
    """
    
    def __init__(self, template_name: str | None = None) -> None:
        """Initialize template renderer.
        
        Args:
            template_name: Name of template to load. If None, uses default.
        """
        self._config: TemplateConfig | None = None
        self._template_name = template_name
        
        if template_name:
            self.load_template(template_name)
    
    @property
    def config(self) -> TemplateConfig:
        """Get current template configuration.
        
        Returns:
            Current TemplateConfig.
            
        Raises:
            RuntimeError: If no template is loaded.
        """
        if self._config is None:
            raise RuntimeError("No template loaded. Call load_template() first.")
        return self._config
    
    def load_template(self, name: str) -> TemplateConfig:
        """Load a template by name.
        
        Searches for template JSON file in the templates directory.
        
        Args:
            name: Template name (without .json extension).
            
        Returns:
            Loaded TemplateConfig.
            
        Raises:
            FileNotFoundError: If template file doesn't exist.
        """
        template_path = TEMPLATE_DIR / f"{name}.json"
        self._config = TemplateConfig.from_json(template_path)
        self._template_name = name
        logger.info(f"Loaded template: {name}")
        return self._config
    
    def get_caption_style(self) -> CaptionStyle:
        """Get CaptionStyle configured for current template.
        
        Returns:
            CaptionStyle instance with template's styling.
        """
        config = self.config

        def hex_to_ass(hex_color: str) -> str:
            """Convert hex color (#RRGGBB) to ASS format (&HAABBGGRR)."""
            hex_color = hex_color.lstrip("#")
            if len(hex_color) == 6:
                r, g, b = hex_color[0:2], hex_color[2:4], hex_color[4:6]
                return f"&H00{b}{g}{r}".upper()
            return "&H00FFFFFF"

        caption_config = config.caption or {}
        
        return CaptionStyle(
            font_family=caption_config.get("font", config.typography.primary_font),
            font_size=caption_config.get("size", config.typography.primary_size),
            color=hex_to_ass(caption_config.get("color", config.colors.text)),
            outline_color=hex_to_ass(caption_config.get("outline_color", config.colors.outline)),
            outline_width=caption_config.get("outline_width", 4),
            shadow_color="&H80000000",
            shadow_depth=2,
            position=config.caption_position,
            margin_v=caption_config.get("margin_v", 80),
            alignment=caption_config.get("alignment", 2),
            bold=caption_config.get("bold", True),
            italic=caption_config.get("italic", False),
        )
    
    def apply_to_builder(
        self,
        builder: VideoBuilder,
        script: Script,
        audio_path: Path | None = None,
        duration: float | None = None,
    ) -> None:
        """Apply template styling to a VideoBuilder instance.
        
        Configures the VideoBuilder with template's background, captions,
        and styling based on the provided script.
        
        Args:
            builder: VideoBuilder instance to configure.
            script: Script containing text for captions.
            audio_path: Path to audio file (optional, for duration detection).
            duration: Video duration in seconds (optional).
        """
        config = self.config

        if config.background.type == "solid":
            builder.add_background(
                source=config.background.color,
                duration=duration or 30.0,
            )
        elif config.background.type == "gradient":
            builder.add_background(
                source=config.background.color,
                duration=duration or 30.0,
            )
        else:
            builder.add_background(
                source=config.background.color,
                duration=duration or 30.0,
            )

        caption_style = self.get_caption_style()
        builder.add_captions(text=script.text, style=caption_style)

        if audio_path:
            builder.add_audio(audio_path=audio_path)
        
        logger.debug(f"Applied template '{config.name}' to VideoBuilder")
    
    def generate_thumbnail(
        self,
        video_path: Path | str,
        output_path: Path | str | None = None,
        timestamp: float = 1.0,
    ) -> Path:
        """Generate a thumbnail from a video file.
        
        Uses FFmpeg to extract a single frame from the video at the
        specified timestamp.
        
        Args:
            video_path: Path to the input video file.
            output_path: Path for output thumbnail. If None, uses
                         video_path with _thumb.png suffix.
            timestamp: Time in seconds to extract frame (default: 1.0).
            
        Returns:
            Path to the generated thumbnail image.
            
        Raises:
            RuntimeError: If FFmpeg fails to generate thumbnail.
        """
        video_path = Path(video_path)
        
        if output_path is None:
            output_path = video_path.parent / f"{video_path.stem}_thumb.png"
        else:
            output_path = Path(output_path)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            "ffmpeg",
            "-y",
            "-i", str(video_path),
            "-ss", str(timestamp),
            "-vframes", "1",
            str(output_path),
        ]
        
        logger.debug(f"Generating thumbnail: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )
        
        if result.returncode != 0:
            logger.error(f"FFmpeg thumbnail failed: {result.stderr}")
            raise RuntimeError(
                f"Failed to generate thumbnail: {result.stderr}"
            )
        
        if not output_path.exists():
            raise RuntimeError(f"Thumbnail file not created: {output_path}")
        
        logger.info(f"Generated thumbnail: {output_path}")
        return output_path
    
    def get_style_summary(self) -> dict[str, Any]:
        """Get a summary of current template's styling.
        
        Returns:
            Dictionary with template styling summary.
        """
        config = self.config
        return {
            "name": config.name,
            "display_name": config.display_name,
            "background": {
                "type": config.background.type,
                "color": config.background.color,
            },
            "colors": {
                "primary": config.colors.primary,
                "accent": config.colors.accent,
                "text": config.colors.text,
            },
            "typography": {
                "primary_font": config.typography.primary_font,
                "primary_size": config.typography.primary_size,
            },
            "caption_position": config.caption_position,
            "transition": config.transition.type,
        }


def list_templates() -> list[str]:
    """List all available template names.
    
    Scans the templates directory for JSON template files.
    
    Returns:
        List of template names (without .json extension).
    """
    templates = []
    
    if not TEMPLATE_DIR.exists():
        return templates
    
    for file in TEMPLATE_DIR.glob("*.json"):
        templates.append(file.stem)
    
    return sorted(templates)


def get_template_path(name: str) -> Path:
    """Get the file path for a template by name.
    
    Args:
        name: Template name.
        
    Returns:
        Path to the template JSON file.
    """
    return TEMPLATE_DIR / f"{name}.json"
