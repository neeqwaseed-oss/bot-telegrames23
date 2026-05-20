"""
TCGIS - Search API Router
"""

from typing import Optional
from fastapi import APIRouter, Query

from shared.clients.elasticsearch_client import es_client
from shared.utils.validators import sanitize_query


router = APIRouter()


@router.get("/")
async def search(
    q: str = Query(..., min_length=1, max_length=200, description="Search query"),
    country_code: Optional[str] = Query(None, description="Filter by country code"),
    category: Optional[str] = Query(None, description="Filter by category"),
    language: Optional[str] = Query(None, description="Filter by language"),
    min_members: Optional[int] = Query(None, ge=0),
    max_members: Optional[int] = Query(None, ge=0),
    min_quality: Optional[int] = Query(None, ge=0, le=100),
    is_verified: Optional[bool] = Query(None),
    sort_by: str = Query("relevance", enum=["relevance", "members", "quality", "activity", "newest"]),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    """البحث المتقدم في المجموعات"""
    # تنظيف الاستعلام
    query = sanitize_query(q)
    
    if not query:
        return {"results": [], "total": 0, "message": "Empty query after sanitization"}
    
    # بناء الفلاتر
    filters = {}
    if country_code:
        filters["country_code"] = country_code.upper()
    if category:
        filters["category"] = category
    if language:
        filters["language"] = language
    if min_members is not None:
        filters["min_members"] = min_members
    if max_members is not None:
        filters["max_members"] = max_members
    if min_quality is not None:
        filters["min_quality"] = min_quality
    if is_verified is not None:
        filters["is_verified"] = is_verified
    
    results = await es_client.search_groups(
        query=query,
        filters=filters if filters else None,
        sort_by=sort_by,
        page=page,
        per_page=per_page
    )
    
    return {
        "query": query,
        **results
    }


@router.get("/autocomplete")
async def autocomplete(
    q: str = Query(..., min_length=1, max_length=100),
    size: int = Query(10, ge=1, le=20)
):
    """الإكمال التلقائي للبحث"""
    prefix = sanitize_query(q)
    suggestions = await es_client.autocomplete(prefix, size)
    return {
        "query": prefix,
        "suggestions": suggestions
    }


@router.get("/trending")
async def trending_searches():
    """البحثات الشائعة"""
    # TODO: تتبع البحثات الشائعة في Redis
    return {
        "trending": [
            {"query": "تسويق", "count": 1250},
            {"query": "برمجة", "count": 980},
            {"query": "تعليم", "count": 850},
            {"query": "أخبار", "count": 720},
            {"query": "رياضة", "count": 690},
        ]
    }
