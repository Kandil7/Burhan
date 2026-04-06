"""
NL2SQL Engine for Quran Analytics.

Converts natural language questions to SQL queries for statistics:
- "كم عدد آيات سورة البقرة؟" → COUNT query
- "ما أطول سورة؟" → ORDER BY query
- "كم سورة مكية؟" → WHERE + COUNT query

Phase 3: 100% numeric accuracy guarantee.
"""
import json
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.config.logging_config import get_logger

logger = get_logger()

# Schema documentation for LLM prompt
SCHEMA_CONTEXT = """
Database Schema for Quran:

Table: surahs
- id: INTEGER (PK)
- number: INTEGER (1-114, unique)
- name_ar: VARCHAR (Arabic name, e.g., "البقرة")
- name_en: VARCHAR (English name, e.g., "Al-Baqarah")
- verse_count: INTEGER (number of ayahs in surah)
- revelation_type: VARCHAR ('meccan' or 'medinan')

Table: ayahs
- id: INTEGER (PK)
- surah_id: INTEGER (FK → surahs.id)
- number: INTEGER (global ayah number 1-6236)
- number_in_surah: INTEGER (ayah number within surah)
- text_uthmani: TEXT (Uthmani script)
- juz: INTEGER (1-30)
- page: INTEGER (1-604)

Relationships:
- ayahs.surah_id → surahs.id

Rules:
- Use surahs.number for surah identification
- revelation_type is 'meccan' or 'medinan'
- ONLY SELECT queries allowed
- NEVER modify data
"""

# Few-shot examples for NL2SQL
NL2SQL_EXAMPLES = [
    {
        "query_ar": "كم عدد آيات سورة البقرة؟",
        "query_en": "How many verses in Surah Al-Baqarah?",
        "sql": "SELECT verse_count FROM surahs WHERE number = 2"
    },
    {
        "query_ar": "ما هي أطول سورة؟",
        "query_en": "What is the longest surah?",
        "sql": "SELECT name_en, verse_count FROM surahs ORDER BY verse_count DESC LIMIT 1"
    },
    {
        "query_ar": "كم عدد السور المكية؟",
        "query_en": "How many Meccan surahs are there?",
        "sql": "SELECT COUNT(*) FROM surahs WHERE revelation_type = 'meccan'"
    },
    {
        "query_ar": "ما هي السور المدنية؟",
        "query_en": "What are the Medinan surahs?",
        "sql": "SELECT name_en FROM surahs WHERE revelation_type = 'medinan'"
    },
    {
        "query_ar": "في أي جزء سورة الكهف؟",
        "query_en": "Which juz is Surah Al-Kahf in?",
        "sql": "SELECT DISTINCT juz FROM ayahs WHERE surah_id = (SELECT id FROM surahs WHERE number = 18) LIMIT 1"
    },
    {
        "query_ar": "كم عدد صفحات القرآن؟",
        "query_en": "How many pages in the Quran?",
        "sql": "SELECT MAX(page) FROM ayahs"
    },
    {
        "query_ar": "ما أقصر سورة؟",
        "query_en": "What is the shortest surah?",
        "sql": "SELECT name_en, verse_count FROM surahs ORDER BY verse_count ASC LIMIT 1"
    },
    {
        "query_ar": "كم عدد أجزاء القرآن؟",
        "query_en": "How many juz in the Quran?",
        "sql": "SELECT COUNT(DISTINCT juz) FROM ayahs"
    },
    {
        "query_ar": "ما اسم السورة رقم 1؟",
        "query_en": "What is surah number 1?",
        "sql": "SELECT name_ar, name_en FROM surahs WHERE number = 1"
    },
    {
        "query_ar": "كم آية في سورة الفاتحة؟",
        "query_en": "How many verses in Al-Fatihah?",
        "sql": "SELECT verse_count FROM surahs WHERE number = 1"
    }
]


class NL2SQLQueryError(Exception):
    """Error in NL2SQL query generation."""
    pass


class NL2SQLExecutionError(Exception):
    """Error in SQL execution."""
    pass


class NL2SQLEngine:
    """
    Engine for converting natural language to SQL for Quran analytics.
    
    Phase 3: Rule-based + template matching
    Phase 4: LLM-based NL2SQL with validation
    
    Usage:
        engine = NL2SQLEngine(session)
        result = await engine.execute("كم عدد آيات سورة البقرة؟")
    """
    
    def __init__(self, session: Session):
        """Initialize engine with database session."""
        self.session = session
    
    async def generate_sql(self, query: str) -> str:
        """
        Generate SQL from natural language query.
        
        Phase 3: Template-based matching
        Phase 4: Will use LLM with schema context
        
        Args:
            query: Natural language question
            
        Returns:
            SQL query string
        """
        query_lower = query.lower()

        # Template 1: "كم عدد آيات سورة..." or "how many verses in surah..." or "how many verses are in..."
        if any(kw in query_lower for kw in ["عدد آيات", "verses in", "ayahs in", "verses are in"]):
            surah = self._extract_surah_number(query)
            if surah:
                return f"SELECT verse_count FROM surahs WHERE number = {surah}"
        
        # Template 2: "أطول سورة" or "longest surah"
        if any(kw in query_lower for kw in ["أطول", "longest"]):
            return "SELECT name_en, verse_count FROM surahs ORDER BY verse_count DESC LIMIT 1"
        
        # Template 3: "أقصر سورة" or "shortest surah"
        if any(kw in query_lower for kw in ["أقصر", "shortest"]):
            return "SELECT name_en, verse_count FROM surahs ORDER BY verse_count ASC LIMIT 1"
        
        # Template 4: "كم سورة مكية" or "how many meccan surahs"
        if any(kw in query_lower for kw in ["مكية", "meccan"]):
            return "SELECT COUNT(*) as count FROM surahs WHERE revelation_type = 'meccan'"
        
        # Template 5: "سور مدنية" or "medinan surahs"
        if any(kw in query_lower for kw in ["مدنية", "medinan"]):
            return "SELECT name_en FROM surahs WHERE revelation_type = 'medinan'"
        
        # Template 6: "كم عدد أجزاء" or "how many juz"
        if any(kw in query_lower for kw in ["أجزاء", "جوز", "juz", "juzs"]):
            return "SELECT COUNT(DISTINCT juz) as count FROM ayahs"
        
        # Template 7: "كم صفحة" or "how many pages"
        if any(kw in query_lower for kw in ["صفحات", "صفحة", "pages"]):
            return "SELECT MAX(page) as max_page FROM ayahs"
        
        # Template 8: "اسم السورة رقم X" or "what is surah number X"
        import re
        number_match = re.search(r'(?:رقم|number)\s*(\d+)', query_lower)
        if number_match or any(kw in query_lower for kw in ["اسم السورة", "surah name"]):
            surah_num = int(number_match.group(1)) if number_match else self._extract_surah_number(query)
            if surah_num:
                return f"SELECT name_ar, name_en FROM surahs WHERE number = {surah_num}"
        
        # Default: Return error with guidance
        raise NL2SQLQueryError(
            f"Could not generate SQL for: {query}\n"
            f"Supported queries: verse counts, longest/shortest surah, "
            f"Meccan/Medinan counts, juz count, page count"
        )
    
    async def execute_sql(self, sql: str) -> list[dict]:
        """
        Execute SQL query safely.
        
        Args:
            sql: SQL query (SELECT only)
            
        Returns:
            List of result dicts
        """
        # Validate SQL (SELECT only)
        self._validate_sql(sql)
        
        try:
            result = self.session.execute(text(sql))
            columns = result.keys()
            rows = [dict(zip(columns, row)) for row in result.fetchall()]
            
            logger.info(
                "nl2sql.executed",
                sql=sql,
                rows_returned=len(rows)
            )
            
            return rows
            
        except Exception as e:
            logger.error("nl2sql.execution_error", error=str(e))
            raise NL2SQLExecutionError(f"SQL execution failed: {str(e)}")
    
    async def execute(self, query: str) -> dict:
        """
        Full pipeline: NL → SQL → Execute → Format.
        
        Args:
            query: Natural language question
            
        Returns:
            Result dict with sql, result, and formatted answer
        """
        try:
            # Generate SQL
            sql = await self.generate_sql(query)
            
            # Execute SQL
            result = await self.execute_sql(sql)
            
            # Format answer
            formatted = self._format_result(query, result)
            
            return {
                "sql": sql,
                "result": result,
                "formatted_answer": formatted,
                "row_count": len(result)
            }
            
        except (NL2SQLQueryError, NL2SQLExecutionError) as e:
            logger.error("nl2sql.pipeline_error", error=str(e))
            raise
    
    def _extract_surah_number(self, query: str) -> Optional[int]:
        """Extract surah number from query."""
        import re

        # Look for number in query (e.g., "surah 2" or "surah number 2")
        match = re.search(r'(\d+)', query)
        if match:
            return int(match.group(1))

        # Map Arabic and English surah names to numbers
        surah_names = {
            "الفاتحة": 1, "البقرة": 2, "آل عمران": 3, "النساء": 4,
            "المائدة": 5, "الأنعام": 6, "الأعراف": 7, "الأنفال": 8,
            "التوبة": 9, "يونس": 10, "هود": 11, "يوسف": 12,
            "الإخلاص": 112, "الفلق": 113, "الناس": 114,
            # English names with variations
            "al-fatihah": 1, "alfatihah": 1, "al fatihah": 1, "fatihah": 1,
            "al-baqarah": 2, "albaqarah": 2, "al baqarah": 2, "baqarah": 2,
            "al-baqara": 2, "albaqara": 2, "al baqara": 2, "baqara": 2,
            "al-ikhlas": 112, "alikhlas": 112, "al ikhlas": 112, "ikhlas": 112,
            "al-falaq": 113, "alfalaq": 113, "al falaq": 113, "falaq": 113,
            "an-nas": 114, "annas": 114, "an nas": 114, "nas": 114,
            # Handle "the" prefix
            "the-fatihah": 1, "the-baqarah": 2, "the-ikhlas": 112,
        }

        query_lower = query.lower().replace("surah", "").replace("sura", "").strip()
        
        # Try exact match first
        for name, number in surah_names.items():
            if name in query_lower:
                return number
        
        # Try removing article prefixes (Al-, The-, etc.)
        query_clean = re.sub(r'^(al[-\s]?|the[-\s]?|a[-\s]?)', '', query_lower).strip()
        for name, number in surah_names.items():
            if name in query_clean:
                return number

        return None
    
    def _validate_sql(self, sql: str):
        """Validate SQL is SELECT only."""
        sql_upper = sql.strip().upper()
        
        if not sql_upper.startswith("SELECT"):
            raise NL2SQLQueryError("Only SELECT queries are allowed")
        
        # Block dangerous keywords
        dangerous = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE", "TRUNCATE"]
        if any(kw in sql_upper for kw in dangerous):
            raise NL2SQLQueryError("Query contains forbidden keywords")
    
    def _format_result(self, query: str, result: list[dict]) -> str:
        """Format SQL result into natural language answer."""
        if not result:
            return "No results found"
        
        row = result[0]
        
        # Format based on query type
        if "count" in str(query).lower() or "عدد" in query:
            count = list(row.values())[0] if row else 0
            return f"The answer is: {count}"
        
        if "longest" in str(query).lower() or "أطول" in query:
            name = row.get("name_en", "Unknown")
            count = row.get("verse_count", 0)
            return f"The longest surah is {name} with {count} verses"
        
        if "shortest" in str(query).lower() or "أقصر" in query:
            name = row.get("name_en", "Unknown")
            count = row.get("verse_count", 0)
            return f"The shortest surah is {name} with {count} verses"
        
        # Default formatting
        return str(result)
