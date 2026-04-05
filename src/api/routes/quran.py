"""
Quran API endpoints for Athar Islamic QA system.

Provides endpoints for:
- Listing surahs
- Getting surah details
- Retrieving specific ayah
- Searching verses
- Validating quotations
- NL2SQL analytics
- Tafsir retrieval

Phase 3: Complete Quran API surface.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import Optional

from src.quran.verse_retrieval import VerseRetrievalEngine, VerseNotFoundError
from src.quran.nl2sql import NL2SQLEngine, NL2SQLQueryError
from src.quran.quotation_validator import QuotationValidator
from src.quran.tafsir_retrieval import TafsirRetrievalEngine, TafsirNotFoundError
from src.infrastructure.db_sync import get_sync_session
from src.data.models.quran import Surah, Ayah, Translation, Tafsir
from src.config.logging_config import get_logger

logger = get_logger()
router = APIRouter(prefix="/quran", tags=["Quran"])


# ==========================================
# Request/Response Models
# ==========================================


class SurahResponse(BaseModel):
    """Surah information response."""

    number: int
    name_ar: str
    name_en: str
    verse_count: int
    revelation_type: str


class AyahResponse(BaseModel):
    """Ayah information response."""

    surah_number: int
    surah_name_en: str
    ayah_number: int
    text_uthmani: str
    text_simple: Optional[str]
    juz: int
    page: int
    quran_url: str
    translations: Optional[list[dict]] = None


class VerseSearchResponse(BaseModel):
    """Verse search response."""

    verses: list[AyahResponse]
    count: int


class QuotationValidationRequest(BaseModel):
    """Quotation validation request."""

    text: str = Field(..., description="Text to validate")


class QuotationValidationResponse(BaseModel):
    """Quotation validation response."""

    is_quran: bool
    confidence: float
    matched_ayah: Optional[AyahResponse]
    suggestion: Optional[str]


class NL2SQLRequest(BaseModel):
    """NL2SQL request."""

    query: str = Field(..., description="Natural language query about Quran")


class NL2SQLResponse(BaseModel):
    """NL2SQL response."""

    sql: str
    result: list[dict]
    formatted_answer: str
    row_count: int


class TafsirResponse(BaseModel):
    """Tafsir response."""

    ayah: AyahResponse
    tafsirs: list[dict]
    available_sources: list[str]


# ==========================================
# Helper Functions
# ==========================================


def get_verse_engine(db_session):
    """Get verse retrieval engine."""
    return VerseRetrievalEngine(db_session)


def get_nl2sql_engine(db_session):
    """Get NL2SQL engine."""
    return NL2SQLEngine(db_session)


def get_quotation_validator(db_session):
    """Get quotation validator."""
    return QuotationValidator(db_session)


def get_tafsir_engine(db_session):
    """Get tafsir engine."""
    return TafsirRetrievalEngine(db_session)


# ==========================================
# Surahs Endpoints
# ==========================================


@router.get("/surahs", response_model=list[SurahResponse])
async def list_surahs(db_session=Depends(get_sync_session)):
    """
    List all 114 surahs.

    Returns basic information about all surahs in the Quran.
    """
    from src.data.models.quran import Surah

    surahs = db_session.query(Surah).order_by(Surah.number).all()

    return [
        SurahResponse(
            number=s.number,
            name_ar=s.name_ar,
            name_en=s.name_en,
            verse_count=s.verse_count,
            revelation_type=s.revelation_type,
        )
        for s in surahs
    ]


@router.get("/surahs/{surah_number}", response_model=dict)
async def get_surah_details(surah_number: int, db_session=Depends(get_sync_session)):
    """
    Get details for a specific surah.

    Includes surah information and list of ayahs.
    """
    from src.data.models.quran import Surah, Ayah

    surah = db_session.query(Surah).filter(Surah.number == surah_number).first()
    if not surah:
        raise HTTPException(status_code=404, detail=f"Surah {surah_number} not found")

    ayahs = db_session.query(Ayah).filter(Ayah.surah_id == surah.id).order_by(Ayah.number_in_surah).all()

    return {
        "number": surah.number,
        "name_ar": surah.name_ar,
        "name_en": surah.name_en,
        "verse_count": surah.verse_count,
        "revelation_type": surah.revelation_type,
        "ayahs": [
            {"number": a.number_in_surah, "text_uthmani": a.text_uthmani, "juz": a.juz, "page": a.page} for a in ayahs
        ],
    }


# ==========================================
# Ayah Endpoints
# ==========================================


@router.get("/ayah/{surah}:{ayah}", response_model=AyahResponse)
async def get_ayah(surah: int, ayah: int, db_session=Depends(get_sync_session)):
    """
    Get a specific ayah by surah:ayah reference.

    Example: /quran/ayah/2:255
    """
    engine = get_verse_engine(db_session)

    try:
        verse = await engine.lookup(f"{surah}:{ayah}", include_translation=True)
        return AyahResponse(**verse)
    except VerseNotFoundError:
        raise HTTPException(status_code=404, detail=f"Verse {surah}:{ayah} not found")


# ==========================================
# Search Endpoint
# ==========================================


class SearchRequest(BaseModel):
    """Search request."""
    query: str = Field(..., description="Search query")
    limit: int = Field(5, ge=1, le=20)


@router.post("/search", response_model=VerseSearchResponse)
async def search_verses(request: SearchRequest, db_session=Depends(get_sync_session)):
    """
    Search Quran verses by text.

    Performs fuzzy search on Uthmani text.
    """
    engine = get_verse_engine(db_session)
    results = await engine.search_verses(request.query, limit=request.limit)

    return VerseSearchResponse(verses=[AyahResponse(**r) for r in results], count=len(results))


# ==========================================
# Quotation Validation Endpoint
# ==========================================


@router.post("/validate", response_model=QuotationValidationResponse)
async def validate_quotation(request: QuotationValidationRequest, db_session=Depends(get_sync_session)):
    """
    Validate if text is from the Quran.

    Returns match confidence and suggested ayah if similar.
    """
    validator = get_quotation_validator(db_session)
    result = await validator.validate(request.text)

    return QuotationValidationResponse(**result)


# ==========================================
# NL2SQL Analytics Endpoint
# ==========================================


@router.post("/analytics", response_model=NL2SQLResponse)
async def quran_analytics(request: NL2SQLRequest, db_session=Depends(get_sync_session)):
    """
    Execute analytics queries on Quran data.

    Converts natural language to SQL and returns results.
    Examples:
    - "كم عدد آيات سورة البقرة؟"
    - "What is the longest surah?"
    - "How many Meccan surahs?"
    """
    engine = get_nl2sql_engine(db_session)

    try:
        result = await engine.execute(request.query)
        return NL2SQLResponse(**result)
    except NL2SQLQueryError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==========================================
# Tafsir Endpoint
# ==========================================


@router.get("/tafsir/{surah}:{ayah}", response_model=TafsirResponse)
async def get_tafsir(surah: int, ayah: int, source: Optional[str] = None, db_session=Depends(get_sync_session)):
    """
    Get tafsir (commentary) for a specific ayah.

    Supports multiple sources: ibn-kathir, al-jalalayn, al-qurtubi
    """
    engine = get_tafsir_engine(db_session)

    try:
        result = await engine.get_tafsir(f"{surah}:{ayah}", source=source)
        return TafsirResponse(**result)
    except TafsirNotFoundError:
        raise HTTPException(status_code=404, detail=f"Tafsir not found for {surah}:{ayah}")


@router.get("/tafsir-sources", response_model=list[dict])
async def list_tafsir_sources(db_session=Depends(get_sync_session)):
    """
    List all available tafsir sources.

    Returns metadata about available tafsir collections.
    """
    engine = get_tafsir_engine(db_session)
    return engine.list_sources()
