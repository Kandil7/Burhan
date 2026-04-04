"""
Health check routes for Athar Islamic QA system.

Provides endpoints for monitoring service health and readiness.
"""
from fastapi import APIRouter
from src.api.schemas.response import HealthResponse
from src.config.settings import settings

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Basic health check endpoint.
    
    Returns 200 OK if the service is running.
    Used by load balancers and monitoring systems.
    """
    return HealthResponse(
        status="ok",
        version="0.1.0",
        services={
            "api": "healthy",
        }
    )


@router.get("/ready", response_model=HealthResponse)
async def readiness_check():
    """
    Readiness probe endpoint.
    
    Returns 200 OK when all dependencies are connected.
    Used by Kubernetes to determine if pod is ready for traffic.
    
    Phase 1: Basic check
    Phase 2+: Check PostgreSQL, Redis, Qdrant connections
    """
    # Phase 1: Always ready if API is running
    # Phase 2: Will check database, redis, qdrant connections
    services = {
        "api": "healthy",
        "postgres": "not_implemented",  # TODO: Check connection
        "redis": "not_implemented",  # TODO: Check connection
        "qdrant": "not_implemented",  # TODO: Check connection
    }
    
    return HealthResponse(
        status="ok",
        version="0.1.0",
        services=services
    )
