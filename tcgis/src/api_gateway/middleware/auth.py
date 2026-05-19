"""
TCGIS - API Gateway Authentication Middleware
"""

import os
import time
from typing import Optional

from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


# API Key authentication
API_KEY_HEADER = "X-API-Key"
security = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[dict]:
    """التحقق اختياري من المستخدم"""
    api_key = request.headers.get(API_KEY_HEADER)
    
    if api_key:
        # TODO: التحقق من API Key في قاعدة البيانات
        return {"api_key": api_key, "tier": "free"}
    
    return None


async def require_api_key(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> dict:
    """التحقق الإلزامي من API Key"""
    api_key = request.headers.get(API_KEY_HEADER)
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # TODO: التحقق من صحة API Key
    return {"api_key": api_key, "tier": "premium"}


async def optional_auth(
    request: Request
) -> Optional[dict]:
    """مصادقة اختيارية"""
    api_key = request.headers.get(API_KEY_HEADER)
    if api_key:
        return {"api_key": api_key}
    return None
