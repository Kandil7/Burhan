"""
NL2SQL Engine for Quran Analytics.

Fixes:
  - _extract_surah_number: name lookup runs BEFORE digit extraction to avoid
    false positives from incidental numbers (page/juz numbers in query)
  - _validate_sql: UNION, EXEC, --, ; added to blocklist
  - Template 1+: broader Arabic keyword coverage (كم آية / كم عدد آيات)
  - Typo: "جوز" → "جزء"
  - `import re` moved to module level
"""
from __future__ import annotations

import re

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.config.logging_config import get_logger

logger = get_logger()


# ── Schema context ─────────────────────────────────────────────────────────────
SCHEMA_CONTEXT = """
Database Schema for Quran:

Table: surahs
- id: INTEGER (PK)
- number: INTEGER (1-114, unique)
- name_ar: VARCHAR (Arabic name, e.g., "البقرة")
- name_en: VARCHAR (English name, e.g., "Al-Baqarah")
- verse_count: INTEGER
- revelation_type: VARCHAR ('meccan' or 'medinan')

Table: ayahs
- id: INTEGER (PK)
- surah_id: INTEGER (FK → surahs.id)
- number: INTEGER (global 1-6236)
- number_in_surah: INTEGER
- text_uthmani: TEXT
- juz: INTEGER (1-30)
- page: INTEGER (1-604)
"""

# ── Few-shot examples ─────────────────────────────────────────────────────────
NL2SQL_EXAMPLES = [
    {"query_ar": "كم عدد آيات سورة البقرة؟",
     "sql": "SELECT verse_count FROM surahs WHERE number = 2"},
    {"query_ar": "ما هي أطول سورة؟",
     "sql": "SELECT name_en, verse_count FROM surahs ORDER BY verse_count DESC LIMIT 1"},
    {"query_ar": "كم عدد السور المكية؟",
     "sql": "SELECT COUNT(*) FROM surahs WHERE revelation_type = 'meccan'"},
    {"query_ar": "ما هي السور المدنية؟",
     "sql": "SELECT name_en FROM surahs WHERE revelation_type = 'medinan'"},
    {"query_ar": "في أي جزء سورة الكهف؟",
     "sql": "SELECT DISTINCT juz FROM ayahs WHERE surah_id = "
            "(SELECT id FROM surahs WHERE number = 18) LIMIT 1"},
    {"query_ar": "كم عدد صفحات القرآن؟",
     "sql": "SELECT MAX(page) FROM ayahs"},
    {"query_ar": "ما أقصر سورة؟",
     "sql": "SELECT name_en, verse_count FROM surahs ORDER BY verse_count ASC LIMIT 1"},
    {"query_ar": "كم عدد أجزاء القرآن؟",
     "sql": "SELECT COUNT(DISTINCT juz) FROM ayahs"},
]

# ── Arabic surah name → number (full 114) ────────────────────────────────────
_SURAH_NAMES_AR: dict[str, int] = {
    "الفاتحة": 1, "البقرة": 2, "آل عمران": 3, "النساء": 4,
    "المائدة": 5, "الأنعام": 6, "الأعراف": 7, "الأنفال": 8,
    "التوبة": 9, "يونس": 10, "هود": 11, "يوسف": 12,
    "الرعد": 13, "إبراهيم": 14, "الحجر": 15, "النحل": 16,
    "الإسراء": 17, "الكهف": 18, "مريم": 19, "طه": 20,
    "الأنبياء": 21, "الحج": 22, "المؤمنون": 23, "النور": 24,
    "الفرقان": 25, "الشعراء": 26, "النمل": 27, "القصص": 28,
    "العنكبوت": 29, "الروم": 30, "لقمان": 31, "السجدة": 32,
    "الأحزاب": 33, "سبأ": 34, "فاطر": 35, "يس": 36,
    "الصافات": 37, "ص": 38, "الزمر": 39, "غافر": 40,
    "فصلت": 41, "الشورى": 42, "الزخرف": 43, "الدخان": 44,
    "الجاثية": 45, "الأحقاف": 46, "محمد": 47, "الفتح": 48,
    "الحجرات": 49, "ق": 50, "الذاريات": 51, "الطور": 52,
    "النجم": 53, "القمر": 54, "الرحمن": 55, "الواقعة": 56,
    "الحديد": 57, "المجادلة": 58, "الحشر": 59, "الممتحنة": 60,
    "الصف": 61, "الجمعة": 62, "المنافقون": 63, "التغابن": 64,
    "الطلاق": 65, "التحريم": 66, "الملك": 67, "القلم": 68,
    "الحاقة": 69, "المعارج": 70, "نوح": 71, "الجن": 72,
    "المزمل": 73, "المدثر": 74, "القيامة": 75, "الإنسان": 76,
    "المرسلات": 77, "النبأ": 78, "النازعات": 79, "عبس": 80,
    "التكوير": 81, "الانفطار": 82, "المطففين": 83, "الانشقاق": 84,
    "البروج": 85, "الطارق": 86, "الأعلى": 87, "الغاشية": 88,
    "الفجر": 89, "البلد": 90, "الشمس": 91, "الليل": 92,
    "الضحى": 93, "الشرح": 94, "التين": 95, "العلق": 96,
    "القدر": 97, "البينة": 98, "الزلزلة": 99, "العاديات": 100,
    "القارعة": 101, "التكاثر": 102, "العصر": 103, "الهمزة": 104,
    "الفيل": 105, "قريش": 106, "الماعون": 107, "الكوثر": 108,
    "الكافرون": 109, "النصر": 110, "المسد": 111, "الإخلاص": 112,
    "الفلق": 113, "الناس": 114,
}

_SURAH_NAMES_EN: dict[str, int] = {
    "al-fatihah": 1,  "alfatihah": 1,  "fatihah": 1,  "fatiha": 1,
    "al-baqarah": 2,  "albaqarah": 2,  "baqarah": 2,  "baqara": 2,
    "al-imran": 3,    "alimran": 3,    "imran": 3,
    "an-nisa": 4,     "annisa": 4,     "nisa": 4,     "nisa'": 4,
    "al-maidah": 5,   "almaidah": 5,   "maidah": 5,
    "al-kahf": 18,    "alkahf": 18,    "kahf": 18,
    "maryam": 19,     "ta-ha": 20,     "taha": 20,
    "al-ikhlas": 112, "alikhlas": 112, "ikhlas": 112,
    "al-falaq": 113,  "alfalaq": 113,  "falaq": 113,
    "an-nas": 114,    "annas": 114,    "nas": 114,
}

# Compiled SQL injection blocklist
_FORBIDDEN_SQL = re.compile(
    r"\b(DROP|DELETE|INSERT|UPDATE|ALTER|CREATE|TRUNCATE|UNION|EXEC|EXECUTE)\b"
    r"|--|/\*|\*/|;",
    re.IGNORECASE,
)


class NL2SQLQueryError(Exception):
    """Could not generate SQL from the given natural language query."""


class NL2SQLExecutionError(Exception):
    """SQL execution failed."""


class NL2SQLEngine:
    """
    Converts natural language Quran analytics questions to SQL.

    Phase 3: Template-based matching.
    Phase 4: LLM-based NL2SQL with schema context + few-shot examples.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    # ── Public API ────────────────────────────────────────────────────────────

    async def generate_sql(self, query: str) -> str:
        """
        Map natural language query to a safe SELECT statement.

        Raises NL2SQLQueryError if no template matches.
        """
        q = query.strip()
        ql = q.lower()

        # T1: verse count for a specific surah
        if any(kw in ql for kw in [
            "عدد آيات", "كم آية", "كم عدد الآيات",
            "verses in", "ayahs in", "how many verses", "how many ayahs",
        ]):
            surah = self._extract_surah_number(q)
            if surah:
                return f"SELECT verse_count FROM surahs WHERE number = {surah}"

        # T2: longest surah
        if any(kw in ql for kw in ["أطول", "longest"]):
            return "SELECT name_en, verse_count FROM surahs ORDER BY verse_count DESC LIMIT 1"

        # T3: shortest surah
        if any(kw in ql for kw in ["أقصر", "shortest"]):
            return "SELECT name_en, verse_count FROM surahs ORDER BY verse_count ASC LIMIT 1"

        # T4: Meccan surah count
        if any(kw in ql for kw in ["مكية", "meccan"]):
            return "SELECT COUNT(*) AS count FROM surahs WHERE revelation_type = 'meccan'"

        # T5: Medinan surah list
        if any(kw in ql for kw in ["مدنية", "medinan"]):
            return "SELECT name_ar, name_en FROM surahs WHERE revelation_type = 'medinan'"

        # T6: juz count / which juz
        if any(kw in ql for kw in ["أجزاء", "جزء", "juz"]):        # ← "جزء" (not "جوز")
            surah = self._extract_surah_number(q)
            if surah:
                return (
                    f"SELECT DISTINCT juz FROM ayahs "
                    f"WHERE surah_id = (SELECT id FROM surahs WHERE number = {surah}) "
                    f"ORDER BY juz LIMIT 1"
                )
            return "SELECT COUNT(DISTINCT juz) AS count FROM ayahs"

        # T7: page count
        if any(kw in ql for kw in ["صفحات", "صفحة", "pages", "page count"]):
            return "SELECT MAX(page) AS total_pages FROM ayahs"

        # T8: surah name/info by number ("السورة رقم X" / "surah number X")
        num_match = re.search(r"(?:رقم|number)\s*(\d+)", ql)
        if num_match or any(kw in ql for kw in ["اسم السورة", "surah name", "what is surah"]):
            surah_num = (
                int(num_match.group(1))
                if num_match
                else self._extract_surah_number(q)
            )
            if surah_num:
                return f"SELECT name_ar, name_en FROM surahs WHERE number = {surah_num}"

        # T9: total surah count
        if any(kw in ql for kw in ["كم سورة", "عدد السور", "how many surahs", "total surahs"]):
            return "SELECT COUNT(*) AS count FROM surahs"

        # T10: total ayah count
        if any(kw in ql for kw in ["كم آية في القرآن", "عدد آيات القرآن", "total verses", "total ayahs"]):
            return "SELECT COUNT(*) AS count FROM ayahs"

        raise NL2SQLQueryError(
            f"Could not generate SQL for: {q!r}\n"
            "Supported: verse counts, longest/shortest surah, "
            "Meccan/Medinan surahs, juz, pages, surah info by number."
        )

    async def execute_sql(self, sql: str) -> list[dict]:
        """Execute a validated SELECT query and return rows as dicts."""
        self._validate_sql(sql)
        try:
            result   = self.session.execute(text(sql))
            columns  = list(result.keys())
            rows     = [dict(zip(columns, row)) for row in result.fetchall()]
            logger.info("nl2sql.executed", sql=sql, rows=len(rows))
            return rows
        except Exception as e:
            logger.error("nl2sql.execution_error", error=str(e), exc_info=True)
            raise NL2SQLExecutionError(f"SQL execution failed: {e}") from e

    async def execute(self, query: str) -> dict:
        """Full pipeline: NL → SQL → Execute → Format."""
        sql      = await self.generate_sql(query)
        rows     = await self.execute_sql(sql)
        return {
            "sql":              sql,
            "result":           rows,
            "formatted_answer": self._format_result(query, rows),
            "row_count":        len(rows),
        }

    # ── Surah extraction ──────────────────────────────────────────────────────

    def _extract_surah_number(self, query: str) -> int | None:
        """
        Extract surah number from query.

        Order of precedence:
          1. Arabic surah name  (البقرة → 2)
          2. English surah name (al-baqarah → 2)
          3. Explicit digit ONLY after 'surah'/'سورة' keyword
             (prevents page/juz numbers being mistaken for surah numbers)
        """
        # 1. Arabic name lookup
        for name, num in _SURAH_NAMES_AR.items():
            if name in query:
                return num

        # 2. English name lookup
        ql = query.lower()
        for name, num in _SURAH_NAMES_EN.items():
            if name in ql:
                return num

        # 3. Digit — only accept digits that directly follow سورة/surah keyword
        #    Pattern: "سورة 18" or "surah 18" or "سورة رقم 18"
        explicit = re.search(
            r"(?:سور[ةه]|surah?)\s+(?:رقم\s*)?(\d{1,3})\b",
            query,
            re.IGNORECASE,
        )
        if explicit:
            n = int(explicit.group(1))
            if 1 <= n <= 114:
                return n

        return None

    # ── Validation ────────────────────────────────────────────────────────────

    def _validate_sql(self, sql: str) -> None:
        """
        Ensure SQL is a SELECT-only statement with no injection vectors.

        Blocks: DDL, DML, UNION, EXEC, comments (--, /* */), multi-statement (;).
        """
        stripped = sql.strip()

        if not stripped.upper().startswith("SELECT"):
            raise NL2SQLQueryError("Only SELECT queries are allowed.")

        if _FORBIDDEN_SQL.search(stripped):
            raise NL2SQLQueryError(
                "Query contains a forbidden keyword or character."
            )

    # ── Formatting ────────────────────────────────────────────────────────────

    def _format_result(self, query: str, rows: list[dict]) -> str:
        """Render SQL result rows as a human-readable string."""
        if not rows:
            return "No results found."

        row = rows[0]
        ql  = query.lower()

        if any(kw in ql for kw in ["أطول", "longest"]):
            return (
                f"The longest surah is {row.get('name_en', '?')} "
                f"with {row.get('verse_count', '?')} verses."
            )

        if any(kw in ql for kw in ["أقصر", "shortest"]):
            return (
                f"The shortest surah is {row.get('name_en', '?')} "
                f"with {row.get('verse_count', '?')} verses."
            )

        # Single scalar value
        if len(row) == 1:
            value = next(iter(row.values()))
            return str(value)

        # Multi-column: list all rows
        if len(rows) == 1:
            return ", ".join(f"{k}: {v}" for k, v in row.items())

        return "\n".join(
            " | ".join(str(v) for v in r.values()) for r in rows
        )