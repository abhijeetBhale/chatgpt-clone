-- Migration script for Personality & Learning System
-- Run this to add new tables for user preferences, memory, and feedback analytics

-- User Preferences table
CREATE TABLE IF NOT EXISTS user_preferences (
    user_id VARCHAR PRIMARY KEY,
    tone VARCHAR(32) NOT NULL DEFAULT 'balanced',
    response_length VARCHAR(32) NOT NULL DEFAULT 'adaptive',
    expertise_level VARCHAR(32) NOT NULL DEFAULT 'auto',
    humor_level FLOAT NOT NULL DEFAULT 0.5,
    feedback_count INTEGER NOT NULL DEFAULT 0,
    last_adapted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences(user_id);

-- User Memory table
CREATE TABLE IF NOT EXISTS user_memory (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    memory_type VARCHAR(32) NOT NULL,
    key VARCHAR(128) NOT NULL,
    value TEXT NOT NULL DEFAULT '',
    confidence FLOAT NOT NULL DEFAULT 0.5,
    source VARCHAR(32) NOT NULL DEFAULT 'inferred',
    created_at TIMESTAMP DEFAULT NOW(),
    last_used_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_memory_user_id ON user_memory(user_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_memory_type_key ON user_memory(user_id, memory_type, key);

-- Feedback Analytics table
CREATE TABLE IF NOT EXISTS feedback_analytics (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR,
    category VARCHAR(64) NOT NULL,
    pattern TEXT NOT NULL DEFAULT '',
    positive_count INTEGER NOT NULL DEFAULT 0,
    negative_count INTEGER NOT NULL DEFAULT 0,
    last_updated TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_feedback_analytics_user_category ON feedback_analytics(user_id, category);