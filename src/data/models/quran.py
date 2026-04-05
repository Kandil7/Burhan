"""
SQLAlchemy models for Quran data.

Provides ORM models for:
- Surahs (114 chapters)
- Ayahs (6,236 verses)
- Translations (multi-language)
- Tafsirs (commentaries)

Phase 3: Foundation for Quran pipeline and NL2SQL.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    ForeignKey,
    DateTime,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class Surah(Base):
    """
    Surah (chapter) model.
    
    Represents one of the 114 chapters of the Quran.
    """
    __tablename__ = "surahs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    number = Column(Integer, nullable=False, unique=True, index=True)
    name_ar = Column(String(100), nullable=False)
    name_en = Column(String(100), nullable=False)
    verse_count = Column(Integer, nullable=False)
    revelation_type = Column(String(7), nullable=False)  # 'meccan' or 'medinan'
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    ayahs = relationship("Ayah", back_populates="surah", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Surah {self.number}: {self.name_en} ({self.verse_count} ayahs)>"


class Ayah(Base):
    """
    Ayah (verse) model.
    
    Represents a single verse of the Quran with Uthmani text and metadata.
    """
    __tablename__ = "ayahs"
    __table_args__ = (
        UniqueConstraint("surah_id", "number_in_surah"),
        Index("idx_ayah_surah_number", "surah_id", "number_in_surah"),
        Index("idx_ayah_juz", "juz"),
        Index("idx_ayah_page", "page"),
        Index("idx_ayah_text_search", "text_uthmani"),
    )
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    surah_id = Column(Integer, ForeignKey("surahs.id", ondelete="CASCADE"), nullable=False, index=True)
    number = Column(Integer, nullable=False)  # Global ayah number (1-6236)
    number_in_surah = Column(Integer, nullable=False)
    text_uthmani = Column(Text, nullable=False)
    text_simple = Column(Text, nullable=True)
    juz = Column(Integer, nullable=False)  # 1-30
    page = Column(Integer, nullable=False)  # 1-604
    hizb = Column(Integer, nullable=True)
    rub_el_hizb = Column(Integer, nullable=True)
    sajdah = Column(Boolean, default=False)
    surah_name = Column(String(100), nullable=True)
    surah_name_ar = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    surah = relationship("Surah", back_populates="ayahs")
    translations = relationship("Translation", back_populates="ayah", cascade="all, delete-orphan")
    tafsirs = relationship("Tafsir", back_populates="ayah", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Ayah {self.surah_id}:{self.number_in_surah}>"


class Translation(Base):
    """
    Translation model.
    
    Stores translations of ayahs in multiple languages.
    """
    __tablename__ = "translations"
    __table_args__ = (
        UniqueConstraint("ayah_id", "language", "translator"),
        Index("idx_translation_ayah", "ayah_id"),
        Index("idx_translation_lang", "language"),
    )
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ayah_id = Column(Integer, ForeignKey("ayahs.id", ondelete="CASCADE"), nullable=False, index=True)
    language = Column(String(5), nullable=False)  # 'en', 'ur', 'fr', etc.
    translator = Column(String(100), nullable=True)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    ayah = relationship("Ayah", back_populates="translations")
    
    def __repr__(self):
        return f"<Translation {self.language} by {self.translator}>"


class Tafsir(Base):
    """
    Tafsir (commentary) model.
    
    Stores scholarly commentaries on ayahs (Ibn Kathir, Al-Jalalayn, etc.).
    """
    __tablename__ = "tafsirs"
    __table_args__ = (
        UniqueConstraint("ayah_id", "source_name"),
        Index("idx_tafsir_ayah", "ayah_id"),
        Index("idx_tafsir_source", "source_name"),
    )
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ayah_id = Column(Integer, ForeignKey("ayahs.id", ondelete="CASCADE"), nullable=False, index=True)
    source_name = Column(String(100), nullable=False)  # 'ibn-kathir', 'al-jalalayn', etc.
    text = Column(Text, nullable=False)
    language = Column(String(2), default="ar")
    author = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    ayah = relationship("Ayah", back_populates="tafsirs")
    
    def __repr__(self):
        return f"<Tafsir {self.source_name} for ayah {self.ayah_id}>"
