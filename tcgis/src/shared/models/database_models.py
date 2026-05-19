"""
TCGIS - Telegram Country Group Indexing System
Database Models using SQLAlchemy
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, Boolean, 
    DateTime, ForeignKey, DECIMAL, 
    CheckConstraint, Index, func
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects.postgresql import TSVECTOR, ARRAY, JSONB

Base = declarative_base()


class Country(Base):
    """جدول الدول"""
    __tablename__ = 'countries'
    
    id = Column(Integer, primary_key=True)
    code = Column(String(10), unique=True, nullable=False, index=True)
    name_en = Column(String(100), nullable=False)
    name_ar = Column(String(100))
    name_local = Column(String(100))
    region = Column(String(50), index=True)
    language_primary = Column(String(50))
    language_secondary = Column(ARRAY(String(50)))
    timezone = Column(String(50))
    is_active = Column(Boolean, default=True, index=True)
    total_groups = Column(Integer, default=0)
    total_channels = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات
    groups = relationship("Group", back_populates="country")
    
    def __repr__(self):
        return f"<Country(code='{self.code}', name='{self.name_en}')>"


class Category(Base):
    """جدول الفئات"""
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True)
    name_en = Column(String(100), nullable=False)
    name_ar = Column(String(100))
    slug = Column(String(100), unique=True, nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey('categories.id'), nullable=True)
    description = Column(Text)
    icon = Column(String(255))
    color = Column(String(7))
    total_groups = Column(Integer, default=0)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # العلاقات
    parent = relationship("Category", remote_side=[id], backref="children")
    groups = relationship("Group", back_populates="category")
    
    def __repr__(self):
        return f"<Category(slug='{self.slug}', name='{self.name_en}')>"


class Source(Base):
    """جدول المصادر"""
    __tablename__ = 'sources'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    url = Column(String(255))
    type = Column(String(50))  # directory, search_engine, social_media, api
    reliability_score = Column(Integer, CheckConstraint('reliability_score BETWEEN 1 AND 10'))
    rate_limit_requests = Column(Integer, default=100)
    rate_limit_window = Column(Integer, default=60)
    is_active = Column(Boolean, default=True)
    last_scraped_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # العلاقات
    groups = relationship("Group", back_populates="source")
    
    def __repr__(self):
        return f"<Source(name='{self.name}', type='{self.type}')>"


class Group(Base):
    """جدول المجموعات الرئيسي"""
    __tablename__ = 'groups'
    
    id = Column(BigInteger, primary_key=True)
    
    # معلومات Telegram
    telegram_id = Column(BigInteger, unique=True, nullable=True)
    username = Column(String(255), unique=True, nullable=True, index=True)
    invite_link = Column(String(255), unique=True, nullable=True, index=True)
    link_type = Column(String(20), CheckConstraint("link_type IN ('public', 'private')"))
    
    # المحتوى
    title = Column(String(255), nullable=False)
    title_ar = Column(String(255))
    description = Column(Text)
    description_ar = Column(Text)
    
    # التصنيف
    country_id = Column(Integer, ForeignKey('countries.id'), index=True)
    category_id = Column(Integer, ForeignKey('categories.id'), index=True)
    subcategory_id = Column(Integer, ForeignKey('categories.id'), nullable=True)
    language_detected = Column(String(50), index=True)
    language_confidence = Column(DECIMAL(5, 2))
    
    # الإحصائيات
    member_count = Column(Integer)
    member_count_history = Column(ARRAY(Integer))
    message_count = Column(Integer, default=0)
    message_frequency = Column(DECIMAL(5, 2))
    
    # الجودة والتقييم
    quality_score = Column(Integer, CheckConstraint('quality_score BETWEEN 0 AND 100'))
    activity_score = Column(Integer, CheckConstraint('activity_score BETWEEN 0 AND 100'))
    spam_score = Column(Integer, CheckConstraint('spam_score BETWEEN 0 AND 100'))
    trust_score = Column(Integer, CheckConstraint('trust_score BETWEEN 0 AND 100'))
    
    # Status flags
    status = Column(
        String(20), 
        CheckConstraint("status IN ('active', 'inactive', 'banned', 'deleted', 'private', 'suspended', 'pending')"),
        default='active',
        index=True
    )
    is_verified = Column(Boolean, default=False, index=True)
    is_featured = Column(Boolean, default=False, index=True)
    is_nsfw = Column(Boolean, default=False, index=True)
    
    # المصدر
    source_id = Column(Integer, ForeignKey('sources.id'))
    source_url = Column(Text)
    discovered_at = Column(DateTime, default=datetime.utcnow, index=True)
    discovered_by = Column(String(100))
    
    # التحقق
    last_verified_at = Column(DateTime)
    last_activity_at = Column(DateTime)
    verification_method = Column(String(50))
    verification_count = Column(Integer, default=0)
    
    # البيانات الوصفية
    photo_url = Column(String(500))
    has_bot_member = Column(Boolean, default=False)
    has_restrictions = Column(Boolean, default=False)
    slow_mode_seconds = Column(Integer)
    
    # SEO
    keywords = Column(ARRAY(String(100)))
    tags = Column(ARRAY(String(50)))
    seo_title = Column(String(255))
    seo_description = Column(Text)
    
    # التدقيق
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    deleted_reason = Column(String(255), nullable=True)
    
    # Full-Text Search
    search_vector = Column(TSVECTOR)
    
    # العلاقات
    country = relationship("Country", back_populates="groups")
    category = relationship("Category", foreign_keys=[category_id], back_populates="groups")
    source = relationship("Source", back_populates="groups")
    links = relationship("GroupLink", back_populates="group", cascade="all, delete-orphan")
    history = relationship("GroupHistory", back_populates="group", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Group(id={self.id}, title='{self.title[:30]}...', country='{self.country_id}')>"
    
    def to_dict(self):
        """تحويل إلى قاموس للـ API"""
        return {
            'id': self.id,
            'telegram_id': self.telegram_id,
            'username': self.username,
            'invite_link': self.invite_link,
            'title': self.title,
            'title_ar': self.title_ar,
            'description': self.description,
            'country': self.country.name_en if self.country else None,
            'category': self.category.name_en if self.category else None,
            'language': self.language_detected,
            'member_count': self.member_count,
            'quality_score': self.quality_score,
            'activity_score': self.activity_score,
            'status': self.status,
            'is_verified': self.is_verified,
            'discovered_at': self.discovered_at.isoformat() if self.discovered_at else None
        }


class GroupLink(Base):
    """جدول روابط المجموعات البديلة"""
    __tablename__ = 'group_links'
    
    id = Column(Integer, primary_key=True)
    group_id = Column(BigInteger, ForeignKey('groups.id', ondelete='CASCADE'), index=True)
    link_type = Column(
        String(20), 
        CheckConstraint("link_type IN ('username', 'invite', 'shortlink', 'redirect')")
    )
    link_value = Column(String(255), nullable=False)
    is_primary = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    discovered_at = Column(DateTime, default=datetime.utcnow)
    last_checked_at = Column(DateTime)
    redirect_count = Column(Integer, default=0)
    
    # العلاقات
    group = relationship("Group", back_populates="links")
    
    def __repr__(self):
        return f"<GroupLink(group_id={self.group_id}, type='{self.link_type}')>"


class GroupHistory(Base):
    """جدول تاريخ المجموعات"""
    __tablename__ = 'group_history'
    
    id = Column(BigInteger, primary_key=True)
    group_id = Column(BigInteger, ForeignKey('groups.id', ondelete='CASCADE'), index=True)
    event_type = Column(String(50), nullable=False, index=True)
    old_value = Column(JSONB)
    new_value = Column(JSONB)
    event_at = Column(DateTime, default=datetime.utcnow, index=True)
    triggered_by = Column(String(100))
    
    # العلاقات
    group = relationship("Group", back_populates="history")
    
    def __repr__(self):
        return f"<GroupHistory(group_id={self.group_id}, event='{self.event_type}')>"


class User(Base):
    """جدول المستخدمين"""
    __tablename__ = 'users'
    
    id = Column(BigInteger, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))
    language_code = Column(String(10))
    country_code = Column(String(10), ForeignKey('countries.code'), nullable=True)
    
    # التفضيلات
    preferred_language = Column(String(10), default='ar')
    preferred_categories = Column(ARRAY(Integer))
    notifications_enabled = Column(Boolean, default=True)
    
    # النشاط
    first_seen_at = Column(DateTime, default=datetime.utcnow)
    last_seen_at = Column(DateTime, default=datetime.utcnow)
    total_searches = Column(Integer, default=0)
    total_clicks = Column(Integer, default=0)
    
    # الاشتراك
    subscription_tier = Column(
        String(20),
        CheckConstraint("subscription_tier IN ('free', 'basic', 'premium', 'enterprise')"),
        default='free'
    )
    subscription_expires_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<User(telegram_id={self.telegram_id}, username='{self.username}')>"


class SearchLog(Base):
    """جدول سجلات البحث"""
    __tablename__ = 'search_logs'
    
    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=True, index=True)
    query = Column(Text, nullable=False)
    filters = Column(JSONB)
    results_count = Column(Integer)
    clicked_groups = Column(ARRAY(BigInteger))
    search_duration_ms = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<SearchLog(query='{self.query[:50]}...', user_id={self.user_id})>"


class AnalyticsDaily(Base):
    """جدول التحليلات اليومية"""
    __tablename__ = 'analytics_daily'
    
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, unique=True, nullable=False)
    country_id = Column(Integer, ForeignKey('countries.id'), nullable=True, index=True)
    
    new_groups = Column(Integer, default=0)
    verified_groups = Column(Integer, default=0)
    deleted_groups = Column(Integer, default=0)
    total_searches = Column(Integer, default=0)
    total_clicks = Column(Integer, default=0)
    active_users = Column(Integer, default=0)
    new_users = Column(Integer, default=0)
    
    avg_search_time_ms = Column(Integer)
    avg_scrape_time_ms = Column(Integer)
    error_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<AnalyticsDaily(date='{self.date}', country_id={self.country_id})>"


class ErrorLog(Base):
    """جدول سجلات الأخطاء"""
    __tablename__ = 'error_logs'
    
    id = Column(BigInteger, primary_key=True)
    service = Column(String(50), nullable=False, index=True)
    error_type = Column(String(100))
    error_message = Column(Text)
    stack_trace = Column(Text)
    context = Column(JSONB)
    severity = Column(
        String(20),
        CheckConstraint("severity IN ('low', 'medium', 'high', 'critical')"),
        index=True
    )
    is_resolved = Column(Boolean, default=False, index=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<ErrorLog(service='{self.service}', severity='{self.severity}')>"


# Indexes إضافية
Index('idx_groups_fts', Group.search_vector, postgresql_using='gin')
Index('idx_groups_members_desc', Group.member_count.desc())
Index('idx_groups_quality_desc', Group.quality_score.desc())
Index('idx_search_logs_query_fts', 
      func.to_tsvector('arabic', SearchLog.query), 
      postgresql_using='gin')
