"""Text-to-speech integration with edge-tts and audio normalization."""

from __future__ import annotations

import asyncio
import hashlib
import logging
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _get_default_cache_dir() -> Path:
    """Get default cache directory, importing settings lazily."""
    from brainrot.config import settings
    return settings.cache_dir / "audio"

VOICE_PROFILES: dict[str, dict[str, Any]] = {
    "default": {
        "voice": "en-US-AriaNeural",
        "rate": "+0%",
        "pitch": "+0Hz",
    },
    "energetic": {
        "voice": "en-US-JennyNeural",
        "rate": "+10%",
        "pitch": "+5Hz",
    },
    "calm": {
        "voice": "en-US-GuyNeural",
        "rate": "-5%",
        "pitch": "-5Hz",
    },
    "professional": {
        "voice": "en-GB-SoniaNeural",
        "rate": "+0%",
        "pitch": "+0Hz",
    },
    "casual": {
        "voice": "en-AU-NatashaNeural",
        "rate": "+5%",
        "pitch": "+0Hz",
    },
}

AVAILABLE_VOICES = [
    "en-US-AriaNeural",
    "en-US-JennyNeural",
    "en-US-GuyNeural",
    "en-GB-SoniaNeural",
    "en-GB-RyanNeural",
    "en-AU-NatashaNeural",
    "en-AU-WilliamNeural",
    "en-CA-ClaraNeural",
    "en-IN-NeerjaNeural",
]


@dataclass
class TTSClient:
    """Text-to-speech client using edge-tts with audio normalization.

    Uses Microsoft Edge's free TTS API via edge-tts package. Supports multiple
    voice profiles, caching, and FFmpeg-based audio normalization.

    Attributes:
        provider: TTS provider (currently only "edge" supported).
        cache_dir: Directory for caching generated audio files.
        normalize: Whether to apply loudnorm audio normalization.
        target_lufs: Target loudness in LUFS (default: -14).
    """

    provider: str = "edge"
    cache_dir: Path | None = field(default=None)
    normalize: bool = True
    target_lufs: float = -14.0

    def __post_init__(self) -> None:
        if self.cache_dir is None:
            self.cache_dir = _get_default_cache_dir()
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def synthesize(
        self,
        text: str,
        voice: str = "default",
        output_path: Path | None = None,
    ) -> Path:
        """Synthesize speech from text and return path to audio file.

        Args:
            text: Text to convert to speech.
            voice: Voice profile name or specific voice ID.
            output_path: Optional output path. If None, uses cache.

        Returns:
            Path to the generated audio file (MP3 format).

        Raises:
            RuntimeError: If TTS synthesis fails.
        """
        cache_key = self._get_cache_key(text, voice)
        cached_path = self.cache_dir / f"{cache_key}.mp3"

        if cached_path.exists():
            logger.debug(f"Using cached audio: {cached_path}")
            if output_path:
                cached_path.rename(output_path)
                return output_path
            return cached_path

        raw_path = self._synthesize_edge(text, voice)

        if self.normalize:
            final_path = self._normalize_audio(raw_path, cached_path)
        else:
            final_path = raw_path.rename(cached_path)

        if output_path and final_path != output_path:
            final_path.rename(output_path)
            return output_path

        return final_path

    def _synthesize_edge(self, text: str, voice: str) -> Path:
        """Synthesize speech using edge-tts.

        Args:
            text: Text to convert to speech.
            voice: Voice profile name or specific voice ID.

        Returns:
            Path to the raw (un-normalized) audio file.

        Raises:
            RuntimeError: If edge-tts synthesis fails.
        """
        voice_config = self._get_voice_config(voice)
        voice_id = voice_config["voice"]
        rate = voice_config.get("rate", "+0%")
        pitch = voice_config.get("pitch", "+0Hz")

        temp_path = self.cache_dir / f"temp_{hashlib.md5(text.encode()).hexdigest()}.mp3"

        try:
            import edge_tts

            communicate = edge_tts.Communicate(text, voice_id, rate=rate, pitch=pitch)

            async def _save() -> None:
                await communicate.save(str(temp_path))

            asyncio.run(_save())

            if not temp_path.exists():
                raise RuntimeError("edge-tts failed to create audio file")

            logger.debug(f"Synthesized audio with voice {voice_id}: {temp_path}")
            return temp_path

        except ImportError as e:
            raise RuntimeError("edge-tts package not installed. Run: pip install edge-tts") from e
        except Exception as e:
            raise RuntimeError(f"TTS synthesis failed: {e}") from e

    def _normalize_audio(self, input_path: Path, output_path: Path) -> Path:
        """Normalize audio to target loudness using FFmpeg loudnorm.

        Args:
            input_path: Path to input audio file.
            output_path: Path for normalized output.

        Returns:
            Path to the normalized audio file.

        Raises:
            RuntimeError: If FFmpeg normalization fails.
        """
        cmd = [
            "ffmpeg",
            "-y",
            "-i", str(input_path),
            "-af", f"loudnorm=I={self.target_lufs}:TP=-1.5:LRA=11",
            "-ar", "44100",
            "-ac", "2",
            str(output_path),
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            if input_path.exists():
                input_path.unlink()
            logger.debug(f"Normalized audio to {self.target_lufs} LUFS: {output_path}")
            return output_path
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"FFmpeg normalization failed: {e.stderr}") from e
        except FileNotFoundError as e:
            raise RuntimeError("FFmpeg not found. Install FFmpeg to enable audio normalization.") from e

    def _get_cache_key(self, text: str, voice: str) -> str:
        """Generate cache key from text and voice.

        Args:
            text: Text content.
            voice: Voice profile or ID.

        Returns:
            MD5 hash string for caching.
        """
        voice_config = self._get_voice_config(voice)
        key_data = f"{text}:{voice_config['voice']}:{voice_config.get('rate', '+0%')}:{voice_config.get('pitch', '+0Hz')}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _get_voice_config(self, voice: str) -> dict[str, Any]:
        """Get voice configuration from profile name or direct voice ID.

        Args:
            voice: Voice profile name (e.g., "energetic") or voice ID.

        Returns:
            Voice configuration dictionary.
        """
        if voice in VOICE_PROFILES:
            return VOICE_PROFILES[voice]
        return {
            "voice": voice,
            "rate": "+0%",
            "pitch": "+0Hz",
        }

    def get_available_voices(self) -> list[str]:
        """Get list of available voice IDs.

        Returns:
            List of available edge-tts voice IDs.
        """
        return AVAILABLE_VOICES.copy()

    def get_voice_profiles(self) -> list[str]:
        """Get list of predefined voice profile names.

        Returns:
            List of voice profile names.
        """
        return list(VOICE_PROFILES.keys())

    def register_voice_profile(self, name: str, config: dict[str, Any]) -> None:
        """Register a custom voice profile.

        Args:
            name: Profile name.
            config: Configuration with 'voice', optional 'rate' and 'pitch'.
        """
        if "voice" not in config:
            raise ValueError("Voice config must include 'voice' key")
        VOICE_PROFILES[name] = config
        logger.debug(f"Registered voice profile: {name}")

    def clear_cache(self) -> int:
        """Clear all cached audio files.

        Returns:
            Number of files deleted.
        """
        count = 0
        for file in self.cache_dir.glob("*.mp3"):
            file.unlink()
            count += 1
        logger.debug(f"Cleared {count} cached audio files")
        return count
