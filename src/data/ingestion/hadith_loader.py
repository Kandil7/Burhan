"""
Hadith Collection Loader for Athar Islamic QA system.

Ingests hadith collections from:
- Sunnah.com API
- Local JSON files

Processes, validates, and chunks hadith for RAG pipeline.
Phase 4: Foundation for hadith-based fiqh answers.
"""
import json
from pathlib import Path
from typing import Optional

import httpx
from sqlalchemy.orm import Session

from src.data.models.quran import Surah, Ayah
from src.config.logging_config import get_logger

logger = get_logger()

# Sunnah.com API (if available)
SUNNAH_API_BASE = "https://sunnah.com/api/v1"  # Placeholder

VALID_GRADES = {"sahih", "hasan", "da'if", "weak", "strong", "good"}


class HadithLoaderError(Exception):
    """Error in hadith loading."""
    pass


class HadithLoader:
    """
    Loader for hadith collections.
    
    Usage:
        loader = HadithLoader(session)
        await loader.load_from_api(["bukhari", "muslim"])
        # or
        loader.load_from_json("data/raw/hadith/bukhari.json")
    """
    
    def __init__(self, session: Optional[Session] = None):
        """Initialize loader."""
        self.session = session
    
    async def load_from_api(self, collections: list[str]) -> dict:
        """
        Load hadith from Sunnah.com API.
        
        Args:
            collections: List of collection names
            
        Returns:
            Statistics dict
        """
        stats = {"collections": 0, "hadiths": 0, "errors": 0}
        
        for collection in collections:
            try:
                # Fetch collection metadata
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{SUNNAH_API_BASE}/collections/{collection}"
                    )
                    response.raise_for_status()
                    collection_data = response.json()
                
                # Fetch hadiths
                hadiths = await self._fetch_collection_hadiths(collection)
                stats["hadiths"] += len(hadiths)
                stats["collections"] += 1
                
                logger.info(
                    "hadith.collection_loaded",
                    collection=collection,
                    count=len(hadiths)
                )
                
            except Exception as e:
                logger.error("hadith.collection_error", collection=collection, error=str(e))
                stats["errors"] += 1
        
        return stats
    
    async def _fetch_collection_hadiths(self, collection: str) -> list[dict]:
        """Fetch all hadiths from a collection."""
        hadiths = []
        page = 1
        
        async with httpx.AsyncClient() as client:
            while True:
                response = await client.get(
                    f"{SUNNAH_API_BASE}/collections/{collection}/hadiths",
                    params={"page": page, "limit": 100}
                )
                response.raise_for_status()
                data = response.json()
                
                if not data.get("hadiths"):
                    break
                
                hadiths.extend(data["hadiths"])
                
                if page >= data.get("pagination", {}).get("total_pages", 1):
                    break
                
                page += 1
        
        return hadiths
    
    def load_from_json(self, file_path: str) -> list[dict]:
        """
        Load hadith from local JSON file.
        
        Expected format:
        [
          {
            "collection": "bukhari",
            "book": "Revelation",
            "hadith_number": 1,
            "arabic": "إنما الأعمال بالنيات...",
            "english": "Actions are judged by intentions...",
            "grade": "Sahih",
            "narrator": "Umar ibn al-Khattab"
          }
        ]
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            List of hadith dicts
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                hadiths = json.load(f)
            
            # Validate
            valid_hadiths = [h for h in hadiths if self.validate_hadith(h)]
            
            logger.info(
                "hadith.json_loaded",
                file=file_path,
                total=len(hadiths),
                valid=len(valid_hadiths)
            )
            
            return valid_hadiths
            
        except Exception as e:
            logger.error("hadith.json_error", file=file_path, error=str(e))
            raise HadithLoaderError(f"Failed to load hadith JSON: {str(e)}")
    
    def validate_hadith(self, hadith: dict) -> bool:
        """
        Validate hadith structure and grade.
        
        Args:
            hadith: Hadith dict
            
        Returns:
            True if valid
        """
        required_fields = ["collection", "hadith_number"]
        
        # Check required fields
        for field in required_fields:
            if field not in hadith:
                logger.warning("hadith.missing_field", field=field, hadith=hadith.get("hadith_number"))
                return False
        
        # Validate grade if present
        grade = hadith.get("grade", "").lower()
        if grade and grade not in VALID_GRADES:
            logger.warning("hadith.invalid_grade", grade=grade)
        
        return True
    
    def chunk_hadith_collection(self, hadiths: list[dict]) -> list[dict]:
        """
        Chunk hadith collection for embedding.
        
        Each hadith is ONE chunk (never split).
        
        Args:
            hadiths: List of hadith dicts
            
        Returns:
            List of chunk dicts ready for embedding
        """
        chunks = []
        
        for i, hadith in enumerate(hadiths):
            # Combine Arabic + English for better embedding
            text_parts = []
            if hadith.get("arabic"):
                text_parts.append(hadith["arabic"])
            if hadith.get("english"):
                text_parts.append(hadith["english"])
            
            content = "\n".join(text_parts)
            
            chunk = {
                "chunk_index": i,
                "content": content,
                "metadata": {
                    "collection": hadith.get("collection", ""),
                    "book": hadith.get("book", ""),
                    "hadith_number": hadith.get("hadith_number", ""),
                    "grade": hadith.get("grade", ""),
                    "narrator": hadith.get("narrator", ""),
                    "source": "hadith",
                    "language": "ar",
                }
            }
            chunks.append(chunk)
        
        logger.info("hadith.chunked", total=len(chunks))
        return chunks
