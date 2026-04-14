# 📂 الملف 5: `src/core/citation.py` - مطبع الاقتباسات (350 سطر)

## 1️⃣ وظيفة الملف

هذا الملف يحتوي على **CitationNormalizer** - النظام الذي **يحول** أي ذكر لمصدر في النص إلى **اقتباس موحد** مثل `[C1]`, `[C2]`, `[C3]`.

بدونه، الإجابات ستكون بدون مصادر واضحة.

---

## 2️⃣ نظرة عامة

| القسم | الأسطر | المحتوى |
|-------|--------|---------|
| Imports | 1-15 | مكتبات أساسية |
| PATTERNS | 16-80 | 6 regex patterns |
| URLs | 81-100 | روابط خارجية |
| normalize() | 101-150 | الدالة الرئيسية |
| Build citations | 151-250 | بناء الاقتباسات |
| enrich_citations() | 251-330 | إضافة metadata |
| _classify_era() | 331-350 | تصنيف العصور |

---

## 3️⃣ شرح سطر بسطر

### الأسطر 1-15: Imports

```python
import re
from typing import Optional, Dict, Any

from src.agents.base import Citation
from src.config.logging_config import get_logger

logger = get_logger()
```

**شرح**:
- `re`: للتعامل مع Regular Expressions (البحث عن أنماط)
- `Citation`: نموذج الاقتباسات
- `logger`: لتسجيل الأحداث

---

### الأسطر 16-80: PATTERNS (6 أنماط regex)

```python
    PATTERNS = [
        # Quran: "Quran 2:255" or "القرآن 2:255" or "البقرة 255"
        (
            r'(?:quran|القرآن|سورة)\s*(\d+)\s*[:\-]\s*(\d+)',
            "quran",
            "quran_reference"
        ),

        # Quran by surah name: "سورة البقرة آية 255"
        (
            r'(?:سورة)\s+([\u0600-\u06FF\s]+?)\s*(?:آية|اية)\s*(\d+)',
            "quran",
            "quran_surah_ayah"
        ),

        # Hadith: "صحيح البخاري، حديث 1234" or "Sahih Bukhari 1234"
        (
            r'(?:صحيح|سنن|مسند)\s+(البخاري|مسلم|الترمذي|أبو داود|النسائي|ابن ماجه)'
            r'\s*(?:،|,)?\s*(?:حديث|رقم|hadith|no\.?)\s*(\d+)',
            "hadith",
            "hadith_reference"
        ),

        # Simplified hadith: "رواه البخاري"
        (
            r'(?:رواه|mentioned in)\s+(صحيح\s+)?(البخاري|مسلم|الترمذي|أبو داود|النسائي|ابن ماجه)',
            "hadith",
            "hadith_book"
        ),

        # Fatwa: "فتوى رقم 12345" or "IslamWeb Fatwa #12345"
        (
            r'(?:فتوى|fatwa)\s*(?:رقم|#)?\s*((\d+)',
            "fatwa",
            "fatwa_reference"
        ),

        # Generic book: "كتاب كذا، باب كذا، رقم 123"
        (
            r'([\u0600-\u06FFa-zA-Z\s]+?)\s*(?:،|,)\s*(?:باب|chapter)\s+([\u0600-\u06FFa-zA-Z\s]+?)'
            r'\s*(?:،|,)?\s*(?:رقم|no\.?|hadith)\s*(\d+)',
            "fiqh_book",
            "fiqh_reference"
        ),
    ]
```

**شرح كل pattern**:

#### Pattern 1: Quran reference
```python
r'(?:quran|القرآن|سورة)\s*(\d+)\s*[:\-]\s*(\d+)'
```

**ما يتطابق**:
- "Quran 2:255" → group(1)="2", group(2)="255"
- "القرآن 2:255" → group(1)="2", group(2)="255"
- "سورة 2-255" → group(1)="2", group(2)="255"

**الرموز**:
- `(?:...)` : non-capturing group (لا يحفظ)
- `\s*` : صفر أو أكثر من مسافة
- `(\d+)` : رقم واحد أو أكثر (يحفط)
- `[:\-]` : نقطتين أو شرطة

---

#### Pattern 2: Quran by surah name
```python
r'(?:سورة)\s+([\u0600-\u06FF\s]+?)\s*(?:آية|اية)\s*(\d+)'
```

**ما يتطابق**:
- "سورة البقرة آية 255" → group(1)="البقرة", group(2)="255"
- "سورة يس اية 10" → group(1)="يس", group(2)="10"

**الرموز**:
- `[\u0600-\u06FF\s]` : حروف عربية + مسافات
- `+?` : واحد أو أكثر (غير greedy)

---

#### Pattern 3: Hadith reference
```python
r'(?:صحيح|سنن|مسند)\s+(البخاري|مسلم|الترمذي|أبو داود|النسائي|ابن ماجه)'
r'\s*(?:،|,)?\s*(?:حديث|رقم|hadith|no\.?)\s*(\d+)'
```

**ما يتطابق**:
- "صحيح البخاري، حديث 1234" → group(1)="البخاري", group(2)="1234"
- "سنن الترمذي hadith 567" → group(1)="الترمذي", group(2)="567"
- "مسند أحمد رقم 890" → لا يتطابق (أحمد ليس في القائمة!)

**القائمة البيضاء**:
- البخاري
- مسلم
- الترمذي
- أبو داود
- النسائي
- ابن ماجه

(هذه الـ 6 تسمى "الكتب الستة" في الحديث)

---

#### Pattern 4: Simplified hadith
```python
r'(?:رواه|mentioned in)\s+(صحيح\s+)?(البخاري|مسلم|الترمذي|أبو داود|النسائي|ابن ماجه)'
```

**ما يتطابق**:
- "رواه البخاري" → group(1)=None, group(2)="البخاري"
- "رواه صحيح مسلم" → group(1)="صحيح", group(2)="مسلم"
- "mentioned in Bukhari" → لا يتطابق (يحتاج عربي!)

---

#### Pattern 5: Fatwa reference
```python
r'(?:فتوى|fatwa)\s*(?:رقم|#)?\s*(\d+)'
```

**ما يتطابق**:
- "فتوى رقم 12345" → group(1)="12345"
- "فتوى #67890" → group(1)="67890"
- "fatwa 11111" → group(1)="11111"

---

#### Pattern 6: Generic fiqh book
```python
r'([\u0600-\u06FFa-zA-Z\s]+?)\s*(?:،|,)\s*(?:باب|chapter)\s+([\u0600-\u06FFa-zA-Z\s]+?)'
r'\s*(?:،|,)?\s*(?:رقم|no\.?|hadith)\s*(\d+)'
```

**ما يتطابق**:
- "موطأ مالك، باب الصلاة، رقم 123" → group(1)="موطأ مالك", group(2)="الصلاة", group(3)="123"
- "صحيح البخاري، chapter Faith، no. 456" → group(1)="صحيح البخاري", group(2)="Faith", group(3)="456"

---

### الأسطر 81-100: External URLs

```python
    QURAN_URL_TEMPLATE = "https://quran.com/{surah}/{ayah}"
    HADITH_URLS = {
        "البخاري": "https://sunnah.com/bukhari",
        "bukhari": "https://sunnah.com/bukhari",
        "مسلم": "https://sunnah.com/muslim",
        "muslim": "https://sunnah.com/muslim",
        "الترمذي": "https://sunnah.com/tirmidhi",
        "tirmidhi": "https://sunnah.com/tirmidhi",
        "أبو داود": "https://sunnah.com/abudawud",
        "abudawud": "https://sunnah.com/abudawud",
        "النسائي": "https://sunnah.com/nasai",
        "nasai": "https://sunnah.com/nasai",
        "ابن ماجه": "https://sunnah.com/ibnmajah",
        "ibnmajah": "https://sunnah.com/ibnmajah",
    }
    FATWA_URL_TEMPLATE = "https://www.islamweb.net/en/fatwa/{id}"
```

**شرح**:

| القالب | الاستخدام | مثال |
|--------|-----------|------|
| `QURAN_URL_TEMPLATE` | آيات القرآن | quran.com/2/255 |
| `HADITH_URLS` | كتب الحديث | sunnah.com/bukhari/1234 |
| `FATWA_URL_TEMPLATE` | فتاوى IslamWeb | islamweb.net/en/fatwa/12345 |

**لماذا مهم**:
- يربط كل اقتباس بمصدره الأصلي
- المستخدم يمكنه التحقق بنفسه

---

### الأسطر 101-150: normalize() - الدالة الرئيسية

```python
    def normalize(self, text: str) -> str:
        """
        Normalize all citations in text to [C1], [C2] format.
        """
        normalized_text = text
        self.citation_counter = 0
        self.citation_map = {}

        for pattern, citation_type, pattern_name in self.PATTERNS:
            matches = list(re.finditer(pattern, normalized_text, re.IGNORECASE))

            # Process matches in reverse to preserve positions
            for match in reversed(matches):
                self.citation_counter += 1
                citation_id = f"C{self.citation_counter}"

                # Build citation object
                citation = self._build_citation(match, citation_type, pattern_name)
                citation.id = citation_id
                self.citation_map[citation_id] = citation

                # Replace in text
                normalized_text = (
                    normalized_text[:match.start()] +
                    f"[{citation_id}]" +
                    normalized_text[match.end():]
                )

        # Reverse the order since we processed in reverse
        self.citation_map = dict(
            sorted(self.citation_map.items(), key=lambda x: int(x[0][1:]))
        )

        if self.citation_counter > 0:
            logger.info(
                "citation.normalized",
                count=self.citation_counter,
                citations=list(self.citation_map.keys())
            )

        return normalized_text
```

**شرح خطوة بخطوة**:

```python
# Input:
text = "قال تعالى في Quran 2:255 ورواه البخاري حديث 1234"

# Step 1: يطبق Pattern 1 (Quran)
# matches = [match("Quran 2:255")]

# Step 2: يعكس (reverse)
# reversed(matches) = [match("Quran 2:255")]

# Step 3: لكل match:
# citation_counter = 1
# citation_id = "C1"
# citation = Citation(type="quran", source="Quran 2:255", ...)
# citation_map["C1"] = citation
# استبدل في النص:
# normalized_text = "قال تعالى في [C1] ورواه البخاري حديث 1234"

# Step 4: يطبق Pattern 3 (Hadith)
# matches = [match("البخاري، حديث 1234")]
# citation_counter = 2
# citation_id = "C2"
# citation = Citation(type="hadith", source="Sahih البخاري", ...)
# normalized_text = "قال تعالى في [C1] ورواه [C2] 1234"

# Output:
# "قال تعالى في [C1] ورواه [C2]"
# citation_map = {"C1": Quran Citation, "C2": Hadith Citation}
```

**لماذا reverse؟**:
- لو استبدل من البداية، المواقع تتغير
- reverse يحافظ على المواقع الصحيحة

---

### الأسطر 151-200: _build_citation()

```python
    def _build_citation(
        self,
        match,
        citation_type: str,
        pattern_name: str
    ) -> Citation:
        """Build structured citation from regex match."""

        if citation_type == "quran":
            return self._build_quran_citation(match, pattern_name)
        elif citation_type == "hadith":
            return self._build_hadith_citation(match, pattern_name)
        elif citation_type == "fatwa":
            return self._build_fatwa_citation(match)
        elif citation_type == "fiqh_book":
            return self._build_fiqh_citation(match)
        else:
            return Citation(
                id="",
                type="unknown",
                source=match.group(0),
                reference=match.group(0)
            )
```

**شرح**:
- يختار الدالة المناسبة حسب النوع
- كل نوع يبني Citation بشكل مختلف

---

### الأسطر 201-230: _build_quran_citation()

```python
    def _build_quran_citation(self, match, pattern_name: str) -> Citation:
        """Build Quran citation from match."""
        if pattern_name == "quran_reference":
            surah = match.group(1)
            ayah = match.group(2)
            return Citation(
                id="",
                type="quran",
                source=f"Quran {surah}:{ayah}",
                reference=f"Surah {surah}, Ayah {ayah}",
                url=self.QURAN_URL_TEMPLATE.format(surah=surah, ayah=ayah)
            )
        else:
            # Surah name + ayah pattern
            surah_name = match.group(1).strip()
            ayah = match.group(2)
            return Citation(
                id="",
                type="quran",
                source=f"Quran: {surah_name}:{ayah}",
                reference=f"Surah {surah_name}, Ayah {ayah}",
                url=None  # Would need surah number lookup
            )
```

**شرح**:

```python
# Input: match("Quran 2:255")
# pattern_name = "quran_reference"

# Output:
Citation(
    id="",
    type="quran",
    source="Quran 2:255",
    reference="Surah 2, Ayah 255",
    url="https://quran.com/2/255"
)

# Input: match("سورة البقرة آية 255")
# pattern_name = "quran_surah_ayah"

# Output:
Citation(
    id="",
    type="quran",
    source="Quran: البقرة:255",
    reference="Surah البقرة, Ayah 255",
    url=None  # يحتاج lookup لرقم السورة
)
```

---

### الأسطر 231-270: _build_hadith_citation()

```python
    def _build_hadith_citation(self, match, pattern_name: str) -> Citation:
        """Build Hadith citation from match."""
        if pattern_name == "hadith_reference":
            book = match.group(1)
            number = match.group(2)
            book_key = book.strip().lower().replace(" ", "")
            url = self.HADITH_URLS.get(book_key, self.HADITH_URLS.get(book, ""))

            return Citation(
                id="",
                type="hadith",
                source=f"Sahih {book}",
                reference=f"Hadith #{number}",
                url=f"{url}/{number}" if url else None
            )
        else:
            # Simplified: "رواه البخاري"
            book = match.group(2) if match.group(2) else match.group(1)
            book_key = book.strip().lower().replace(" ", "")
            url = self.HADITH_URLS.get(book_key, self.HADITH_URLS.get(book, ""))

            return Citation(
                id="",
                type="hadith",
                source=f"Collected by {book}",
                reference=match.group(0),
                url=url
            )
```

**شرح**:

```python
# Input: match("صحيح البخاري، حديث 1234")
# pattern_name = "hadith_reference"

# Output:
Citation(
    id="",
    type="hadith",
    source="Sahih البخاري",
    reference="Hadith #1234",
    url="https://sunnah.com/bukhari/1234"
)
```

---

### الأسطر 271-300: _build_fatwa_citation() و _build_fiqh_citation()

```python
    def _build_fatwa_citation(self, match) -> Citation:
        """Build Fatwa citation from match."""
        fatwa_number = match.group(1)
        return Citation(
            id="",
            type="fatwa",
            source=f"IslamWeb Fatwa",
            reference=f"Fatwa #{fatwa_number}",
            url=self.FATWA_URL_TEMPLATE.format(id=fatwa_number)
        )

    def _build_fiqh_citation(self, match) -> Citation:
        """Build Fiqh book citation from match."""
        book = match.group(1).strip()
        chapter = match.group(2).strip()
        number = match.group(3)

        return Citation(
            id="",
            type="fiqh_book",
            source=book,
            reference=f"Chapter: {chapter}, #{number}"
        )
```

**شرح**:

```python
# Fatwa Input: match("فتوى رقم 12345")
# Output:
Citation(
    id="",
    type="fatwa",
    source="IslamWeb Fatwa",
    reference="Fatwa #12345",
    url="https://www.islamweb.net/en/fatwa/12345"
)

# Fiqh Input: match("موطأ مالك، باب الصلاة، رقم 123")
# Output:
Citation(
    id="",
    type="fiqh_book",
    source="موطأ مالك",
    reference="Chapter: الصلاة, #123"
)
```

---

### الأسطر 301-330: enrich_citations()

```python
    def enrich_citations(self, passages: list[Dict[str, Any]]) -> list[Citation]:
        """
        Enhance citations with rich metadata from retrieved passages.

        Adds:
        - Book title and author name
        - Author death year (Hijri)
        - Page number and chapter/section
        - Collection category
        - Scholarly era classification
        - Source text link
        """
        citations = self.get_citations()
        enriched = []

        for i, citation in enumerate(citations):
            # Get corresponding passage metadata
            passage = passages[i] if i < len(passages) else {}

            # Extract metadata from passage
            book_id = passage.get("book_id")
            book_title = passage.get("title", "")
            author = passage.get("author", "")
            author_death = passage.get("author_death")
            page = passage.get("page")
            chapter = passage.get("chapter", "")
            section = passage.get("section", "")
            collection = passage.get("collection", "")
            doc_id = passage.get("doc_id", "")

            # Build rich metadata
            meta = citation.metadata.copy() if hasattr(citation, 'metadata') and citation.metadata else {}

            if book_id:
                meta["book_id"] = book_id
            if book_title:
                meta["book_title"] = book_title
            if author:
                meta["author"] = author
            if author_death:
                meta["author_death"] = author_death
                meta["scholarly_era"] = self._classify_era(author_death)
            if page:
                meta["page"] = page
            if chapter:
                meta["chapter"] = chapter
            if section:
                meta["section"] = section
            if collection:
                meta["collection"] = collection
            if doc_id:
                meta["doc_id"] = doc_id

            # Build enhanced display text
            if author and book_title:
                meta["display_source"] = f"{author} - {book_title}"
                if page:
                    meta["display_source"] += f", p. {page}"
            elif book_title:
                meta["display_source"] = book_title
                if page:
                    meta["display_source"] += f", p. {page}"

            # Create enriched citation
            enriched_citation = Citation(
                id=citation.id,
                type=citation.type,
                source=meta.get("display_source", citation.source),
                reference=citation.reference,
                url=citation.url,
                metadata=meta,
            )
            enriched.append(enriched_citation)

        return enriched
```

**شرح**:

```python
# Input:
passages = [
    {
        "book_id": "matta_123",
        "title": "موطأ مالك",
        "author": "الإمام مالك",
        "author_death": 179,
        "page": 45,
        "chapter": "الصلاة",
        "collection": "fiqh_passages"
    }
]

# Output:
Citation(
    id="C1",
    type="fiqh_book",
    source="الإمام مالك - موطأ مالك, p. 45",  # محسن!
    reference="Chapter: الصلاة, #123",
    metadata={
        "book_id": "matta_123",
        "book_title": "موطأ مالك",
        "author": "الإمام مالك",
        "author_death": 179,
        "scholarly_era": "classical",  # مصنف!
        "page": 45,
        "chapter": "الصلاة",
        "collection": "fiqh_passages",
        "display_source": "الإمام مالك - موطأ مالك, p. 45"
    }
)
```

---

### الأسطر 331-350: _classify_era()

```python
    @staticmethod
    def _classify_era(death_year_hijri: int) -> str:
        """
        Classify scholar's era based on death year (Hijri).

        Eras:
        - Prophetic: 0-100 AH (Companions)
        - Tabi'un: 100-200 AH (Successors)
        - Classical: 200-500 AH (Golden age)
        - Medieval: 500-900 AH (Post-classical)
        - Ottoman: 900-1300 AH (Ottoman era)
        - Modern: 1300+ AH (Modern era)
        """
        if death_year_hijri <= 100:
            return "prophetic"
        elif death_year_hijri <= 200:
            return "tabiun"
        elif death_year_hijri <= 500:
            return "classical"
        elif death_year_hijri <= 900:
            return "medieval"
        elif death_year_hijri <= 1300:
            return "ottoman"
        else:
            return "modern"
```

**شرح**:

```python
_classify_era(95)   # "prophetic"    → الصحابة
_classify_era(150)  # "tabiun"      → التابعون
_classify_era(179)  # "classical"   → الإمام مالك
_classify_era(600)  # "medieval"    → النووي
_classify_era(1000) # "ottoman"     → ابن حجر
_classify_era(1400) # "modern"      → علماء العصر الحديث
```

**لماذا مهم**:
- يساعد في تصنيف المصادر
- يسهل البحث حسب العصر
- يعطي سياق تاريخي

---

## 5️⃣ الخلاصة العملية

### ما الذي يجب أن تفهمه فعلاً؟

1. **6 regex patterns** لاكتشاف الاقتباسات
2. **normalize()** تحول أي ذكر لمصدر إلى `[C1]`, `[C2]`
3. **enrich_citations()** تضيف metadata من passages
4. **External URLs** تربط بمصادر حقيقية

### 📝 تمرين صغير

1. ما الفرق بين pattern 1 و pattern 2 للقرآن؟
2. لماذا يعالج matches في reverse؟
3. ماذا يحدث إذا لم يتطابق أي pattern؟

### 🔜 الخطوة التالية

اقرأ الملف 6: `src/agents/base.py`

---

**📖 الدليل الكامل:** [`docs/mentoring/`](docs/mentoring/)
