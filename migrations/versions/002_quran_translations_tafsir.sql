-- ============================================
-- QURAN TRANSLATIONS AND TAFSIR TABLES
-- Phase 3 Migration
-- ============================================

-- Translations table (multi-language support)
CREATE TABLE IF NOT EXISTS translations (
    id SERIAL PRIMARY KEY,
    ayah_id INT NOT NULL REFERENCES ayahs(id) ON DELETE CASCADE,
    language VARCHAR(5) NOT NULL,
    translator VARCHAR(100),
    text TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(ayah_id, language, translator)
);

-- Indexes for translations
CREATE INDEX IF NOT EXISTS idx_translation_ayah ON translations(ayah_id);
CREATE INDEX IF NOT EXISTS idx_translation_lang ON translations(language);

-- Tafsir table (commentaries)
CREATE TABLE IF NOT EXISTS tafsirs (
    id SERIAL PRIMARY KEY,
    ayah_id INT NOT NULL REFERENCES ayahs(id) ON DELETE CASCADE,
    source_name VARCHAR(100) NOT NULL,
    text TEXT NOT NULL,
    language VARCHAR(2) DEFAULT 'ar',
    author VARCHAR(200),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(ayah_id, source_name)
);

-- Indexes for tafsirs
CREATE INDEX IF NOT EXISTS idx_tafsir_ayah ON tafsirs(ayah_id);
CREATE INDEX IF NOT EXISTS idx_tafsir_source ON tafsirs(source_name);
CREATE INDEX IF NOT EXISTS idx_tafsir_text_search ON tafsirs USING GIN (to_tsvector('simple', text));

-- Add full-text search index for translations (if not exists)
CREATE INDEX IF NOT EXISTS idx_translation_text_search ON translations USING GIN (to_tsvector('simple', text));
