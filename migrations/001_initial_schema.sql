-- ============================================
-- QURAN TABLES (Phase 1 Priority)
-- ============================================

CREATE TABLE IF NOT EXISTS surahs (
    id SERIAL PRIMARY KEY,
    number INT NOT NULL UNIQUE CHECK (number BETWEEN 1 AND 114),
    name_ar VARCHAR(100) NOT NULL,
    name_en VARCHAR(100) NOT NULL,
    verse_count INT NOT NULL,
    revelation_type VARCHAR(7) CHECK (revelation_type IN ('meccan', 'medinan')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ayahs (
    id SERIAL PRIMARY KEY,
    surah_id INT NOT NULL REFERENCES surahs(id) ON DELETE CASCADE,
    number INT NOT NULL,
    number_in_surah INT NOT NULL,
    text_uthmani TEXT NOT NULL,
    text_simple TEXT,
    juz INT NOT NULL CHECK (juz BETWEEN 1 AND 30),
    page INT NOT NULL,
    hizb INT,
    rub_el_hizb INT,
    sajdah BOOLEAN DEFAULT FALSE,
    surah_name VARCHAR(100),
    surah_name_ar VARCHAR(100),
    UNIQUE(surah_id, number_in_surah),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_ayah_surah_number ON ayahs(surah_id, number_in_surah);
CREATE INDEX idx_ayah_juz ON ayahs(juz);
CREATE INDEX idx_ayah_page ON ayahs(page);
CREATE INDEX idx_ayah_text_search ON ayahs USING GIN (to_tsvector('simple', text_uthmani));
CREATE INDEX idx_ayah_text_trgm ON ayahs USING GIN (text_uthmani gin_trgm_ops);

-- ============================================
-- TRANSLATIONS (Multi-language support)
-- ============================================

CREATE TABLE IF NOT EXISTS translations (
    id SERIAL PRIMARY KEY,
    ayah_id INT NOT NULL REFERENCES ayahs(id) ON DELETE CASCADE,
    language VARCHAR(5) NOT NULL,
    translator VARCHAR(100),
    text TEXT NOT NULL,
    UNIQUE(ayah_id, language, translator),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_translation_ayah ON translations(ayah_id);
CREATE INDEX idx_translation_lang ON translations(language);

-- ============================================
-- TAFSIR (Commentaries)
-- ============================================

CREATE TABLE IF NOT EXISTS tafsirs (
    id SERIAL PRIMARY KEY,
    ayah_id INT NOT NULL REFERENCES ayahs(id) ON DELETE CASCADE,
    source_name VARCHAR(100) NOT NULL,
    text TEXT NOT NULL,
    language VARCHAR(2) DEFAULT 'ar',
    author VARCHAR(200),
    UNIQUE(ayah_id, source_name),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_tafsir_ayah ON tafsirs(ayah_id);
CREATE INDEX idx_tafsir_source ON tafsirs(source_name);

-- ============================================
-- QUERY LOGGING (Analytics)
-- ============================================

CREATE TABLE IF NOT EXISTS query_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_query TEXT NOT NULL,
    intent VARCHAR(30) NOT NULL,
    intent_confidence FLOAT,
    agent_used VARCHAR(50),
    response_summary TEXT,
    citations JSONB DEFAULT '[]'::jsonb,
    latency_ms INT,
    language VARCHAR(5) DEFAULT 'ar',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_query_intent ON query_logs(intent);
CREATE INDEX idx_query_created ON query_logs(created_at);
CREATE INDEX idx_query_language ON query_logs(language);

-- ============================================
-- CREATED_AT/UPDATED_AT TRIGGER
-- ============================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_surahs_updated_at
    BEFORE UPDATE ON surahs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
