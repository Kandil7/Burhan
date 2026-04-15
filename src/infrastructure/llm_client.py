"""
LLM client abstraction for Athar Islamic QA system.

Provides unified interface for multiple LLM providers:
- OpenAI  (GPT-4o-mini, GPT-4)
- Groq    (Qwen3-32B, Llama-3.3-70B)
- Local   (future — any OpenAI-compatible endpoint)

Design principles
─────────────────
- No module-level asyncio.Lock (created inside event loop only).
- No global mutable singletons — clients built in lifespan, injected
  via app.state / FastAPI Depends.
- _strip_thinking() applied to every text response.
- generate_json() gracefully skips response_format on Groq.
- close_all() properly closes both clients.
- temperature=0.0 handled correctly (not treated as falsy).
"""
from __future__ import annotations

import asyncio
import json
import re
from typing import Any

from openai import AsyncOpenAI

from src.config.logging_config import get_logger
from src.config.settings import settings

logger = get_logger()

# ── Optional Groq import ──────────────────────────────────────────────────────
try:
    from groq import AsyncGroq
    GROQ_AVAILABLE = True
except ImportError:
    AsyncGroq = None          # type: ignore[misc,assignment]
    GROQ_AVAILABLE = False

# ── Regex ─────────────────────────────────────────────────────────────────────
_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)

# ── Available models ──────────────────────────────────────────────────────────
MODELS: dict[str, dict[str, str]] = {
    "openai": {
        "default": "gpt-4o-mini",
        "fast":    "gpt-4o-mini",
        "smart":   "gpt-4o",
    },
    "groq": {
        "default": "qwen/qwen3-32b",
        "fast":    "meta-llama/llama-3.3-70b-versatile",
        "smart":   "qwen/qwen3-32b",
    },
}

# ── Providers that do NOT support response_format ────────────────────────────
_NO_RESPONSE_FORMAT: frozenset[str] = frozenset({"groq"})

# ── Providers that support thinking disable via extra_body ───────────────────
_SUPPORTS_THINKING_DISABLE: frozenset[str] = frozenset({"groq", "openrouter"})


class ConfigurationError(Exception):
    """Raised when required configuration is missing or invalid."""


# ─────────────────────────────────────────────────────────────────────────────
# Pure helpers
# ─────────────────────────────────────────────────────────────────────────────

def _strip_thinking(text: str) -> str:
    """
    Remove <think>…</think> blocks emitted by Qwen3 and similar models.

    Applied to every text response so callers never see raw reasoning.
    """
    return _THINK_RE.sub("", text).strip()


def _supports_response_format(provider: str) -> bool:
    """Return True if the provider accepts response_format=json_object."""
    return provider.lower() not in _NO_RESPONSE_FORMAT


def _thinking_extra_body(provider: str) -> dict[str, Any]:
    """
    Return extra_body to disable chain-of-thought if the provider supports it.
    Returns {} for providers that don't support the field (avoids 400 errors).
    """
    if provider.lower() in _SUPPORTS_THINKING_DISABLE:
        return {"thinking": {"type": "disabled"}}
    return {}


# ─────────────────────────────────────────────────────────────────────────────
# LLMClients — single object injected into app.state
# ─────────────────────────────────────────────────────────────────────────────

class LLMClients:
    """
    Container for all initialised LLM clients.

    Instantiated once in lifespan() and stored at app.state.llm_clients.
    Never use module-level globals — always inject this object.

    Usage (lifespan):
        app.state.llm_clients = await LLMClients.create()

    Usage (endpoint via Depends):
        def get_llm(request: Request) -> LLMClients:
            return request.app.state.llm_clients
    """

    def __init__(
        self,
        openai_client: AsyncOpenAI | None,
        groq_client: Any | None,          # AsyncGroq | None
        active_provider: str,
    ) -> None:
        self._openai  = openai_client
        self._groq    = groq_client
        self._provider = active_provider.lower()

    # ── Factory ───────────────────────────────────────────────────────────────

    @classmethod
    async def create(cls) -> "LLMClients":
        """
        Build and validate all configured LLM clients.

        Called exactly once from lifespan().
        Raises ConfigurationError on missing keys or unknown provider.
        """
        provider = settings.llm_provider.lower()
        openai_client: AsyncOpenAI | None = None
        groq_client: Any = None

        if provider == "groq":
            if not GROQ_AVAILABLE:
                raise ConfigurationError(
                    "Groq package not installed. Run: pip install groq"
                )
            if not settings.groq_api_key:
                raise ConfigurationError(
                    "GROQ_API_KEY is not set. Add it to your .env file."
                )
            groq_client = AsyncGroq(api_key=settings.groq_api_key)
            logger.info("llm.groq_initialized", model=MODELS["groq"]["default"])

        else:   # openai (default)
            if not settings.openai_api_key:
                raise ConfigurationError(
                    "OPENAI_API_KEY is not set. Add it to your .env file."
                )
            openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
            logger.info("llm.openai_initialized", model=settings.llm_model)

        return cls(openai_client, groq_client, provider)

    # ── Active client ─────────────────────────────────────────────────────────

    @property
    def client(self) -> AsyncOpenAI | Any:
        """Return the active client for the configured provider."""
        if self._provider == "groq":
            return self._groq
        return self._openai

    @property
    def provider(self) -> str:
        return self._provider

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def close(self) -> None:
        """Close all open clients gracefully."""
        if self._openai:
            await self._openai.close()
            logger.info("llm.openai_closed")
        if self._groq and hasattr(self._groq, "close"):
            await self._groq.close()
            logger.info("llm.groq_closed")

    # ── High-level API ────────────────────────────────────────────────────────

    async def generate_text(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """
        Generate a plain-text response.

        - <think> blocks are stripped automatically.
        - temperature=0.0 is handled correctly (not treated as falsy).
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # None → use settings; 0.0 → keep as 0.0 (not falsy)
        _temp   = settings.llm_temperature if temperature is None else temperature
        _tokens = settings.llm_max_tokens  if max_tokens  is None else max_tokens

        try:
            response = await self.client.chat.completions.create(
                model=settings.llm_model,
                messages=messages,
                temperature=_temp,
                max_tokens=_tokens,
                **(_thinking_extra_body(self._provider)),
            )
        except Exception as e:
            logger.error("llm.generate_text_error", error=str(e), exc_info=True)
            raise

        return _strip_thinking(response.choices[0].message.content)

    async def generate_json(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> dict:
        """
        Generate a JSON response and parse it.

        - response_format=json_object used only for providers that support it.
        - Groq (and other unsupported providers) rely on prompt-level JSON
          instruction instead.
        - <think> blocks stripped before JSON parsing.
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        else:
            # Fallback system prompt when none provided — ensures JSON output
            messages.append({
                "role": "system",
                "content": "Respond with valid JSON only. No explanation.",
            })
        messages.append({"role": "user", "content": prompt})

        kwargs: dict[str, Any] = {
            "model":       settings.llm_model,
            "messages":    messages,
            "temperature": 0.0,
            "max_tokens":  settings.llm_max_tokens,
        }

        # Only add response_format for providers that support it
        if _supports_response_format(self._provider):
            kwargs["response_format"] = {"type": "json_object"}

        # Disable thinking where supported
        kwargs.update(_thinking_extra_body(self._provider))

        try:
            response = await self.client.chat.completions.create(**kwargs)
        except Exception as e:
            logger.error("llm.generate_json_error", error=str(e), exc_info=True)
            raise

        content = _strip_thinking(response.choices[0].message.content)

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error("llm.json_decode_error", raw=content[:200], error=str(e))
            raise ValueError(f"LLM returned invalid JSON: {e}") from e


# ─────────────────────────────────────────────────────────────────────────────
# Backwards-compatible module-level helpers
# (for code that still calls generate_text() directly — migrate gradually)
# ─────────────────────────────────────────────────────────────────────────────

_legacy_clients: LLMClients | None = None
_legacy_lock:    asyncio.Lock | None = None


def _get_legacy_lock() -> asyncio.Lock:
    """Create lock lazily inside the running event loop."""
    global _legacy_lock
    if _legacy_lock is None:
        _legacy_lock = asyncio.Lock()
    return _legacy_lock


async def _get_legacy_clients() -> LLMClients:
    """Lazy singleton for legacy callers. Prefer LLMClients.create() in lifespan."""
    global _legacy_clients
    if _legacy_clients is None:
        async with _get_legacy_lock():
            if _legacy_clients is None:
                _legacy_clients = await LLMClients.create()
    return _legacy_clients


async def init_llm() -> None:
    """Initialise the legacy LLM singleton (called from lifespan if not using LLMClients)."""
    clients = await _get_legacy_clients()
    logger.info(
        "llm.ready",
        provider=clients.provider,
        model=settings.llm_model,
        temperature=settings.llm_temperature,
    )


async def close_llm() -> None:
    """Close the legacy LLM singleton."""
    global _legacy_clients
    if _legacy_clients:
        await _legacy_clients.close()
        _legacy_clients = None


async def generate_text(
    prompt: str,
    system_prompt: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> str:
    """Legacy module-level generate_text. Prefer LLMClients.generate_text()."""
    clients = await _get_legacy_clients()
    return await clients.generate_text(
        prompt, system_prompt, temperature, max_tokens
    )


async def generate_json(
    prompt: str,
    system_prompt: str | None = None,
) -> dict:
    """Legacy module-level generate_json. Prefer LLMClients.generate_json()."""
    clients = await _get_legacy_clients()
    return await clients.generate_json(prompt, system_prompt)


# Keep get_llm_client() for code that calls it directly
async def get_llm_client() -> Any:
    """Legacy: return the active raw client. Prefer injecting LLMClients."""
    return (await _get_legacy_clients()).client