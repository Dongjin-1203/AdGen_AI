-- ============================================================
-- Migration: Vision AI 필드 + GenerationHistory 테이블 (SQLite)
-- Date: 2025-01-14
-- ============================================================

-- ============================================================
-- 1. UserContent 테이블 - Vision AI 필드 추가
-- ============================================================

-- SQLite는 ADD COLUMN을 하나씩만 지원
ALTER TABLE user_contents ADD COLUMN sub_category TEXT;
ALTER TABLE user_contents ADD COLUMN material TEXT;
ALTER TABLE user_contents ADD COLUMN fit TEXT;
ALTER TABLE user_contents ADD COLUMN style_tags TEXT;
ALTER TABLE user_contents ADD COLUMN ai_confidence REAL;
ALTER TABLE user_contents ADD COLUMN confirmed INTEGER DEFAULT 0;  -- SQLite는 BOOLEAN 없음 (0=false, 1=true)


-- ============================================================
-- 2. GenerationHistory 테이블 생성
-- ============================================================

CREATE TABLE IF NOT EXISTS generation_history (
    -- Primary Key
    history_id TEXT PRIMARY KEY,
    
    -- Foreign Keys
    content_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    
    -- 생성 정보
    style TEXT NOT NULL,
    prompt TEXT,
    result_url TEXT NOT NULL,
    
    -- 메타데이터
    processing_time REAL,
    created_at TEXT DEFAULT (datetime('now')),
    
    -- Foreign Key Constraints
    FOREIGN KEY (content_id) REFERENCES user_contents(content_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);


-- ============================================================
-- 3. 인덱스 생성
-- ============================================================

-- UserContent 인덱스
CREATE INDEX IF NOT EXISTS idx_contents_user_created 
    ON user_contents(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_contents_confirmed 
    ON user_contents(confirmed) 
    WHERE confirmed = 0;  -- 미확인 항목만

-- GenerationHistory 인덱스
CREATE INDEX IF NOT EXISTS idx_history_user_created 
    ON generation_history(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_history_content 
    ON generation_history(content_id);

CREATE INDEX IF NOT EXISTS idx_history_style 
    ON generation_history(style);


-- ============================================================
-- 4. 확인 쿼리 (선택)
-- ============================================================

-- 테이블 구조 확인
-- PRAGMA table_info(user_contents);
-- PRAGMA table_info(generation_history);