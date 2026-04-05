"""
Quran Data Loader for Athar Islamic QA system.

Loads complete Quran data from:
- Quran.com API (primary source)
- Local JSON files (fallback)

Inserts surahs, ayahs, translations with validation.
Phase 3: Foundation for all Quran pipeline features.
"""
import json
from pathlib import Path
from typing import Optional

import httpx
from sqlalchemy.orm import Session

from src.data.models.quran import Surah, Ayah, Translation, Tafsir
from src.config.logging_config import get_logger

logger = get_logger()

# Quran.com API v4 endpoints
QURAN_API_BASE = "https://api.quran.com/api/v4"
CHAPTERS_ENDPOINT = f"{QURAN_API_BASE}/chapters"
AYAH_ENDPOINT = f"{QURAN_API_BASE}/verses/by_chapter"


class QuranLoader:
    """
    Loader for Quran data from API or local files.
    
    Usage:
        loader = QuranLoader(session)
        await loader.load_from_api(language="en")
        # or
        loader.load_from_json("data/seed/quran_full.json")
    """
    
    def __init__(self, session: Session):
        """
        Initialize loader with database session.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
    
    async def load_from_api(self, language: str = "en") -> dict:
        """
        Load complete Quran data from Quran.com API.
        
        Args:
            language: Translation language code (default: "en" for English)
            
        Returns:
            Statistics dict with counts of loaded data
        """
        stats = {"surahs": 0, "ayahs": 0, "translations": 0}
        
        try:
            # Step 1: Load all surahs
            logger.info("quran.loader.loading_surahs")
            surahs = await self._load_surahs()
            stats["surahs"] = len(surahs)
            
            # Step 2: Load ayahs for each surah with translations
            logger.info("quran.loader.loading_ayahs", surah_count=len(surahs))
            for surah in surahs:
                ayah_count = await self._load_ayahs_for_surah(surah["id"], language)
                stats["ayahs"] += ayah_count
                stats["translations"] += ayah_count  # 1 translation per ayah
            
            logger.info(
                "quran.loader.complete",
                surahs=stats["surahs"],
                ayahs=stats["ayahs"],
                translations=stats["translations"]
            )
            
            return stats
            
        except Exception as e:
            logger.error("quran.loader.error", error=str(e))
            self.session.rollback()
            raise
    
    async def _load_surahs(self) -> list[dict]:
        """Load all 114 surahs from API."""
        async with httpx.AsyncClient() as client:
            response = await client.get(CHAPTERS_ENDPOINT)
            response.raise_for_status()
            data = response.json()
            
            surahs_data = data.get("chapters", [])
            
            for surah_data in surahs_data:
                # Check if surah already exists
                existing = self.session.query(Surah).filter_by(
                    number=surah_data["id"]
                ).first()
                
                if existing:
                    logger.debug(
                        "quran.loader.surah_exists",
                        number=surah_data["id"],
                        name=surah_data.get("name_simple")
                    )
                    continue
                
                # Create surah
                surah = Surah(
                    number=surah_data["id"],
                    name_ar=surah_data.get("name_arabic", ""),
                    name_en=surah_data.get("name_simple", ""),
                    verse_count=surah_data.get("verses_count", 0),
                    revelation_type=surah_data.get("revelation_place", "meccan").lower()
                )
                
                self.session.add(surah)
                logger.debug(
                    "quran.loader.surah_added",
                    number=surah.number,
                    name=surah.name_en
                )
            
            self.session.commit()
            logger.info("quran.loader.surahs_committed", count=len(surahs_data))
            
            return surahs_data
    
    async def _load_ayahs_for_surah(
        self,
        surah_number: int,
        language: str = "en"
    ) -> int:
        """
        Load all ayahs for a specific surah.
        
        Args:
            surah_number: Surah number (1-114)
            language: Translation language code
            
        Returns:
            Number of ayahs loaded
        """
        count = 0
        
        # Get surah from DB
        surah = self.session.query(Surah).filter_by(number=surah_number).first()
        if not surah:
            logger.error("quran.loader.surah_not_found", number=surah_number)
            return 0
        
        # Load ayahs page by page
        page = 1
        per_page = 50  # API limit
        
        while True:
            async with httpx.AsyncClient() as client:
                # Fetch ayahs with translation
                params = {
                    "chapter_number": surah_number,
                    "page": page,
                    "per_page": per_page,
                    "words": "false",
                    "translations": language,
                    "fields": "text_uthmani,text_simple,juz,page,hizb_number,rub_el_hizb_number,sajdah"
                }
                
                response = await client.get(AYAH_ENDPOINT, params=params)
                response.raise_for_status()
                data = response.json()
                
                ayahs = data.get("verses", [])
                if not ayahs:
                    break
                
                for ayah_data in ayahs:
                    # Check if ayah already exists
                    existing = self.session.query(Ayah).filter_by(
                        surah_id=surah.id,
                        number_in_surah=ayah_data["verse_key"].split(":")[1]
                    ).first()
                    
                    if existing:
                        count += 1
                        continue
                    
                    # Parse verse_key (e.g., "2:255")
                    surah_num, ayah_num = ayah_data["verse_key"].split(":")
                    
                    # Create ayah
                    ayah = Ayah(
                        surah_id=surah.id,
                        number=ayah_data.get("id"),
                        number_in_surah=int(ayah_num),
                        text_uthmani=ayah_data.get("text_uthmani", ""),
                        text_simple=ayah_data.get("text_simple"),
                        juz=ayah_data.get("juz_number", 1),
                        page=ayah_data.get("page_number", 1),
                        hizb=ayah_data.get("hizb_number"),
                        rub_el_hizb=ayah_data.get("rub_el_hizb_number"),
                        sajdah=ayah_data.get("sajdah", False),
                        surah_name=surah.name_en,
                        surah_name_ar=surah.name_ar
                    )
                    
                    self.session.add(ayah)
                    
                    # Add translation if available
                    if ayah_data.get("translations"):
                        for translation in ayah_data["translations"]:
                            translator_name = translation.get("resource_name", "Unknown")
                            trans = Translation(
                                ayah_id=ayah.id,
                                language=language,
                                translator=translator_name,
                                text=translation.get("text", "")
                            )
                            self.session.add(trans)
                    
                    count += 1
                
                # Check if there are more pages
                pagination = data.get("pagination", {})
                if page >= pagination.get("total_pages", 1):
                    break
                
                page += 1
        
        self.session.commit()
        logger.info(
            "quran.loader.ayahs_loaded",
            surah=surah_number,
            count=count
        )
        
        return count
    
    def load_from_json(self, file_path: str) -> dict:
        """
        Load Quran data from local JSON file.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            Statistics dict
        """
        stats = {"surahs": 0, "ayahs": 0, "translations": 0}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Load surahs
            for surah_data in data.get("surahs", []):
                surah = Surah(
                    number=surah_data["number"],
                    name_ar=surah_data.get("name_ar", ""),
                    name_en=surah_data.get("name_en", ""),
                    verse_count=surah_data.get("verse_count", 0),
                    revelation_type=surah_data.get("revelation_type", "meccan")
                )
                self.session.add(surah)
                stats["surahs"] += 1
            
            self.session.commit()
            
            # Load ayahs
            for ayah_data in data.get("ayahs", []):
                surah = self.session.query(Surah).filter_by(
                    number=ayah_data["surah_number"]
                ).first()
                
                if not surah:
                    continue
                
                ayah = Ayah(
                    surah_id=surah.id,
                    number=ayah_data.get("number"),
                    number_in_surah=ayah_data.get("number_in_surah"),
                    text_uthmani=ayah_data.get("text_uthmani", ""),
                    text_simple=ayah_data.get("text_simple"),
                    juz=ayah_data.get("juz", 1),
                    page=ayah_data.get("page", 1),
                    hizb=ayah_data.get("hizb"),
                    rub_el_hizb=ayah_data.get("rub_el_hizb"),
                    sajdah=ayah_data.get("sajdah", False),
                    surah_name=surah.name_en,
                    surah_name_ar=surah.name_ar
                )
                
                self.session.add(ayah)
                stats["ayahs"] += 1
                
                # Add translations
                for trans_data in ayah_data.get("translations", []):
                    trans = Translation(
                        ayah_id=ayah.id,
                        language=trans_data.get("language", "en"),
                        translator=trans_data.get("translator"),
                        text=trans_data.get("text", "")
                    )
                    self.session.add(trans)
                    stats["translations"] += 1
            
            self.session.commit()
            logger.info(
                "quran.loader.json_loaded",
                file=file_path,
                **stats
            )
            
            return stats
            
        except Exception as e:
            logger.error("quran.loader.json_error", error=str(e))
            self.session.rollback()
            raise
