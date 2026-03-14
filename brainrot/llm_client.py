"""LLM client with Ollama primary and Groq fallback support.

This module provides a unified interface for LLM generation, preferring local
Ollama instances with automatic fallback to Groq's free tier when Ollama is
unavailable.

Usage:
    >>> from brainrot.llm_client import LLMClient
    >>> client = LLMClient()
    >>> response = client.generate("Write a short joke about programming.")
    >>> print(response)
"""

from __future__ import annotations

import logging
from typing import Any

import requests

from brainrot.config import settings
from brainrot.exceptions import retry

logger = logging.getLogger(__name__)

__all__ = ["LLMClient"]

# Default models for each provider
OLLAMA_DEFAULT_MODEL = "llama3.2"
GROQ_DEFAULT_MODEL = "llama-3.1-8b-instant"

# API endpoints
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


class LLMClient:
    """LLM client with automatic provider detection and fallback.

    Automatically detects available LLM providers, preferring local Ollama.
    Falls back to Groq's free tier if Ollama is unavailable.

    Attributes:
        _provider: The detected or forced provider ("ollama" or "groq").
        _ollama_available: Whether Ollama server is reachable.

    Example:
        >>> client = LLMClient()  # Auto-detect provider
        >>> client = LLMClient(provider="groq")  # Force Groq
        >>> response = client.generate("Hello, world!")
    """

    def __init__(self, provider: str | None = None) -> None:
        """Initialize the LLM client.

        Args:
            provider: Force a specific provider ("ollama" or "groq").
                      If None, auto-detects available provider.
        """
        self._provider: str | None = provider
        self._ollama_available: bool | None = None

        if provider is not None and provider not in ("ollama", "groq"):
            raise ValueError(f"Invalid provider: {provider}. Must be 'ollama' or 'groq'")

    @property
    def provider(self) -> str:
        """Get the active provider.

        Returns:
            The provider name: "ollama" or "groq".
        """
        if self._provider is not None:
            return self._provider

        if self._check_ollama_available():
            self._provider = "ollama"
        elif settings.groq_api_key:
            logger.info("Ollama unavailable, falling back to Groq")
            self._provider = "groq"
        else:
            raise RuntimeError(
                "No LLM provider available. Ensure Ollama is running or set GROQ_API_KEY."
            )

        return self._provider

    def _check_ollama_available(self) -> bool:
        """Check if the Ollama server is available.

        Returns:
            True if Ollama server is reachable, False otherwise.
        """
        if self._ollama_available is not None:
            return self._ollama_available

        try:
            response = requests.get(
                f"{settings.ollama_host}/api/tags",
                timeout=5.0,
            )
            self._ollama_available = response.status_code == 200
            if self._ollama_available:
                logger.debug(f"Ollama server available at {settings.ollama_host}")
        except (requests.RequestException, OSError) as e:
            logger.debug(f"Ollama server check failed: {e}")
            self._ollama_available = False

        return self._ollama_available

    @retry(max_attempts=3, backoff_factor=2.0, exceptions=(requests.RequestException, OSError))
    def generate(
        self,
        prompt: str,
        model: str | None = None,
        system: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Generate text using the configured LLM provider.

        Automatically routes to the appropriate provider based on availability.
        Retries on transient failures with exponential backoff.

        Args:
            prompt: The user prompt to send to the LLM.
            model: Model to use. If None, uses provider-specific default.
            system: Optional system message for context/instructions.
            **kwargs: Additional provider-specific parameters.

        Returns:
            The generated text response.

        Raises:
            RuntimeError: If no LLM provider is available.
            requests.RequestException: On API failures after retries.

        Example:
            >>> client = LLMClient()
            >>> response = client.generate(
            ...     "Write a haiku about coding.",
            ...     system="You are a helpful assistant."
            ... )
        """
        active_provider = self.provider

        if active_provider == "ollama":
            return self._generate_ollama(prompt, model, system, **kwargs)
        else:
            return self._generate_groq(prompt, model, system, **kwargs)

    def _generate_ollama(
        self,
        prompt: str,
        model: str | None,
        system: str | None,
        **kwargs: Any,
    ) -> str:
        """Generate text using local Ollama instance.

        Args:
            prompt: The user prompt to send.
            model: Model name (default: llama3.2).
            system: Optional system message.
            **kwargs: Additional parameters passed to ollama.generate().

        Returns:
            The generated text response.
        """
        import ollama

        model = model or OLLAMA_DEFAULT_MODEL

        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        logger.debug(f"Generating with Ollama model: {model}")

        response = ollama.chat(
            model=model,
            messages=messages,
            host=settings.ollama_host,
            **kwargs,
        )

        return response["message"]["content"]

    def _generate_groq(
        self,
        prompt: str,
        model: str | None,
        system: str | None,
        **kwargs: Any,
    ) -> str:
        """Generate text using Groq API.

        Args:
            prompt: The user prompt to send.
            model: Model name (default: llama-3.1-8b-instant for free tier).
            system: Optional system message.
            **kwargs: Additional parameters (temperature, max_tokens, etc.).

        Returns:
            The generated text response.

        Raises:
            RuntimeError: If GROQ_API_KEY is not configured.
            requests.RequestException: On API failures.
        """
        if not settings.groq_api_key:
            raise RuntimeError("GROQ_API_KEY is not configured")

        model = model or GROQ_DEFAULT_MODEL

        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {settings.groq_api_key}",
            "Content-Type": "application/json",
        }

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
        }

        for key in ("temperature", "max_tokens", "top_p", "stream"):
            if key in kwargs:
                payload[key] = kwargs[key]

        logger.debug(f"Generating with Groq model: {model}")

        response = requests.post(
            GROQ_API_URL,
            headers=headers,
            json=payload,
            timeout=60.0,
        )
        response.raise_for_status()

        data = response.json()
        return data["choices"][0]["message"]["content"]
