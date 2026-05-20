"""
TCGIS - Deduplication Processor
Remove duplicate groups based on various criteria
"""

import logging
from typing import List, Set, Dict, Any
from sqlalchemy import select

from shared.models.database_models import Group


logger = logging.getLogger(__name__)


class DeduplicationProcessor:
    """معالج إزالة التكرار"""
    
    @staticmethod
    async def find_duplicates(session) -> List[List[Group]]:
        """البحث عن مجموعات مكررة"""
        duplicates = []
        
        # البحث حسب اسم المستخدم
        result = await session.execute(
            select(Group).where(Group.username.isnot(None))
        )
        groups = result.scalars().all()
        
        username_groups: Dict[str, List[Group]] = {}
        for group in groups:
            if group.username:
                username = group.username.lower()
                if username not in username_groups:
                    username_groups[username] = []
                username_groups[username].append(group)
        
        for username, group_list in username_groups.items():
            if len(group_list) > 1:
                duplicates.append(group_list)
        
        return duplicates
    
    @staticmethod
    async def merge_duplicates(session, duplicate_groups: List[List[Group]]) -> int:
        """دمج المجموعات المكررة"""
        merged_count = 0
        
        for group_list in duplicate_groups:
            # الاحتفاظ بالأقدم أو الأكثر اكتمالاً
            primary = max(group_list, key=lambda g: (
                bool(g.title) + bool(g.description) + bool(g.member_count),
                g.created_at or 0
            ))
            
            for duplicate in group_list:
                if duplicate.id == primary.id:
                    continue
                
                # نقل البيانات المفقودة
                if not primary.description and duplicate.description:
                    primary.description = duplicate.description
                if not primary.member_count and duplicate.member_count:
                    primary.member_count = duplicate.member_count
                if not primary.invite_link and duplicate.invite_link:
                    primary.invite_link = duplicate.invite_link
                
                # حذف المكرر
                await session.delete(duplicate)
                merged_count += 1
        
        return merged_count
    
    @staticmethod
    def deduplicate_scraped(groups: List[Any]) -> List[Any]:
        """إزالة التكرار من النتائج المجمعة"""
        seen_usernames: Set[str] = set()
        seen_links: Set[str] = set()
        unique = []
        
        for group in groups:
            key = group.username or group.invite_link
            if not key:
                unique.append(group)
                continue
            
            key_lower = key.lower()
            if key_lower not in seen_usernames and key_lower not in seen_links:
                seen_usernames.add(key_lower)
                if group.invite_link:
                    seen_links.add(group.invite_link.lower())
                unique.append(group)
        
        return unique
