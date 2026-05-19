"""
TCGIS - API Gateway
FastAPI-based REST API with authentication, rate limiting, and logging
"""

import os
import time
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request, Response, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from shared.clients.postgres_client import init_db, close_db
from shared.clients.redis_client import redis_client
from shared.clients.elasticsearch_client import es_client

from api_gateway.routers.v1 import groups, countries, search, analytics
from api_gateway.routers import health
from api_gateway.middleware import auth, rate_limit, logging as logging_middleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """إدارة دورة حياة التطبيق"""
    # Startup
    await redis_client.connect()
    await es_client.connect()
    await init_db()
    print("🚀 API Gateway started successfully")
    
    yield
    
    # Shutdown
    await close_db()
    await redis_client.disconnect()
    await es_client.disconnect()
    print("🛑 API Gateway stopped")


# إنشاء التطبيق
app = FastAPI(
    title="TCGIS API",
    description="Telegram Country Group Indexing System - REST API",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Routers
app.include_router(health.router, tags=["Health"])
app.include_router(
    groups.router, 
    prefix="/api/v1/groups", 
    tags=["Groups"],
    dependencies=[Depends(auth.get_current_user_optional)]
)
app.include_router(
    countries.router, 
    prefix="/api/v1/countries", 
    tags=["Countries"]
)
app.include_router(
    search.router, 
    prefix="/api/v1/search", 
    tags=["Search"],
    dependencies=[Depends(rate_limit.rate_limit_dependency)]
)
app.include_router(
    analytics.router, 
    prefix="/api/v1/analytics", 
    tags=["Analytics"],
    dependencies=[Depends(auth.require_api_key)]
)


@app.middleware("http")
async def logging_middleware_func(request: Request, call_next):
    """Middleware لتسجيل الطلبات"""
    start_time = time.time()
    
    # تسجيل الطلب
    logging_middleware.log_request(request)
    
    response = await call_next(request)
    
    # تسجيل الاستجابة
    duration = time.time() - start_time
    logging_middleware.log_response(request, response, duration)
    
    # إضافة headers
    response.headers["X-Response-Time"] = str(duration)
    response.headers["X-API-Version"] = "2.0.0"
    
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """معالجة الاستثناءات"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url)
        }
    )


@app.get("/")
async def root():
    """الصفحة الرئيسية"""
    return {
        "name": "TCGIS API",
        "version": "2.0.0",
        "description": "Telegram Country Group Indexing System",
        "documentation": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api_gateway.main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
        workers=int(os.getenv("API_WORKERS", 4)),
        reload=os.getenv("ENV") == "development"
    )
