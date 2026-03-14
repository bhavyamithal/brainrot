"""Content templates library for video styling.

This module provides template-based styling for video content,
enabling consistent visual branding across video productions.

Classes:
    - TemplateConfig: Configuration model for a video template
    - TemplateRenderer: Applies template styling to video builder

Templates define:
    - Background style (colors, gradients)
    - Caption style (fonts, colors, positioning)
    - Transition effects
    - Color palettes
    - Typography choices
"""

from brainrot.templates.renderer import (
    TemplateConfig,
    TemplateRenderer,
    list_templates,
)

__all__ = [
    "TemplateConfig",
    "TemplateRenderer",
    "list_templates",
]
