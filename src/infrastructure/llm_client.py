"""
LLM client abstraction for Athar Islamic QA system.

Provides unified interface for multiple LLM providers:
- OpenAI (GPT-4o-mini, GPT-4)
- Groq (Qwen3-32B, Llama 3.3 70B, Mixtral 8x7B)
- Local models (future)

Phase 4: Added Groq support for faster, cheaper inference.
Phase 6 Refactoring: Added asyncio.Lock for thread-safe client creation.
"""
import asyncio
import json

from openai import AsyncOpenAI


class ConfigurationError(Exception):
    """Raised when required configuration is missing."""
    pass

try:
    from groq import AsyncGroq
    GROQ_AVAILABLE = True
except ImportError:
    AsyncGroq = None
    GROQ_AVAILABLE = False

from src.config.logging_config import get_logger
from src.config.settings import settings

logger = get_logger()

# Global LLM clients with thread-safe locks
llm_client: AsyncOpenAI | None = None
groq_client: AsyncGroq | None = None
_client_lock: asyncio.Lock = asyncio.Lock()
_openai_lock: asyncio.Lock = asyncio.Lock()


# Available models per provider
MODELS = {
    "openai": {
        "default": "gpt-4o-mini",
        "fast": "gpt-4o-mini",
        "smart": "gpt-4o",
    },
    "groq": {
        "default": "qwen/qwen3-32b",
        "fast": "meta-llama/llama-3.3-70b-versatile",
        "smart": "qwen/qwen3-32b",
    }
}


async def get_llm_client() -> AsyncOpenAI:
    """
    Get or create LLM client instance.

    Phase 6 Refactoring: Uses asyncio.Lock for thread-safe creation.

    Supports multiple providers:
    - openai: OpenAI API (GPT-4o-mini, GPT-4)
    - groq: Groq API (Qwen3-32B, Llama 3.3 70B)

    Usage:
        client = await get_llm_client()
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello"}]
        )
    """
    global llm_client, groq_client

    provider = settings.llm_provider.lower()

    if provider == "groq":
        if not GROQ_AVAILABLE:
            logger.error("llm.groq_not_installed")
            raise ConfigurationError(
                "Groq package not installed. Run: pip install groq"
            )

        if groq_client is None:
            async with _client_lock:
                # Double-checked locking
                if groq_client is None:
                    if not settings.groq_api_key:
                        logger.error("llm.no_groq_key")
                        raise ConfigurationError(
                            "GROQ_API_KEY environment variable is not set. "
                            "Please set it in your .env file or environment."
                        )

                    groq_client = AsyncGroq(api_key=settings.groq_api_key)
                    logger.info(
                        "llm.groq_initialized",
                        model=MODELS["groq"]["default"]
                    )
        return groq_client
    else:
        return await get_openai_client()


async def get_openai_client() -> AsyncOpenAI:
    """
    Get OpenAI client.

    Phase 6 Refactoring: Uses asyncio.Lock for thread-safe creation.
    """
    global llm_client

    if llm_client is None:
        async with _openai_lock:
            # Double-checked locking
            if llm_client is None:
                if not settings.openai_api_key:
                    logger.error("llm.no_openai_key", provider="openai")
                    raise ConfigurationError(
                        "OPENAI_API_KEY environment variable is not set. "
                        "Please set it in your .env file or environment."
                    )
                else:
                    llm_client = AsyncOpenAI(api_key=settings.openai_api_key)

                logger.info(
                    "llm.openai_initialized",
                    model=settings.llm_model
                )

    return llm_client


async def init_llm():
    """
    Initialize LLM client.

    Phase 1: Just create client
    Phase 2+: Verify API key, test connection
    """
    try:
        await get_llm_client()
        logger.info(
            "llm.ready",
            provider=settings.llm_provider,
            model=settings.llm_model,
            temperature=settings.llm_temperature
        )
    except Exception as e:
        logger.error("llm.initialization_error", error=str(e))
        raise


async def close_llm():
    """Close LLM client."""
    global llm_client
    if llm_client:
        await llm_client.close()
        llm_client = None
        logger.info("llm.closed")


async def generate_text(
    prompt: str,
    system_prompt: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> str:
    """
    Generate text using LLM.

    Args:
        prompt: User prompt
        system_prompt: Optional system prompt
        temperature: Override temperature (default: from settings)
        max_tokens: Override max tokens (default: from settings)

    Returns:
        Generated text response
    """
    try:
        client = await get_llm_client()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await client.chat.completions.create(
            model=settings.llm_model,
            messages=messages,
            temperature=temperature or settings.llm_temperature,
            max_tokens=max_tokens or settings.llm_max_tokens,
        )

        return response.choices[0].message.content

    except Exception as e:
        logger.error("llm.generate_error", error=str(e))
        raise


async def generate_json(
    prompt: str,
    system_prompt: str | None = None,
) -> dict:
    """
    Generate JSON response using LLM.

    Phase 6 Refactoring: Moved json import to module level.

    Args:
        prompt: User prompt
        system_prompt: Optional system prompt

    Returns:
        Parsed JSON response
    """
    try:
        client = await get_llm_client()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await client.chat.completions.create(
            model=settings.llm_model,
            messages=messages,
            temperature=0.0,  # Deterministic
            max_tokens=settings.llm_max_tokens,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content
        return json.loads(content)

    except json.JSONDecodeError as e:
        logger.error("llm.json_decode_error", error=str(e))
        raise ValueError(f"LLM returned invalid JSON: {e}")
    except Exception as e:
        logger.error("llm.generate_error", error=str(e))
        raise
