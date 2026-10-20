-- ============================================
-- QURAN TRANSLATIONS AND TAFSIR FULL-TEXT INDEXES
-- Phase 3 Migration (delta)
-- ============================================
-- The `translations` and `tafsirs` tables are created in
-- 001_initial_schema.sql. This migration only adds the full-text
-- search indexes that are not part of the initial schema, so the
-- two files do not duplicate table definitions.

-- Full-text search index for tafsir text
CREATE INDEX IF NOT EXISTS idx_tafsir_text_search
    ON tafsirs USING GIN (to_tsvector('simple', text));

-- Full-text search index for translations
CREATE INDEX IF NOT EXISTS idx_translation_text_search
    ON translations USING GIN (to_tsvector('simple', text));
