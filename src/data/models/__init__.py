"""SQLAlchemy models for Quran data."""
from src.data.models.quran import Base, Surah, Ayah, Translation, Tafsir, QueryLog

__all__ = ["Base", "Surah", "Ayah", "Translation", "Tafsir", "QueryLog"]
