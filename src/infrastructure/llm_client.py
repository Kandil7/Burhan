"""
LLM client abstraction for Athar Islamic QA system.

Provides unified interface for multiple LLM providers (OpenAI, Azure, local).
"""
from typing import Optional
from openai import AsyncOpenAI

from src.config.settings import settings
from src.config.logging_config import get_logger

logger = get_logger()

# Global LLM client
llm_client: Optional[AsyncOpenAI] = None


async def get_llm_client() -> AsyncOpenAI:
    """
    Get or create LLM client instance.
    
    Phase 1: OpenAI client
    Phase 2+: Support multiple providers (Azure, local models, etc.)
    
    Usage:
        client = await get_llm_client()
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello"}]
        )
    """
    global llm_client
    
    if llm_client is None:
        if not settings.openai_api_key:
            logger.warning("llm.no_api_key", provider=settings.llm_provider)
            # Phase 1: Allow running without LLM (for testing)
            # Phase 2: Raise error in production
        
        llm_client = AsyncOpenAI(
            api_key=settings.openai_api_key or "sk-dummy-key-for-testing",
            base_url=None,  # Use OpenAI default
        )
        
        logger.info(
            "llm.client_initialized",
            provider=settings.llm_provider,
            model=settings.openai_model
        )
    
    return llm_client


async def init_llm():
    """
    Initialize LLM client.
    
    Phase 1: Just create client
    Phase 2+: Verify API key, test connection
    """
    try:
        client = await get_llm_client()
        logger.info(
            "llm.ready",
            provider=settings.llm_provider,
            model=settings.openai_model,
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
    system_prompt: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
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
            model=settings.openai_model,
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
    system_prompt: Optional[str] = None,
) -> dict:
    """
    Generate JSON response using LLM.
    
    Args:
        prompt: User prompt
        system_prompt: Optional system prompt
        
    Returns:
        Parsed JSON response
    """
    import json
    
    try:
        client = await get_llm_client()
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = await client.chat.completions.create(
            model=settings.openai_model,
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
