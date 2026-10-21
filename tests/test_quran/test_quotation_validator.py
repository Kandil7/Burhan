"""Regression tests for quotation validation against a seeded Quran table."""

import pytest
from sqlalchemy import create_engine, literal, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from src.data.models.quran import Ayah, Surah, Tafsir, Translation
from src.quran.quotation_validator import (
    QuotationValidator,
    _skeleton,
    _skeleton_sql,
)

# Ayat al-Kursi as stored: the simple column keeps tatweel and alef maksura,
# which is exactly what broke the old candidate filter.
KURSI_UTHMANI = "ٱللَّهُ لَآ إِلَـٰهَ إِلَّا هُوَ ٱلْحَىُّ ٱلْقَيُّومُ"
KURSI_SIMPLE = "الله لا اله الا هو الحى القيوم"
KURSI_INPUT = "اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ"


@pytest.fixture()
def validator():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    tables = [Surah.__table__, Ayah.__table__, Translation.__table__, Tafsir.__table__]
    Surah.metadata.create_all(engine, tables=tables)
    with Session(engine) as session:
        surah = Surah(
            number=2,
            name_ar="البقرة",
            name_en="Al-Baqarah",
            verse_count=286,
            revelation_type="medinan",
        )
        session.add(surah)
        session.flush()
        session.add(
            Ayah(
                surah_id=surah.id,
                number=262,
                number_in_surah=255,
                text_uthmani=KURSI_UTHMANI,
                text_simple=KURSI_SIMPLE,
                juz=3,
                page=42,
                surah_name="Al-Baqarah",
                surah_name_ar="البقرة",
            )
        )
        session.commit()
        yield QuotationValidator(session)


def test_sql_skeleton_mirrors_python_skeleton(validator):
    tricky = "ٱلْحَىُّ ــ ٱلْقَيُّومُ ة"
    sql_value = validator.session.execute(select(_skeleton_sql(literal(tricky)))).scalar()
    assert sql_value == _skeleton(tricky).replace(" ", "")


async def test_verbatim_verse_is_recognised(validator):
    result = await validator.validate(KURSI_INPUT)
    assert result["is_quran"] is True
    assert result["confidence"] == 1.0
    assert result["matched_ayah"]["ayah_number"] == 255


async def test_fragment_is_recognised(validator):
    result = await validator.validate("لا اله الا هو")
    assert result["is_quran"] is True
    assert result["confidence"] == 1.0
    assert result["matched_ayah"]["surah_number"] == 2


async def test_unrelated_text_is_rejected(validator):
    result = await validator.validate("هذا نص ليس من القرآن الكريم إطلاقا")
    assert result["is_quran"] is False
    assert result["matched_ayah"] is None
