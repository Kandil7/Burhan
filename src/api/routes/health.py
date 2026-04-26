"""
Health check routes for Burhan Islamic QA system.

Provides endpoints for monitoring service health and readiness.
Phase 9: Added metrics endpoint.
"""

from fastapi import APIRouter, Response

from src.api.schemas.common import HealthResponse
from src.config.settings import settings
from src.config.logging_config import metrics

router = APIRouter(tags=["Health"])


async def check_postgres() -> str:
    """Check PostgreSQL connection."""
    try:
        import asyncpg

        db_url = settings.database_url.replace("+asyncpg", "")
        conn = await asyncpg.connect(db_url, timeout=5)
        await conn.execute("SELECT 1")
        await conn.close()
        return "healthy"
    except Exception as e:
        return f"error: {str(e)[:50]}"


async def check_redis() -> str:
    """Check Redis connection."""
    try:
        import redis.asyncio as redis

        r = redis.from_url(settings.redis_url)
        await r.ping()
        await r.close()
        return "healthy"
    except Exception as e:
        return f"error: {str(e)[:50]}"


async def check_qdrant() -> str:
    """Check Qdrant connection."""
    try:
        from qdrant_client import QdrantClient

        client = QdrantClient(url=settings.qdrant_url)
        collections = client.get_collections()
        return f"healthy ({len(collections.collections)} collections)"
    except Exception as e:
        return f"error: {str(e)[:50]}"


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Basic health check endpoint.
    Returns 200 OK if the API service is running.
    """
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        services={
            "api": "healthy",
        },
    )


@router.get("/ready", response_model=HealthResponse)
async def readiness_check():
    """
    Readiness probe - checks all service connections.
    Returns status of PostgreSQL, Redis, and Qdrant.
    """
    postgres = await check_postgres()
    redis = await check_redis()
    qdrant = await check_qdrant()

    services = {
        "api": "healthy",
        "postgres": postgres,
        "redis": redis,
        "qdrant": qdrant,
    }

    # Determine overall status
    all_healthy = all("healthy" in v for v in services.values())

    return HealthResponse(status="ok" if all_healthy else "degraded", version=settings.app_version, services=services)


@router.get("/metrics")
async def get_metrics():
    """
    Metrics endpoint for monitoring.

    Returns:
        - counters: Request counts by endpoint
        - gauges: Current state values
        - timings: Recent operation timings
    """
    return metrics.get_metrics()


@router.get("/metrics/counters")
async def get_counters():
    """Get counter metrics only."""
    return metrics.get_metrics()["counters"]


@router.get("/metrics/timings")
async def get_timings():
    """Get timing metrics only."""
    return metrics.get_metrics()["timings"]


@router.get("/metrics/reset", status_code=204)
async def reset_metrics():
    """Reset all metrics."""
    metrics.reset()
    return None
