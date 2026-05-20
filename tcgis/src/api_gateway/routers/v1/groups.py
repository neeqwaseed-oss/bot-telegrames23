"""
TCGIS - Groups API Router
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from shared.clients.postgres_client import get_db
from shared.clients.elasticsearch_client import es_client
from shared.models.database_models import Group, Country, Category


router = APIRouter()


@router.get("/")
async def list_groups(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    country_code: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = "active",
    sort_by: str = "newest",
    db: AsyncSession = Depends(get_db)
):
    """قائمة المجموعات مع التصفية والترتيب"""
    query = select(Group)
    
    if status:
        query = query.where(Group.status == status)
    if country_code:
        # الحصول على معرف الدولة
        country_result = await db.execute(
            select(Country).where(Country.code == country_code.upper())
        )
        country = country_result.scalar_one_or_none()
        if country:
            query = query.where(Group.country_id == country.id)
    if category:
        cat_result = await db.execute(
            select(Category).where(Category.slug == category)
        )
        cat = cat_result.scalar_one_or_none()
        if cat:
            query = query.where(Group.category_id == cat.id)
    
    # الترتيب
    if sort_by == "newest":
        query = query.order_by(Group.discovered_at.desc())
    elif sort_by == "members":
        query = query.order_by(Group.member_count.desc())
    elif sort_by == "quality":
        query = query.order_by(Group.quality_score.desc())
    
    # الترقيم الصفحي
    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar()
    
    query = query.offset((page - 1) * per_page).limit(per_page)
    
    result = await db.execute(query)
    groups = result.scalars().all()
    
    return {
        "groups": [g.to_dict() for g in groups],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page
    }


@router.get("/search")
async def search_groups(
    q: str = Query(..., min_length=1),
    country_code: Optional[str] = None,
    category: Optional[str] = None,
    language: Optional[str] = None,
    min_members: Optional[int] = None,
    max_members: Optional[int] = None,
    is_verified: Optional[bool] = None,
    sort_by: str = "relevance",
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    """البحث في المجموعات"""
    filters = {}
    if country_code:
        filters["country_code"] = country_code
    if category:
        filters["category"] = category
    if language:
        filters["language"] = language
    if min_members:
        filters["min_members"] = min_members
    if max_members:
        filters["max_members"] = max_members
    if is_verified is not None:
        filters["is_verified"] = is_verified
    
    results = await es_client.search_groups(
        query=q,
        filters=filters if filters else None,
        sort_by=sort_by,
        page=page,
        per_page=per_page
    )
    
    return results


@router.get("/{group_id}")
async def get_group(
    group_id: int,
    db: AsyncSession = Depends(get_db)
):
    """الحصول على تفاصيل مجموعة"""
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    return group.to_dict()


@router.get("/featured/list")
async def get_featured_groups(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50)
):
    """الحصول على المجموعات المميزة"""
    results = await es_client.search_groups(
        query="",
        filters={"is_featured": True, "status": "active"},
        sort_by="quality",
        page=page,
        per_page=per_page
    )
    return results
