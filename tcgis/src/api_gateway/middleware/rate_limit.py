"""
TCGIS - Rate Limiting Middleware
"""

import os
from fastapi import Request, HTTPException, status, Depends

from shared.clients.redis_client import redis_client


# إعدادات Rate Limit
RATE_LIMIT_REQUESTS = int(os.getenv('RATE_LIMIT_REQUESTS', 100))
RATE_LIMIT_WINDOW = int(os.getenv('RATE_LIMIT_WINDOW', 60))


async def rate_limit_dependency(request: Request):
    """Dependency للتحقق من Rate Limit"""
    client_ip = request.client.host
    key = f"rate_limit:{client_ip}:{request.url.path}"
    
    allowed, remaining = await redis_client.check_rate_limit(
        key,
        RATE_LIMIT_REQUESTS,
        RATE_LIMIT_WINDOW
    )
    
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
            headers={"Retry-After": str(RATE_LIMIT_WINDOW)}
        )
    
    return {"remaining": remaining}


async def check_rate_limit(request: Request) -> bool:
    """التحقق من Rate Limit"""
    client_ip = request.client.host
    key = f"rate_limit:{client_ip}:{request.url.path}"
    
    allowed, _ = await redis_client.check_rate_limit(
        key,
        RATE_LIMIT_REQUESTS,
        RATE_LIMIT_WINDOW
    )
    
    return allowed
