"""
TCGIS - PostgreSQL Database Client
Async database connection manager
"""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession, 
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.orm import sessionmaker

from shared.models.database_models import Base


# إعدادات الاتصال
DATABASE_URL = os.getenv(
    'DATABASE_URL', 
    'postgresql+asyncpg://tcgis_user:tcgis_password@localhost:5432/tcgis'
)

# تصحيح الرابط للعمل مع المحرك غير المتزامن (ضروري لـ Render)
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# إنشاء المحرك
engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv('DEBUG', 'false').lower() == 'true',
    pool_size=int(os.getenv('DB_POOL_SIZE', 20)),
    max_overflow=int(os.getenv('DB_MAX_OVERFLOW', 10)),
    pool_pre_ping=True,
    pool_recycle=3600,
)

# إنشاء session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


async def init_db():
    """تهيئة قاعدة البيانات - إنشاء الجداول"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database initialized successfully")


async def close_db():
    """إغلاق الاتصال بقاعدة البيانات"""
    await engine.dispose()
    print("✅ Database connection closed")


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Context manager للحصول على session"""
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        raise e
    finally:
        await session.close()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency للـ FastAPI"""
    async with get_db_session() as session:
        yield session
