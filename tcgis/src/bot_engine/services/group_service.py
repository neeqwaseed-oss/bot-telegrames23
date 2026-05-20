"""
TCGIS - Group Service
Business logic for group operations
"""

from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.database_models import Group, Country, Category
from shared.clients.elasticsearch_client import es_client


class GroupService:
    """خدمة المجموعات"""
    
    @staticmethod
    async def search_groups(
        query: str,
        country_code: Optional[str] = None,
        category: Optional[str] = None,
        page: int = 1,
        per_page: int = 10
    ) -> dict:
        """البحث عن مجموعات"""
        filters = {}
        if country_code:
            filters["country_code"] = country_code.upper()
        if category:
            filters["category"] = category
        
        results = await es_client.search_groups(
            query=query,
            filters=filters if filters else None,
            page=page,
            per_page=per_page
        )
        
        return results
    
    @staticmethod
    async def get_country_groups(
        country_code: str,
        page: int = 1,
        per_page: int = 15
    ) -> dict:
        """الحصول على مجموعات دولة"""
        results = await es_client.search_groups(
            query="",
            filters={"country_code": country_code.upper(), "status": "active"},
            sort_by="members",
            page=page,
            per_page=per_page
        )
        
        return results
    
    @staticmethod
    async def get_featured_groups(per_page: int = 10) -> dict:
        """الحصول على المجموعات المميزة"""
        results = await es_client.search_groups(
            query="",
            filters={"is_featured": True, "status": "active"},
            sort_by="quality",
            page=1,
            per_page=per_page
        )
        
        return results
    
    @staticmethod
    async def get_group_stats() -> dict:
        """الحصول على إحصائيات المجموعات"""
        es_stats = await es_client.get_stats()
        
        return {
            "total_indexed": es_stats.get("total_docs", 0),
            "index_size_mb": round(es_stats.get("size_in_bytes", 0) / (1024 * 1024), 2)
        }
