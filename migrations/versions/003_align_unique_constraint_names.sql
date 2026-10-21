-- ============================================
-- ALIGN UNIQUE CONSTRAINT NAMES WITH THE MODELS
-- Phase 3 Migration (delta)
-- ============================================
-- `001_initial_schema.sql` created these UNIQUE constraints without names, so
-- PostgreSQL named them after the table and columns. The SQLAlchemy models in
-- `src/data/models/quran.py` declare explicit names instead:
--
--   ayahs        uq_ayah_surah_number
--   translations uq_translation
--   tafsirs      uq_tafsir
--
-- Any code that later drops or recreates a constraint by the model name
-- (`drop_constraint("uq_tafsir")`, a bulk copy, a schema diff) would fail
-- against the database-generated name. This migration renames each constraint
-- to its declared model name.
--
-- Renaming a constraint also renames its backing index. Nothing queries these
-- names at runtime, so the rename is transparent to the application.
--
-- The migration is idempotent: each block does nothing unless the old name is
-- present and the new name is absent.

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'ayahs_surah_id_number_in_surah_key'
          AND conrelid = 'ayahs'::regclass
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'uq_ayah_surah_number'
          AND conrelid = 'ayahs'::regclass
    ) THEN
        ALTER TABLE ayahs
            RENAME CONSTRAINT ayahs_surah_id_number_in_surah_key TO uq_ayah_surah_number;
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'translations_ayah_id_language_translator_key'
          AND conrelid = 'translations'::regclass
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'uq_translation'
          AND conrelid = 'translations'::regclass
    ) THEN
        ALTER TABLE translations
            RENAME CONSTRAINT translations_ayah_id_language_translator_key TO uq_translation;
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'tafsirs_ayah_id_source_name_key'
          AND conrelid = 'tafsirs'::regclass
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'uq_tafsir'
          AND conrelid = 'tafsirs'::regclass
    ) THEN
        ALTER TABLE tafsirs
            RENAME CONSTRAINT tafsirs_ayah_id_source_name_key TO uq_tafsir;
    END IF;
END $$;
