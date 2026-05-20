"""
TCGIS - Analytics API Router
"""

from typing import Optional
from fastapi import APIRouter, Query, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from shared.clients.postgres_client import get_db
from shared.clients.elasticsearch_client import es_client
from shared.models.database_models import AnalyticsDaily, Group, Country


router = APIRouter()


@router.get("/overview")
async def get_overview_analytics(
    db: AsyncSession = Depends(get_db)
):
    """نظرة عامة على التحليلات"""
    # إجمالي المجموعات
    groups_result = await db.execute(select(func.count(Group.id)))
    total_groups = groups_result.scalar()
    
    # المجموعات النشطة
    active_result = await db.execute(
        select(func.count(Group.id)).where(Group.status == 'active')
    )
    active_groups = active_result.scalar()
    
    # إجمالي الدول
    countries_result = await db.execute(
        select(func.count(Country.id)).where(Country.is_active == True)
    )
    total_countries = countries_result.scalar()
    
    # إحصائيات Elasticsearch
    es_stats = await es_client.get_stats()
    
    return {
        "total_groups": total_groups,
        "active_groups": active_groups,
        "total_countries": total_countries,
        "indexed_groups": es_stats.get("total_docs", 0),
        "index_size_mb": round(es_stats.get("size_in_bytes", 0) / (1024 * 1024), 2),
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/daily")
async def get_daily_analytics(
    days: int = Query(30, ge=1, le=365),
    country_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """التحليلات اليومية"""
    from_date = datetime.utcnow() - timedelta(days=days)
    
    query = select(AnalyticsDaily).where(AnalyticsDaily.date >= from_date)
    if country_id:
        query = query.where(AnalyticsDaily.country_id == country_id)
    query = query.order_by(AnalyticsDaily.date.desc())
    
    result = await db.execute(query)
    analytics = result.scalars().all()
    
    return {
        "period_days": days,
        "data": [
            {
                "date": a.date.isoformat(),
                "new_groups": a.new_groups,
                "verified_groups": a.verified_groups,
                "deleted_groups": a.deleted_groups,
                "total_searches": a.total_searches,
                "total_clicks": a.total_clicks,
                "active_users": a.active_users,
                "new_users": a.new_users
            }
            for a in analytics
        ]
    }


@router.get("/countries")
async def get_countries_analytics(
    db: AsyncSession = Depends(get_db)
):
    """تحليلات حسب الدولة"""
    query = select(Country).where(Country.is_active == True).order_by(Country.total_groups.desc())
    result = await db.execute(query)
    countries = result.scalars().all()
    
    return {
        "countries": [
            {
                "code": c.code,
                "name_en": c.name_en,
                "name_ar": c.name_ar,
                "total_groups": c.total_groups,
                "total_channels": c.total_channels
            }
            for c in countries
        ]
    }


@router.get("/categories")
async def get_categories_analytics():
    """تحليلات حسب الفئة"""
    # البحث في Elasticsearch عن توزيع الفئات
    results = await es_client.search_groups(
        query="",
        filters={"status": "active"},
        page=1,
        per_page=1
    )
    
    categories = results.get("aggregations", {}).get("by_category", {}).get("buckets", [])
    
    return {
        "categories": [
            {"name": c["key"], "count": c["doc_count"]}
            for c in categories
        ]
    }
