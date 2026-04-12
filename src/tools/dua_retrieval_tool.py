"""
Dua Retrieval Tool for Athar Islamic QA system.

Retrieves verified duas and adhkar from authenticated sources (Hisn al-Muslim).
No LLM generation - returns exact text with translations and references.

Based on Fanar-Sadiq architecture: Verified sources only, no generation.
"""
import json
from pathlib import Path
from typing import Optional

from src.tools.base import BaseTool, ToolOutput
from src.config.logging_config import get_logger

logger = get_logger()

# Path to duas database
DUAS_DB_PATH = Path(__file__).parent.parent.parent / "data" / "seed" / "duas.json"
AZKAR_DB_PATH = Path(__file__).parent.parent.parent / "data" / "seed" / "azkar_imported.json"


class DuaRetrievalTool(BaseTool):
    """
    Tool for retrieving verified duas and adhkar.
    
    Retrieves from authenticated database only - no LLM generation.
    Supports search by occasion, category, or semantic query.
    Integrates both Hisn al-Muslim and azkar-db datasets.
    
    Usage:
        tool = DuaRetrievalTool()
        result = await tool.execute(occasion="morning")
    """
    
    name = "dua_retrieval_tool"
    
    def __init__(self, duas_path: Optional[Path] = None, azkar_path: Optional[Path] = None):
        """Initialize with duas databases."""
        self.duas_path = duas_path or DUAS_DB_PATH
        self.azkar_path = azkar_path or AZKAR_DB_PATH
        self.duas = self._load_duas()
        self.azkar = self._load_azkar()
        logger.info(
            "dua.tool_initialized",
            duas_count=len(self.duas),
            azkar_count=len(self.azkar),
            total=len(self.duas) + len(self.azkar)
        )
    
    def _load_duas(self) -> list[dict]:
        """Load duas from JSON database (Hisn al-Muslim)."""
        try:
            if self.duas_path.exists():
                with open(self.duas_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error("dua.load_error", error=str(e))
        return []
    
    def _load_azkar(self) -> list[dict]:
        """Load azkar from imported database."""
        try:
            if self.azkar_path.exists():
                with open(self.azkar_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error("azkar.load_error", error=str(e))
        return []
    
    async def execute(
        self,
        query: str = "",
        occasion: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 5,
        **kwargs
    ) -> ToolOutput:
        """
        Retrieve duas based on occasion, category, or query.
        
        Searches both Hisn al-Muslim and azkar-db datasets.
        
        Args:
            query: User query for semantic search
            occasion: Specific occasion (morning, evening, travel, etc.)
            category: Category (morning_evening, prayer, travel, food, protection)
            limit: Maximum number of duas to return
            
        Returns:
            ToolOutput with list of verified duas
        """
        try:
            # Combine both datasets
            all_duas = self.duas + self.azkar

            # Category to occasion mapping for user-friendly queries
            category_to_occasion = {
                "morning": "morning",
                "evening": "evening",
                "morning_evening": "morning_evening",
                "sleep": "before_sleep",
                "wake": "upon_waking",
                "food": "before_eating",
                "eating": "before_eating",
                "travel": "traveling",
                "protection": "protection",
                "prayer": "prayer",
            }

            # Filter by category (with occasion fallback)
            if category:
                category_lower = category.lower()
                # Try exact category match first
                filtered = [d for d in all_duas if d.get("category") == category_lower]
                if not filtered:
                    # Try occasion mapping
                    mapped_occasion = category_to_occasion.get(category_lower, category_lower)
                    filtered = [d for d in all_duas if mapped_occasion in d.get("occasion", "").lower()]
                if not filtered:
                    # Try partial match in occasion or category
                    filtered = [d for d in all_duas if category_lower in d.get("occasion", "").lower() or category_lower in d.get("category", "").lower()]
                all_duas = filtered

            # Filter by occasion (with broader matching)
            if occasion:
                occasion_lower = occasion.lower()
                all_duas = [
                    d for d in all_duas
                    if occasion_lower in d.get("occasion", "").lower()
                    or occasion_lower in d.get("category", "").lower()
                ]
            
            # Semantic search by query (simple keyword matching for Phase 2)
            if query and not occasion and not category:
                all_duas = self._search_duas(query, all_duas)
            
            # Limit results
            all_duas = all_duas[:limit]
            
            # Format response
            result = {
                "duas": all_duas,
                "count": len(all_duas),
                "filters": {
                    "occasion": occasion,
                    "category": category,
                    "query": query if query else None
                },
                "sources": {
                    "hisn_al_muslim": len(self.duas),
                    "azkar_db": len(self.azkar)
                }
            }
            
            logger.info(
                "dua.retrieved",
                count=len(all_duas),
                occasion=occasion,
                category=category
            )
            
            return ToolOutput(
                result=result,
                success=True,
                metadata={
                    "source": "Hisn al-Muslim + Azkar Database (https://github.com/osamayy/azkar-db)",
                    "note": "All duas are from verified sources with proper references"
                }
            )
            
        except Exception as e:
            logger.error("dua.retrieval_error", error=str(e))
            return ToolOutput(
                result={},
                success=False,
                error=f"Error retrieving duas: {str(e)}"
            )
    
    def _search_duas(self, query: str, duas: list[dict]) -> list[dict]:
        """
        Search duas by query terms (simple keyword matching).
        
        Phase 2: Keyword matching
        Phase 4: Will use embedding-based semantic search
        """
        query_lower = query.lower()
        query_terms = query_lower.split()
        
        scored_duas = []
        for dua in duas:
            score = 0
            
            # Search in Arabic text
            arabic_text = dua.get("arabic_text", "").lower()
            for term in query_terms:
                if term in arabic_text:
                    score += 3  # High weight for Arabic match
            
            # Search in translation
            translation = dua.get("translation", "").lower()
            for term in query_terms:
                if term in translation:
                    score += 2  # Medium weight for translation match
            
            # Search in transliteration
            transliteration = dua.get("transliteration", "").lower()
            for term in query_terms:
                if term in transliteration:
                    score += 1  # Low weight for transliteration match
            
            # Search in occasion and category
            if query_lower in dua.get("occasion", "").lower():
                score += 2
            if query_lower in dua.get("category", "").lower():
                score += 2
            
            if score > 0:
                scored_duas.append((score, dua))
        
        # Sort by score (descending)
        scored_duas.sort(key=lambda x: x[0], reverse=True)
        
        return [dua for score, dua in scored_duas]
    
    def get_occasions(self) -> list[str]:
        """Get list of all available occasions."""
        occasions = set()
        for dua in self.duas + self.azkar:
            if dua.get("occasion"):
                occasions.add(dua["occasion"])
            if dua.get("category"):
                occasions.add(dua["category"])
        return sorted(list(occasions))
    
    def get_categories(self) -> list[str]:
        """Get list of all available categories."""
        categories = set()
        for dua in self.duas + self.azkar:
            if dua.get("category"):
                categories.add(dua["category"])
        return sorted(list(categories))
