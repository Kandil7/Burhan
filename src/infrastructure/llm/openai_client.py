"""
OpenAI client factory for Burhan.

Supports any OpenAI-compatible API (OpenAI, Azure, Ollama, vLLM, Groq, etc.)
by reading from settings.
"""

from __future__ import annotations

from openai import AsyncOpenAI

from src.config.settings import settings


def build_openai_client() -> AsyncOpenAI:
    """
    Factory: constructs an AsyncOpenAI client from Settings.

    Supports any OpenAI-compatible API by reading OPENAI_BASE_URL from environment.

    Example — use with Groq or Ollama:
        OPENAI_BASE_URL=https://api.groq.com/openai/v1
        OPENAI_API_KEY=gsk_...
    """
    if not settings.openai_api_key:
        raise ValueError(
            "OPENAI_API_KEY is required when classifier_backend is 'llm' or 'chain'. "
            "Set it in your .env file or environment."
        )

    return AsyncOpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
    )
