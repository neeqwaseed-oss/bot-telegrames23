:wq-- TCGIS - Initial Database Schema
-- Telegram Country Group Indexing System

-- إنشاء قاعدة البيانات
-- CREATE DATABASE tcgis;

-- تمكين الامتدادات
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- جدول الدول
CREATE TABLE IF NOT EXISTS countries (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) UNIQUE NOT NULL,
    name_en VARCHAR(100) NOT NULL,
    name_ar VARCHAR(100),
    name_local VARCHAR(100),
    region VARCHAR(50),
    language_primary VARCHAR(50),
    language_secondary VARCHAR(50)[],
    timezone VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    total_groups INTEGER DEFAULT 0,
    total_channels INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_countries_code ON countries(code);
CREATE INDEX idx_countries_region ON countries(region);
CREATE INDEX idx_countries_active ON countries(is_active);

-- جدول الفئات
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name_en VARCHAR(100) NOT NULL,
    name_ar VARCHAR(100),
    slug VARCHAR(100) UNIQUE NOT NULL,
    parent_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    description TEXT,
    icon VARCHAR(255),
    color VARCHAR(7),
    total_groups INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_categories_slug ON categories(slug);
CREATE INDEX idx_categories_active ON categories(is_active);

-- جدول المصادر
CREATE TABLE IF NOT EXISTS sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    url VARCHAR(255),
    type VARCHAR(50),
    reliability_score INTEGER CHECK (reliability_score BETWEEN 1 AND 10),
    rate_limit_requests INTEGER DEFAULT 100,
    rate_limit_window INTEGER DEFAULT 60,
    is_active BOOLEAN DEFAULT TRUE,
    last_scraped_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- جدول المجموعات الرئيسي
CREATE TABLE IF NOT EXISTS groups (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE,
    username VARCHAR(255) UNIQUE,
    invite_link VARCHAR(255) UNIQUE,
    link_type VARCHAR(20) CHECK (link_type IN ('public', 'private')),
    title VARCHAR(255) NOT NULL,
    title_ar VARCHAR(255),
    description TEXT,
    description_ar TEXT,
    country_id INTEGER REFERENCES countries(id),
    category_id INTEGER REFERENCES categories(id),
    subcategory_id INTEGER REFERENCES categories(id),
    language_detected VARCHAR(50),
    language_confidence DECIMAL(5, 2),
    member_count INTEGER,
    member_count_history INTEGER[],
    message_count INTEGER DEFAULT 0,
    message_frequency DECIMAL(5, 2),
    quality_score INTEGER CHECK (quality_score BETWEEN 0 AND 100),
    activity_score INTEGER CHECK (activity_score BETWEEN 0 AND 100),
    spam_score INTEGER CHECK (spam_score BETWEEN 0 AND 100),
    trust_score INTEGER CHECK (trust_score BETWEEN 0 AND 100),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'banned', 'deleted', 'private', 'suspended', 'pending')),
    is_verified BOOLEAN DEFAULT FALSE,
    is_featured BOOLEAN DEFAULT FALSE,
    is_nsfw BOOLEAN DEFAULT FALSE,
    source_id INTEGER REFERENCES sources(id),
    source_url TEXT,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    discovered_by VARCHAR(100),
    last_verified_at TIMESTAMP,
    last_activity_at TIMESTAMP,
    verification_method VARCHAR(50),
    verification_count INTEGER DEFAULT 0,
    photo_url VARCHAR(500),
    has_bot_member BOOLEAN DEFAULT FALSE,
    has_restrictions BOOLEAN DEFAULT FALSE,
    slow_mode_seconds INTEGER,
    keywords VARCHAR(100)[],
    tags VARCHAR(50)[],
    seo_title VARCHAR(255),
    seo_description TEXT,
    search_vector TSVECTOR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    deleted_reason VARCHAR(255)
);

CREATE INDEX idx_groups_telegram_id ON groups(telegram_id);
CREATE INDEX idx_groups_username ON groups(username);
CREATE INDEX idx_groups_invite_link ON groups(invite_link);
CREATE INDEX idx_groups_country ON groups(country_id);
CREATE INDEX idx_groups_category ON groups(category_id);
CREATE INDEX idx_groups_language ON groups(language_detected);
CREATE INDEX idx_groups_status ON groups(status);
CREATE INDEX idx_groups_verified ON groups(is_verified);
CREATE INDEX idx_groups_featured ON groups(is_featured);
CREATE INDEX idx_groups_discovered ON groups(discovered_at);
CREATE INDEX idx_groups_fts ON groups USING gin(search_vector);
CREATE INDEX idx_groups_members_desc ON groups(member_count DESC NULLS LAST);
CREATE INDEX idx_groups_quality_desc ON groups(quality_score DESC NULLS LAST);

-- جدول روابط المجموعات البديلة
CREATE TABLE IF NOT EXISTS group_links (
    id SERIAL PRIMARY KEY,
    group_id BIGINT REFERENCES groups(id) ON DELETE CASCADE,
    link_type VARCHAR(20) CHECK (link_type IN ('username', 'invite', 'shortlink', 'redirect')),
    link_value VARCHAR(255) NOT NULL,
    is_primary BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_checked_at TIMESTAMP,
    redirect_count INTEGER DEFAULT 0
);

CREATE INDEX idx_group_links_group ON group_links(group_id);

-- جدول تاريخ المجموعات
CREATE TABLE IF NOT EXISTS group_history (
    id BIGSERIAL PRIMARY KEY,
    group_id BIGINT REFERENCES groups(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    old_value JSONB,
    new_value JSONB,
    event_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    triggered_by VARCHAR(100)
);

CREATE INDEX idx_group_history_group ON group_history(group_id);
CREATE INDEX idx_group_history_event ON group_history(event_type);
CREATE INDEX idx_group_history_event_at ON group_history(event_at);

-- جدول المستخدمين
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    language_code VARCHAR(10),
    country_code VARCHAR(10) REFERENCES countries(code),
    preferred_language VARCHAR(10) DEFAULT 'ar',
    preferred_categories INTEGER[],
    notifications_enabled BOOLEAN DEFAULT TRUE,
    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_searches INTEGER DEFAULT 0,
    total_clicks INTEGER DEFAULT 0,
    subscription_tier VARCHAR(20) DEFAULT 'free' CHECK (subscription_tier IN ('free', 'basic', 'premium', 'enterprise')),
    subscription_expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_telegram_id ON users(telegram_id);

-- جدول سجلات البحث
CREATE TABLE IF NOT EXISTS search_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    query TEXT NOT NULL,
    filters JSONB,
    results_count INTEGER,
    clicked_groups BIGINT[],
    search_duration_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_search_logs_user ON search_logs(user_id);
CREATE INDEX idx_search_logs_created ON search_logs(created_at);
CREATE INDEX idx_search_logs_query_fts ON search_logs USING gin(to_tsvector('arabic', query));

-- جدول التحليلات اليومية
CREATE TABLE IF NOT EXISTS analytics_daily (
    id SERIAL PRIMARY KEY,
    date TIMESTAMP UNIQUE NOT NULL,
    country_id INTEGER REFERENCES countries(id),
    new_groups INTEGER DEFAULT 0,
    verified_groups INTEGER DEFAULT 0,
    deleted_groups INTEGER DEFAULT 0,
    total_searches INTEGER DEFAULT 0,
    total_clicks INTEGER DEFAULT 0,
    active_users INTEGER DEFAULT 0,
    new_users INTEGER DEFAULT 0,
    avg_search_time_ms INTEGER,
    avg_scrape_time_ms INTEGER,
    error_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_analytics_date ON analytics_daily(date);
CREATE INDEX idx_analytics_country ON analytics_daily(country_id);

-- جدول سجلات الأخطاء
CREATE TABLE IF NOT EXISTS error_logs (
    id BIGSERIAL PRIMARY KEY,
    service VARCHAR(50) NOT NULL,
    error_type VARCHAR(100),
    error_message TEXT,
    stack_trace TEXT,
    context JSONB,
    severity VARCHAR(20) CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_error_logs_service ON error_logs(service);
CREATE INDEX idx_error_logs_severity ON error_logs(severity);
CREATE INDEX idx_error_logs_resolved ON error_logs(is_resolved);
CREATE INDEX idx_error_logs_created ON error_logs(created_at);

-- إدراج الدول العربية
INSERT INTO countries (code, name_en, name_ar, region, language_primary, timezone, is_active) VALUES
('SA', 'Saudi Arabia', 'السعودية', 'GCC', 'arabic', 'Asia/Riyadh', TRUE),
('AE', 'United Arab Emirates', 'الإمارات', 'GCC', 'arabic', 'Asia/Dubai', TRUE),
('KW', 'Kuwait', 'الكويت', 'GCC', 'arabic', 'Asia/Kuwait', TRUE),
('QA', 'Qatar', 'قطر', 'GCC', 'arabic', 'Asia/Qatar', TRUE),
('BH', 'Bahrain', 'البحرين', 'GCC', 'arabic', 'Asia/Bahrain', TRUE),
('OM', 'Oman', 'عمان', 'GCC', 'arabic', 'Asia/Muscat', TRUE),
('EG', 'Egypt', 'مصر', 'North Africa', 'arabic', 'Africa/Cairo', TRUE),
('IQ', 'Iraq', 'العراق', 'Levant', 'arabic', 'Asia/Baghdad', TRUE),
('JO', 'Jordan', 'الأردن', 'Levant', 'arabic', 'Asia/Amman', TRUE),
('LB', 'Lebanon', 'لبنان', 'Levant', 'arabic', 'Asia/Beirut', TRUE),
('SY', 'Syria', 'سوريا', 'Levant', 'arabic', 'Asia/Damascus', TRUE),
('PS', 'Palestine', 'فلسطين', 'Levant', 'arabic', 'Asia/Gaza', TRUE),
('DZ', 'Algeria', 'الجزائر', 'North Africa', 'arabic', 'Africa/Algiers', TRUE),
('MA', 'Morocco', 'المغرب', 'North Africa', 'arabic', 'Africa/Casablanca', TRUE),
('TN', 'Tunisia', 'تونس', 'North Africa', 'arabic', 'Africa/Tunis', TRUE),
('LY', 'Libya', 'ليبيا', 'North Africa', 'arabic', 'Africa/Tripoli', TRUE),
('SD', 'Sudan', 'السودان', 'East Africa', 'arabic', 'Africa/Khartoum', TRUE),
('YE', 'Yemen', 'اليمن', 'Arabian Peninsula', 'arabic', 'Asia/Aden', TRUE)
ON CONFLICT (code) DO NOTHING;

-- إدراج الفئات الافتراضية
INSERT INTO categories (name_en, name_ar, slug, description, is_active) VALUES
('General', 'عام', 'general', 'General groups', TRUE),
('Technology', 'تقنية', 'technology', 'Technology and programming groups', TRUE),
('Business', 'أعمال', 'business', 'Business and marketing groups', TRUE),
('Education', 'تعليم', 'education', 'Educational groups', TRUE),
('Entertainment', 'ترفيه', 'entertainment', 'Entertainment groups', TRUE),
('News', 'أخبار', 'news', 'News groups', TRUE),
('Health', 'صحة', 'health', 'Health and fitness groups', TRUE),
('Religion', 'دين', 'religion', 'Religious groups', TRUE),
('Travel', 'سفر', 'travel', 'Travel groups', TRUE),
('Food', 'طعام', 'food', 'Food groups', TRUE),
('Fashion', 'موضة', 'fashion', 'Fashion groups', TRUE),
('Automotive', 'سيارات', 'automotive', 'Automotive groups', TRUE),
('Real Estate', 'عقارات', 'real-estate', 'Real estate groups', TRUE),
('Jobs', 'وظائف', 'jobs', 'Job groups', TRUE),
('Community', 'مجتمع', 'community', 'Community groups', TRUE)
ON CONFLICT (slug) DO NOTHING;

-- إدراج المصادر
INSERT INTO sources (name, url, type, reliability_score, is_active) VALUES
('TGStat', 'https://tgstat.com', 'directory', 8, TRUE),
('Google Search', 'https://google.com', 'search_engine', 6, TRUE),
('Telegram Directory', 'https://telegram-directory.com', 'directory', 7, TRUE)
ON CONFLICT DO NOTHING;

-- إنشاء دالة لتحديث updated_at تلقائياً
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- تطبيق الدالة على الجداول
CREATE TRIGGER update_countries_updated_at BEFORE UPDATE ON countries
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_groups_updated_at BEFORE UPDATE ON groups
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
