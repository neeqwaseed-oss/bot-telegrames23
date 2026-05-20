"""
TCGIS - Countries API Router
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from shared.clients.postgres_client import get_db
from shared.models.database_models import Country, Group


router = APIRouter()


@router.get("/")
async def list_countries(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """قائمة الدول"""
    query = select(Country)
    if active_only:
        query = query.where(Country.is_active == True)
    query = query.order_by(Country.name_en)
    
    result = await db.execute(query)
    countries = result.scalars().all()
    
    return {
        "countries": [
            {
                "id": c.id,
                "code": c.code,
                "name_en": c.name_en,
                "name_ar": c.name_ar,
                "name_local": c.name_local,
                "region": c.region,
                "flag": get_flag_emoji(c.code),
                "total_groups": c.total_groups,
                "total_channels": c.total_channels,
                "is_active": c.is_active
            }
            for c in countries
        ],
        "total": len(countries)
    }


@router.get("/{country_code}")
async def get_country(
    country_code: str,
    db: AsyncSession = Depends(get_db)
):
    """الحصول على تفاصيل دولة"""
    result = await db.execute(
        select(Country).where(Country.code == country_code.upper())
    )
    country = result.scalar_one_or_none()
    
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    
    return {
        "id": country.id,
        "code": country.code,
        "name_en": country.name_en,
        "name_ar": country.name_ar,
        "name_local": country.name_local,
        "region": country.region,
        "flag": get_flag_emoji(country.code),
        "language_primary": country.language_primary,
        "timezone": country.timezone,
        "total_groups": country.total_groups,
        "total_channels": country.total_channels
    }


@router.get("/{country_code}/groups")
async def get_country_groups(
    country_code: str,
    page: int = 1,
    per_page: int = 20,
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """الحصول على مجموعات دولة معينة"""
    from shared.clients.elasticsearch_client import es_client
    
    filters = {"country_code": country_code.upper(), "status": "active"}
    if category:
        filters["category"] = category
    
    results = await es_client.search_groups(
        query="",
        filters=filters,
        sort_by="members",
        page=page,
        per_page=per_page
    )
    
    return results


def get_flag_emoji(country_code: str) -> str:
    """تحويل رمز الدولة إلى إيموجي علم"""
    flags = {
        'SA': '🇸🇦', 'AE': '🇦🇪', 'EG': '🇪🇬', 'KW': '🇰🇼',
        'QA': '🇶🇦', 'BH': '🇧🇭', 'OM': '🇴🇲', 'JO': '🇯🇴',
        'LB': '🇱🇧', 'IQ': '🇮🇶', 'DZ': '🇩🇿', 'MA': '🇲🇦',
        'TN': '🇹🇳', 'LY': '🇱🇾', 'SD': '🇸🇩', 'YE': '🇾🇪',
        'SY': '🇸🇾', 'PS': '🇵🇸'
    }
    return flags.get(country_code.upper(), '🌍')
