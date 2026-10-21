"""Tests for the Quran loader used by the seeding script."""

import json

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from src.data.ingestion.quran_loader import (
    SURAH_VERSE_COUNTS,
    QuranLoader,
    clean_translation,
    global_ayah_number,
    revelation_type,
)
from src.data.models.quran import Ayah, Surah, Tafsir, Translation


def test_clean_translation_removes_footnotes_and_tags():
    raw = "Alif, Lām, Meem.<sup foot_note=195935>1</sup> &amp; more"
    assert clean_translation(raw) == "Alif, Lām, Meem. & more"


def test_clean_translation_collapses_whitespace():
    assert clean_translation("  a\n\n b  ") == "a b"


def test_surah_verse_counts_cover_the_whole_quran():
    assert len(SURAH_VERSE_COUNTS) == 114
    assert sum(SURAH_VERSE_COUNTS) == 6236


def test_global_ayah_number_matches_known_verses():
    assert global_ayah_number(1, 1) == 1
    assert global_ayah_number(2, 255) == 262
    assert global_ayah_number(18, 10) == 2150
    assert global_ayah_number(114, 6) == 6236


def test_global_ayah_number_rejects_out_of_range_values():
    with pytest.raises(ValueError):
        global_ayah_number(115, 1)
    with pytest.raises(ValueError):
        global_ayah_number(1, 8)


def test_revelation_type_maps_api_places():
    assert revelation_type("makkah") == "meccan"
    assert revelation_type("madinah") == "medinan"
    assert revelation_type(None) == "meccan"
    assert revelation_type("meccan") == "meccan"


@pytest.fixture()
def session():
    engine = create_engine("sqlite://")
    tables = [Surah.__table__, Ayah.__table__, Translation.__table__, Tafsir.__table__]
    Surah.metadata.create_all(engine, tables=tables)
    with Session(engine) as db_session:
        yield db_session


def _write_sample(tmp_path):
    payload = {
        "surahs": [
            {
                "number": 1,
                "name_ar": "الفاتحة",
                "name_en": "Al-Fatihah",
                "verse_count": 7,
                "revelation_type": "meccan",
                "ayahs": [
                    {
                        "number_in_surah": 1,
                        "text_uthmani": "بِسْمِ ٱللَّهِ",
                        "juz": 1,
                        "page": 1,
                        "translations": [
                            {
                                "language": "en",
                                "translator": "Saheeh International",
                                "text": "In the name of Allah.",
                            }
                        ],
                    },
                    {
                        "number_in_surah": 2,
                        "text_uthmani": "ٱلْحَمْدُ لِلَّهِ",
                        "juz": 1,
                        "page": 1,
                        "translations": [],
                    },
                ],
            },
            {
                "number": 2,
                "name_ar": "البقرة",
                "name_en": "Al-Baqarah",
                "verse_count": 286,
                "revelation_type": "medinan",
                "ayahs": [
                    {
                        "number_in_surah": 1,
                        "text_uthmani": "الٓمٓ",
                        "juz": 1,
                        "page": 2,
                        "translations": [],
                    }
                ],
            },
        ]
    }
    path = tmp_path / "quran.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return str(path)


def test_load_from_json_assigns_global_verse_numbers(session, tmp_path):
    stats = QuranLoader(session).load_from_json(_write_sample(tmp_path))

    assert stats == {"surahs": 2, "ayahs": 3, "translations": 1}

    sutras = session.scalars(select(Surah).order_by(Surah.number)).all()
    assert [surah.name_en for surah in sutras] == ["Al-Fatihah", "Al-Baqarah"]
    assert sutras[1].revelation_type == "medinan"

    ayahs = session.scalars(select(Ayah).order_by(Ayah.number)).all()
    assert [ayah.number for ayah in ayahs] == [1, 2, 8]
    assert [ayah.number_in_surah for ayah in ayahs] == [1, 2, 1]
    assert ayahs[2].surah_id == sutras[1].id
    assert ayahs[0].surah_name == "Al-Fatihah"

    translation = session.scalars(select(Translation)).one()
    assert translation.language == "en"
    assert translation.text == "In the name of Allah."


def test_load_from_json_is_idempotent(session, tmp_path):
    path = _write_sample(tmp_path)
    QuranLoader(session).load_from_json(path)
    stats = QuranLoader(session).load_from_json(path)

    assert stats == {"surahs": 2, "ayahs": 3, "translations": 1}
    assert len(session.scalars(select(Surah)).all()) == 2
    assert len(session.scalars(select(Ayah)).all()) == 3
    assert len(session.scalars(select(Translation)).all()) == 1
