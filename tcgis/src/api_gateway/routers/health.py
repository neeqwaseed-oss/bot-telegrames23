"""
TCGIS - Health Check Router
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from shared.clients.postgres_client import get_db
from shared.clients.redis_client import redis_client
from shared.clients.elasticsearch_client import es_client


router = APIRouter()


@router.get("/health")
async def health_check():
    """فحص صحة النظام"""
    return {
        "status": "healthy",
        "service": "tcgis-api-gateway",
        "version": "2.0.0",
        "timestamp": ""
    }


@router.get("/health/detailed")
async def detailed_health_check():
    """فحص صحة مفصل لجميع الخدمات"""
    checks = {
        "api_gateway": {"status": "healthy"},
        "database": {"status": "unknown"},
        "redis": {"status": "unknown"},
        "elasticsearch": {"status": "unknown"}
    }
    
    # فحص PostgreSQL
    try:
        from sqlalchemy import text
        async with get_db() as db:
            result = await db.execute(text("SELECT 1"))
            checks["database"] = {"status": "healthy"}
    except Exception as e:
        checks["database"] = {"status": "unhealthy", "error": str(e)}
    
    # فحص Redis
    try:
        await redis_client._client.ping()
        checks["redis"] = {"status": "healthy"}
    except Exception as e:
        checks["redis"] = {"status": "unhealthy", "error": str(e)}
    
    # فحص Elasticsearch
    try:
        await es_client.client.ping()
        checks["elasticsearch"] = {"status": "healthy"}
    except Exception as e:
        checks["elasticsearch"] = {"status": "unhealthy", "error": str(e)}
    
    overall = "healthy" if all(
        c["status"] == "healthy" for c in checks.values()
    ) else "degraded"
    
    return {
        "status": overall,
        "checks": checks
    }
