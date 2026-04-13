"""
SQLAlchemy models for the Quran database.

Defines the table structure for storing Quran text, translations, and tafsir.
Used by the Quran pipeline for verse retrieval, NL2SQL, and quotation validation.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Surah(Base):
    """Quran chapter (Surah)."""

    __tablename__ = "surahs"

    id = Column(Integer, primary_key=True)
    number = Column(Integer, unique=True, nullable=False)
    name_ar = Column(String(100), nullable=False)
    name_en = Column(String(100), nullable=False)
    verse_count = Column(Integer, nullable=False)
    revelation_type = Column(String(7), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    ayahs = relationship("Ayah", back_populates="surah", lazy="selectin")

    __table_args__ = (
        CheckConstraint("number BETWEEN 1 AND 114", name="chk_surah_number"),
        CheckConstraint(
            "revelation_type IN ('meccan', 'medinan')",
            name="chk_revelation_type",
        ),
    )

    def __repr__(self) -> str:
        return f"<Surah {self.number}: {self.name_en}>"


class Ayah(Base):
    """Quran verse (Ayah)."""

    __tablename__ = "ayahs"

    id = Column(Integer, primary_key=True)
    surah_id = Column(Integer, ForeignKey("surahs.id", ondelete="CASCADE"), nullable=False)
    number = Column(Integer, nullable=False)
    number_in_surah = Column(Integer, nullable=False)
    text_uthmani = Column(Text, nullable=False)
    text_simple = Column(Text, nullable=True)
    juz = Column(Integer, nullable=False)
    page = Column(Integer, nullable=False)
    hizb = Column(Integer, nullable=True)
    rub_el_hizb = Column(Integer, nullable=True)
    sajdah = Column(Boolean, default=False)
    surah_name = Column(String(100), nullable=True)
    surah_name_ar = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    surah = relationship("Surah", back_populates="ayahs")
    translations = relationship("Translation", back_populates="ayah", lazy="selectin")
    tafsirs = relationship("Tafsir", back_populates="ayah", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("surah_id", "number_in_surah", name="uq_ayah_surah_number"),
        CheckConstraint("juz BETWEEN 1 AND 30", name="chk_ayah_juz"),
    )

    def __repr__(self) -> str:
        return f"<Ayah {self.surah_id}:{self.number_in_surah}>"


class Translation(Base):
    """Translation of a Quran verse in a specific language."""

    __tablename__ = "translations"

    id = Column(Integer, primary_key=True)
    ayah_id = Column(Integer, ForeignKey("ayahs.id", ondelete="CASCADE"), nullable=False)
    language = Column(String(5), nullable=False)
    translator = Column(String(100), nullable=True)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    ayah = relationship("Ayah", back_populates="translations")

    __table_args__ = (
        UniqueConstraint("ayah_id", "language", "translator", name="uq_translation"),
    )

    def __repr__(self) -> str:
        return f"<Translation {self.language} by {self.translator}>"


class Tafsir(Base):
    """Tafsir (commentary) for a Quran verse."""

    __tablename__ = "tafsirs"

    id = Column(Integer, primary_key=True)
    ayah_id = Column(Integer, ForeignKey("ayahs.id", ondelete="CASCADE"), nullable=False)
    source_name = Column(String(100), nullable=False)
    text = Column(Text, nullable=False)
    language = Column(String(2), default="ar")
    author = Column(String(200), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    ayah = relationship("Ayah", back_populates="tafsirs")

    __table_args__ = (
        UniqueConstraint("ayah_id", "source_name", name="uq_tafsir"),
    )

    def __repr__(self) -> str:
        return f"<Tafsir {self.source_name}>"


class QueryLog(Base):
    """Log of user queries for analytics."""

    __tablename__ = "query_logs"

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_query = Column(Text, nullable=False)
    intent = Column(String(30), nullable=False)
    intent_confidence = Column(Float, nullable=True)
    agent_used = Column(String(50), nullable=True)
    response_summary = Column(Text, nullable=True)
    citations = Column(JSONB, default=lambda: [])
    latency_ms = Column(Integer, nullable=True)
    language = Column(String(5), default="ar")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<QueryLog {self.intent} ({self.language})>"
