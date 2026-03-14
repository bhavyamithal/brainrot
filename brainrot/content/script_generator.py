"""Script generator with template-based content creation.

Provides template-driven script generation for short-form video content,
with validation for length and engagement hooks.
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from brainrot.config import settings
from brainrot.llm_client import LLMClient
from brainrot.types import Script, Trend

logger = logging.getLogger(__name__)

__all__ = ["ScriptTemplate", "ScriptGenerator"]


@dataclass
class ScriptTemplate:
    """Template definition for script generation.

    Attributes:
        name: Template identifier (e.g., 'news_synthesis')
        system_prompt: Instructions for the LLM
        user_prompt_template: Template with {placeholders}
        min_words: Minimum word count (default 150)
        max_words: Maximum word count (default 300)
    """

    name: str
    system_prompt: str
    user_prompt_template: str
    min_words: int = 150
    max_words: int = 300

    def format_prompt(self, **kwargs: Any) -> str:
        """Format the user prompt template with provided values.

        Args:
            **kwargs: Values for template placeholders

        Returns:
            Formatted prompt string
        """
        return self.user_prompt_template.format(**kwargs)


DEFAULT_TEMPLATES: dict[str, ScriptTemplate] = {
    "news_synthesis": ScriptTemplate(
        name="news_synthesis",
        system_prompt="""You are a tech content creator specializing in short-form videos.
Create engaging, concise scripts for YouTube Shorts (under 30 seconds).

Your scripts must:
- Start with a compelling hook in the first sentence (grab attention immediately)
- Be conversational and energetic
- Explain technical concepts simply
- End with a call-to-action or thought-provoking statement
- Be exactly 150-300 words (critical for 30-second format)

Do NOT use:
- Generic intros like "Today we're discussing" or "In this video"
- Filler words or phrases
- Overly technical jargon without explanation

Write as if speaking directly to one viewer.""",
        user_prompt_template="""Create a 30-second script about this trending tech news:

Title: {title}
Source: {source}
URL: {url}

Keywords to incorporate: {keywords}

Requirements:
1. Start with a hook that makes viewers stop scrolling
2. Summarize the news in simple terms
3. Add brief analysis or opinion
4. End with engagement hook

Word count: 150-300 words exactly.""",
        min_words=150,
        max_words=300,
    ),
    "explainer": ScriptTemplate(
        name="explainer",
        system_prompt="""You are an expert at explaining complex technical concepts in simple, engaging ways.
Create short-form video scripts that make viewers feel smart.

Your scripts must:
- Start with a relatable hook or question
- Use analogies and examples
- Be conversational and fun
- Build understanding progressively
- Be exactly 150-300 words

Avoid:
- Lecturing tone
- Assumption of prior knowledge
- Dry definitions

Write like you're explaining to a curious friend.""",
        user_prompt_template="""Create an explainer script for this concept:

Title: {title}
Keywords: {keywords}

Requirements:
1. Open with a relatable question or scenario
2. Explain the concept using a simple analogy
3. Give a concrete example
4. End with why this matters

Word count: 150-300 words exactly.""",
        min_words=150,
        max_words=300,
    ),
}


class ScriptGenerator:
    """Generate scripts from trends using templates and LLM.

    Handles script generation, validation, and history tracking
    to avoid duplicate content.
    """

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        """Initialize the script generator.

        Args:
            llm_client: Optional LLM client. Creates new one if not provided.
        """
        self._llm = llm_client
        self._templates: dict[str, ScriptTemplate] = dict(DEFAULT_TEMPLATES)
        self._history_path = settings.cache_dir / "script_history.json"
        self._history: list[dict[str, Any]] = self._load_history()

    @property
    def llm(self) -> LLMClient:
        """Get or create LLM client lazily."""
        if self._llm is None:
            self._llm = LLMClient()
        return self._llm

    def _load_history(self) -> list[dict[str, Any]]:
        """Load script history from cache file."""
        if self._history_path.exists():
            try:
                with open(self._history_path) as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"Failed to load script history: {e}")
        return []

    def _save_history(self) -> None:
        """Persist script history to cache file."""
        self._history_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._history_path, "w") as f:
            json.dump(self._history, f, indent=2)

    def register_template(self, template: ScriptTemplate) -> None:
        """Register a new template or override existing one.

        Args:
            template: Template to register
        """
        self._templates[template.name] = template
        logger.debug(f"Registered template: {template.name}")

    def get_template(self, name: str) -> ScriptTemplate:
        """Get a template by name.

        Args:
            name: Template name

        Returns:
            ScriptTemplate instance

        Raises:
            KeyError: If template not found
        """
        if name not in self._templates:
            available = ", ".join(self._templates.keys())
            raise KeyError(f"Template '{name}' not found. Available: {available}")
        return self._templates[name]

    def is_duplicate(self, trend_id: str) -> bool:
        """Check if a script already exists for this trend.

        Args:
            trend_id: Trend identifier to check

        Returns:
            True if script already generated for this trend
        """
        return any(entry.get("trend_id") == trend_id for entry in self._history)

    def generate(
        self,
        trend: Trend | dict[str, Any],
        template: str = "news_synthesis",
    ) -> Script:
        """Generate a script from a trend using specified template.

        Args:
            trend: Trend object or dict with trend data
            template: Template name to use

        Returns:
            Generated Script object

        Raises:
            KeyError: If template not found
            ValueError: If generated script fails validation
        """
        template_obj = self.get_template(template)

        if isinstance(trend, Trend):
            trend_data = trend.model_dump()
            trend_id = trend.id
        else:
            trend_data = trend
            trend_id = trend_data.get("id", str(uuid.uuid4()))

        if self.is_duplicate(trend_id):
            logger.warning(f"Script already exists for trend {trend_id}")
            existing = next(
                e for e in self._history if e.get("trend_id") == trend_id
            )
            return Script(**existing)

        prompt = template_obj.format_prompt(
            title=trend_data.get("title", ""),
            source=trend_data.get("source", ""),
            url=trend_data.get("url", ""),
            keywords=", ".join(trend_data.get("keywords", [])),
        )

        logger.info(f"Generating script for trend: {trend_id}")
        text = self.llm.generate(
            prompt=prompt,
            system=template_obj.system_prompt,
        )

        word_count = self._count_words(text)

        if not self._validate_script(text, template_obj.min_words, template_obj.max_words):
            adjusted_text = self._adjust_length(
                text, word_count, template_obj.min_words, template_obj.max_words
            )
            if adjusted_text:
                text = adjusted_text
                word_count = self._count_words(text)

        if not self._validate_script(text, template_obj.min_words, template_obj.max_words):
            raise ValueError(
                f"Generated script has {word_count} words, "
                f"must be {template_obj.min_words}-{template_obj.max_words}"
            )

        hook = self._extract_hook(text)
        script = Script(
            id=str(uuid.uuid4()),
            trend_id=trend_id,
            text=text.strip(),
            hook=hook,
            word_count=word_count,
            template=template,
            created_at=datetime.utcnow(),
        )

        self._history.append(script.model_dump())
        self._save_history()

        logger.info(f"Generated script {script.id}: {word_count} words")
        return script

    def _count_words(self, text: str) -> int:
        """Count words in text.

        Args:
            text: Text to count

        Returns:
            Word count
        """
        words = text.split()
        return len(words)

    def _validate_script(self, text: str, min_words: int, max_words: int) -> bool:
        """Validate script meets length requirements.

        Args:
            text: Script text to validate
            min_words: Minimum word count
            max_words: Maximum word count

        Returns:
            True if valid, False otherwise
        """
        word_count = self._count_words(text)
        return min_words <= word_count <= max_words

    def _extract_hook(self, text: str) -> str:
        """Extract the hook (first engaging sentence) from script.

        The hook is the first sentence that grabs attention,
        critical for the first 3 seconds of video.

        Args:
            text: Full script text

        Returns:
            Hook sentence (first sentence, up to 150 chars)
        """
        sentences = re.split(r"[.!?]+", text.strip())
        if sentences:
            hook = sentences[0].strip()
            if len(hook) > 150:
                hook = hook[:147] + "..."
            return hook
        return text[:150]

    def _adjust_length(
        self, text: str, current_count: int, min_words: int, max_words: int
    ) -> str | None:
        """Attempt to adjust script length via LLM regeneration.

        Args:
            text: Original text
            current_count: Current word count
            min_words: Target minimum
            max_words: Target maximum

        Returns:
            Adjusted text or None if failed
        """
        if current_count < min_words:
            instruction = f"Expand this script to {min_words}-{max_words} words while keeping the same message and style. Add more detail and examples."
        elif current_count > max_words:
            instruction = f"Condense this script to {min_words}-{max_words} words while keeping the key message and hook. Remove filler words."
        else:
            return None

        try:
            adjusted = self.llm.generate(
                prompt=f"{instruction}\n\nOriginal script:\n{text}",
                system="You are an editor. Adjust the script length precisely. Output only the adjusted script.",
            )
            return adjusted
        except Exception as e:
            logger.warning(f"Failed to adjust script length: {e}")
            return None

    def get_history(self, limit: int = 50) -> list[Script]:
        """Get recent script history.

        Args:
            limit: Maximum number of scripts to return

        Returns:
            List of Script objects from history
        """
        scripts = []
        for entry in self._history[-limit:]:
            try:
                scripts.append(Script(**entry))
            except Exception as e:
                logger.warning(f"Invalid history entry: {e}")
        return scripts

    def clear_history(self) -> None:
        """Clear all script history."""
        self._history = []
        self._save_history()
        logger.info("Script history cleared")
