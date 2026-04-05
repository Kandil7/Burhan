"""
Tafsir Retrieval Engine for Athar Islamic QA system.

Retrieves scholarly commentaries on Quran verses from:
- Ibn Kathir (most popular)
- Al-Jalalayn (concise)
- Al-Qurtubi (fiqh-focused)

Phase 3: Foundation for Quran interpretation features.
"""
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import or_

from src.data.models.quran import Surah, Ayah, Tafsir
from src.quran.verse_retrieval import VerseRetrievalEngine
from src.config.logging_config import get_logger

logger = get_logger()


class TafsirRetrievalError(Exception):
    """Error in tafsir retrieval."""
    pass


class TafsirNotFoundError(TafsirRetrievalError):
    """Tafsir not found for verse."""
    pass


class TafsirRetrievalEngine:
    """
    Engine for retrieving tafsir (commentaries) on Quran verses.
    
    Usage:
        engine = TafsirRetrievalEngine(session)
        tafsir = await engine.get_tafsir("2:255", source="ibn-kathir")
    """
    
    AVAILABLE_SOURCES = {
        "ibn-kathir": {
            "name_ar": "تفسير ابن كثير",
            "name_en": "Ibn Kathir",
            "author": "Ismail ibn Kathir",
            "language": "ar"
        },
        "al-jalalayn": {
            "name_ar": "تفسير الجلالين",
            "name_en": "Al-Jalalayn",
            "author": "Jalal ad-Din al-Mahalli and Jalal ad-Din as-Suyuti",
            "language": "ar"
        },
        "al-qurtubi": {
            "name_ar": "تفسير القرطبي",
            "name_en": "Al-Qurtubi",
            "author": "Abu 'Abdullah Al-Qurtubi",
            "language": "ar"
        }
    }
    
    def __init__(self, session: Session):
        """
        Initialize engine with database session.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
        self.verse_engine = VerseRetrievalEngine(session)
    
    async def get_tafsir(
        self,
        ayah_reference: str,
        source: Optional[str] = None
    ) -> dict:
        """
        Get tafsir for a specific verse.
        
        Args:
            ayah_reference: Verse reference (e.g., "2:255")
            source: Tafsir source (ibn-kathir, al-jalalayn, al-qurtubi)
                   If None, returns all available sources
            
        Returns:
            Tafsir response with ayah and commentaries
        """
        try:
            # Get ayah first
            ayah = await self.verse_engine.lookup(ayah_reference, include_translation=True)
            
            # Get surah and ayah numbers
            surah_num = ayah["surah_number"]
            ayah_num = ayah["ayah_number"]
            
            # Query tafsir
            query = (
                self.session.query(Tafsir)
                .join(Ayah)
                .join(Surah)
                .filter(
                    Surah.number == surah_num,
                    Ayah.number_in_surah == ayah_num
                )
            )
            
            # Filter by source if specified
            if source:
                query = query.filter(Tafsir.source_name == source)
                tafsirs = query.all()
                
                if not tafsirs:
                    raise TafsirNotFoundError(
                        f"Tafsir from '{source}' not found for {ayah_reference}"
                    )
            else:
                tafsirs = query.all()
            
            # Format response
            result = {
                "ayah": ayah,
                "tafsirs": [
                    {
                        "source": t.source_name,
                        "author": self.AVAILABLE_SOURCES.get(t.source_name, {}).get("author", t.author),
                        "text": t.text,
                        "language": t.language
                    }
                    for t in tafsirs
                ],
                "available_sources": list(set(t.source_name for t in tafsirs))
            }
            
            logger.info(
                "tafsir.retrieved",
                reference=ayah_reference,
                sources=result["available_sources"]
            )
            
            return result
            
        except TafsirNotFoundError:
            raise
        except Exception as e:
            logger.error("tafsir.retrieval_error", error=str(e))
            raise TafsirRetrievalError(f"Error retrieving tafsir: {str(e)}")
    
    async def search_tafsir(
        self,
        query: str,
        source: Optional[str] = None,
        limit: int = 5
    ) -> list[dict]:
        """
        Search tafsir text by keyword.
        
        Args:
            query: Search query
            source: Filter by tafsir source
            limit: Maximum results
            
        Returns:
            List of tafsir passages matching query
        """
        try:
            # Full-text search in tafsir text
            tafsirs = (
                self.session.query(Tafsir)
                .join(Ayah)
                .join(Surah)
                .filter(Tafsir.text.contains(query))
            )
            
            if source:
                tafsirs = tafsirs.filter(Tafsir.source_name == source)
            
            tafsirs = tafsirs.limit(limit).all()
            
            results = []
            for tafsir in tafsirs:
                results.append({
                    "surah_number": tafsir.ayah.surah.number,
                    "surah_name_en": tafsir.ayah.surah.name_en,
                    "ayah_number": tafsir.ayah.number_in_surah,
                    "ayah_text": tafsir.ayah.text_uthmani[:100] + "...",
                    "source": tafsir.source_name,
                    "author": self.AVAILABLE_SOURCES.get(tafsir.source_name, {}).get("author", tafsir.author),
                    "tafsir_text": tafsir.text[:300] + "...",
                    "quran_url": f"https://quran.com/{tafsir.ayah.surah.number}/{tafsir.ayah.number_in_surah}"
                })
            
            logger.info(
                "tafsir.searched",
                query=query,
                results=len(results)
            )
            
            return results
            
        except Exception as e:
            logger.error("tafsir.search_error", error=str(e))
            raise TafsirRetrievalError(f"Error searching tafsir: {str(e)}")
    
    def list_sources(self) -> list[dict]:
        """
        List all available tafsir sources.
        
        Returns:
            List of source metadata
        """
        return [
            {
                "id": source_id,
                **metadata
            }
            for source_id, metadata in self.AVAILABLE_SOURCES.items()
        ]
