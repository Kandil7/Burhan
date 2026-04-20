# 🕌 دليل نظام التحقق المفصل جداً

## شرح كل فحص بالتفصيل المطلق

هذا الدليل يشرح نظام التحقق (Verification System) في Athar بالتفصيل.

---

## جدول المحتويات

1. [/مقدمة](#1-مقدمة)
2. [/Exact Quote Validator](#2-exact-quote-validator)
3. [/Source Attribution](#3-source-attribution)
4. [/Hadith Grade](#4-hadith-grade)
5. [/Contradiction Detector](#5-contradiction-detector)
6. [/Evidence Sufficiency](#6-evidence-sufficiency)
7. [/Suite Builder](#7-suite-builder)
8. [/ملخص](#8-ملخص)

---

## 1. مقدمة

### 1.1 ما هو نظام التحقق؟

نظام التحقق يضمن أن الإجابات مبنية على مصادر صحيحة وموثوقة.

### 1.2 الفحوصات المتاحة

```
src/verifiers/
    ├── base.py
    ├── __init__.py
    ├── exact_quote.py          # التحقق من الاقتباس
    ├── source_attribution.py   # التحقق من المصدر
    ├── hadith_grade.py        # التحقق من درجة الحديث
    ├── contradiction.py       # التحقق من التناقض
    ├── evidence_sufficiency.py # التحقق من كفاية الدليل
    ├── temporal_consistency.py  # التحقق الزمني
    ├── school_consistency.py    # التحقق من اتساق المذهب
    ├── groundedness_judge.py      # الحكم في الت grounding
    ├── quote_span.py            # استخراج الاقتباسات
    ├── policies.py              # السياسات
    ├── pipeline.py            # خط الأنابيب
    ├── suite_builder.py        # بناء المجموعات
    ├── misattribution.py      # التحقق من نسب المصدر
    ├── missing_evidence.py     # التحقق من الشهود المفقودين
    ├── fiqh_checks.py          # فحوصات فقهية
```

---

## 2. Exact Quote Validator

### 2.1 الوصف

يفحص أن الاقتباسات في الإجابة مطابقة للمصادر.

### 2.2 المنطق

```python
# في src/verifiers/exact_quote.py

import re
from typing import Optional

class ExactQuoteValidator:
    """مدقق الاقتباسات."""
    
    async def validate(
        self,
        answer: str,
        passages: list[RetrievalResult],
    ) -> CheckResult:
        """تحقق من الاقتباسات."""
        
        # 1. استخراج الاقتباسات من الإجابة
        quotes = self._extract_quotes(answer)
        
        if not quotes:
            return CheckResult(
                status="passed",
                message="No quotes found in answer"
            )
        
        # 2. التحقق من كل اقتباس
        for quote in quotes:
            # البحث في المصادر
            match = self._find_match(quote, passages)
            
            if not match:
                return CheckResult(
                    status="failed",
                    message=f"Quote not found in sources: {quote[:50]}..."
                )
            
            # التحقق Exact
            if not self._is_exact_match(quote, match.text):
                return CheckResult(
                    status="warning",
                    message="Quote is not exact match"
                )
        
        return CheckResult(status="passed")
    
    def _extract_quotes(self, text: str) -> list[str]:
        """استخراج الاقتباسات."""
        
        # Patterns for quotes
        patterns = [
            # [1] text
            rb"\[(\d+)\]([^\[]+)",
            # "text"
            rb'"([^"]+)"',
            # «text»
            rb'«([^»]+)»',
            # "قال..." without quotes
            rb'قال[^:]+:([^.]+)',
        ]
        
        quotes = []
        for pattern in patterns:
            matches = re.finditer(pattern, text)
            quotes.extend([m.group(1).strip() for m in matches])
        
        return quotes
    
    def _find_match(
        self,
        quote: str,
        passages: list[RetrievalResult],
    ) -> Optional[RetrievalResult]:
        """البحث عن تطابق."""
        
        quote_normalized = self._normalize(quote)
        
        for passage in passages:
            passage_normalized = self._normalize(passage.text)
            
            if quote_normalized in passage_normalized:
                return passage
        
        return None
    
    def _is_exact_match(self, quote: str, text: str) -> bool:
        """التحقق من التطابق Exact."""
        
        return self._normalize(quote) in self._normalize(text)
    
    def _normalize(self, text: str) -> str:
        """تطبيع النص."""
        # إزالة التشكيل
        text = re.sub(r"[\u064B-\u0652]", "", text)
        # إزالة المسافات
        text = re.sub(r"\s+", " ", text)
        # تحويل إلى lowercase
        return text.strip().lower()
```

### 2.3 مثال

**الإجابة**:
```
صلاة الجماعة فرض عين [1]على كل ذكر قادر.
```

**المصدر**:
```
[1] صلاة الجماعة فرض عين على كل ذكر قادر خلافاً للعلماء.
```

**النتيجة**: Warning (الاقتباس غير Exact)

---

## 3. Source Attribution

### 3.1 الوصف

يفحص أن المصادر المذكورة صحيحة وموجودة.

### 3.2 المنطق

```python
# في src/verifiers/source_attribution.py

class SourceAttributionValidator:
    """مدقق نسب المصادر."""
    
    async def validate(
        self,
        answer: str,
        passages: list[RetrievalResult],
    ) -> CheckResult:
        """تحقق من نسب المصادر."""
        
        # 1. استخراج أسماء المصادر
        sources = self._extract_sources(answer)
        
        # 2. التحقق من كل مصدر
        valid_sources = []
        invalid_sources = []
        
        for source in sources:
            if self._validate_source(source, passages):
                valid_sources.append(source)
            else:
                invalid_sources.append(source)
        
        if invalid_sources:
            return CheckResult(
                status="warning",
                message=f"Unverified sources: {invalid_sources}"
            )
        
        return CheckResult(status="passed")
    
    def _extract_sources(self, text: str) -> list[str]:
        """استخراج أسماء المصادر."""
        
        patterns = [
            # صحيح البخاري
            r"(?:صحيح|سنن|مجمع) (\w+)",
            # تفسير ابن كثير
            r"تفسير (\w+)",
            # الموسوعة الفقهية
            r"(\w+) الفقهية",
        ]
        
        sources = []
        for pattern in patterns:
            matches = re.finditer(pattern, text)
            sources.extend([m.group(0).strip() for m in matches])
        
        return list(set(sources))
    
    def _validate_source(
        self,
        source: str,
        passages: list[RetrievalResult],
    ) -> bool:
        """التحقق من المصدر."""
        
        for passage in passages:
            metadata = passage.metadata
            book_title = metadata.get("book_title", "")
            
            if source.lower() in book_title.lower():
                return True
        
        return False
```

---

## 4. Hadith Grade

### 4.1 الوصف

يفحص أن أحاديث mentioned have correct grades.

### 4.2 المنطق

```python
# في src/verifiers/hadith_grade.py

class HadithGradeValidator:
    """مدقق درجات الأحاديث."""
    
    async def validate(
        self,
        answer: str,
        passages: list[RetrievalResult],
    ) -> CheckResult:
        """تحقق من درجات الأحاديث."""
        
        # 1. استخراج الأحاديث
        ahadith = self._extract_ahadith(answer)
        
        if not ahadith:
            return CheckResult(status="passed")
        
        # 2. التحقق من كل حديث
        weak_mentioned = []
        fabricated = []
        
        for hadith in ahadith:
            grade = self._get_grade(hadith, passages)
            
            if grade == "ضعيف":
                weak_mentioned.append(hadith[:50])
            elif grade == "موضوع":
                fabricated.append(hadith[:50])
        
        # 3. تقرير النتيجة
        if fabricated:
            return CheckResult(
                status="failed",
                message=f"Fabricated hadith mentioned: {fabricated}"
            )
        
        if weak_mentioned:
            return CheckResult(
                status="warning",
                message=f"Weak hadith mentioned: {weak_mentioned}"
            )
        
        return CheckResult(status="passed")
    
    def _extract_ahadith(self, text: str) -> list[str]:
        """استخراج الأحاديث."""
        
        patterns = [
            r"(?:قال|أخبر) النبي",
            r"حديث (?:عمر|علي|أبي|ابن) \w+",
            r"heard from",
        ]
        
        ahadith = []
        for pattern in patterns:
            matches = re.finditer(pattern, text)
            ahadith.extend([m.group(0) for m in matches])
        
        return ahadith
    
    def _get_grade(
        self,
        hadith: str,
        passages: list[RetrievalResult],
    ) -> str:
        """الحصول على درجة الحديث."""
        
        for passage in passages:
            if hadith in passage.text:
                return passage.metadata.get("grade", "unknown")
        
        return "unknown"
```

---

## 5. Contradiction Detector

### 5.1 الوصف

يفحص وجود تناقضات في الإجابة.

### 5.2 المنطق

```python
# في src/verifiers/contradiction.py

class ContradictionDetector:
    """كاشف التناقضات."""
    
    async def validate(
        self,
        answer: str,
        passages: list[RetrievalResult],
    ) -> CheckResult:
        """تحقق من التناقضات."""
        
        # 1. استخراج الادعاءات
        claims = self._extract_claims(answer)
        
        # 2. التحقق من التناقضات
        contradictions = []
        
        for i, claim1 in enumerate(claims):
            for claim2 in claims[i+1:]:
                if self._is_contradiction(claim1, claim2):
                    contradictions.append((claim1, claim2))
        
        if contradictions:
            return CheckResult(
                status="warning",
                message=f"Possible contradictions: {contradictions}"
            )
        
        return CheckResult(status="passed")
    
    def _extract_claims(self, text: str) -> list[str]:
        """استخراج الادعاءات."""
        
        # جمل affirmative
        patterns = [
            r"[^\.]+\.(?:قال|ذهب|فرض|واجب|حظر|حرام)",
        ]
        
        claims = []
        for pattern in patterns:
            matches = re.finditer(pattern, text)
            claims.extend([m.group(0).strip() for m in matches])
        
        return claims
    
    def _is_contradiction(self, claim1: str, claim2: str) -> bool:
        """التحقق من التناقض."""
        
        # Keywords المتناقضة
        pairs = [
            (["فرض", "واجب"], ["سنة", "مستحب"]),
            (["حلال", "حرام"], ["مكروه", "حرام"]),
            (["صحيح", "موضوع"], ["ضعيف", "موضوع"]),
        ]
        
        for pair1, pair2 in pairs:
            has_pair1_in_claim1 = any(w in claim1 for w in pair1)
            has_pair2_in_claim2 = any(w in claim2 for w in pair2)
            has_pair2_in_claim1 = any(w in claim1 for w in pair2)
            has_pair1_in_claim2 = any(w in claim2 for w in pair1)
            
            if has_pair1_in_claim1 and has_pair2_in_claim2:
                return True
            if has_pair2_in_claim1 and has_pair1_in_claim2:
                return True
        
        return False
```

---

## 6. Evidence Sufficiency

### 6.1 الوصف

يفحص أن الأدلة sufficient for the answer.

### 6.2 المنطق

```python
# في src/verifiers/evidence_sufficiency.py

class EvidenceSufficiencyValidator:
    """مدقق كفاية الأدلة."""
    
    async def validate(
        self,
        answer: str,
        passages: list[RetrievalResult],
    ) -> CheckResult:
        """تحقق من كفاية الأدلة."""
        
        # 1. تقييم قوة الأدلة
        score = self._evaluate_evidence(passages)
        
        if score < 0.3:
            return CheckResult(
                status="failed",
                confidence=score,
                message="Evidence insufficient"
            )
        
        if score < 0.6:
            return CheckResult(
                status="warning",
                confidence=score,
                message="Evidence moderate"
            )
        
        return CheckResult(
            status="passed",
            confidence=score
        )
    
    def _evaluate_evidence(self, passages: list[RetrievalResult]) -> float:
        """تقييم قوة الأدلة."""
        
        if not passages:
            return 0.0
        
        # Factors
        scores = []
        
        for passage in passages:
            score = 0.0
            
            # 1. Grade
            grade = passage.metadata.get("grade", "")
            if grade in ["sahih", "hasan"]:
                score += 0.4
            elif grade == "weak":
                score += 0.2
            
            # 2. Score
            score += passage.score * 0.3
            
            # 3. Source authority
            book = passage.metadata.get("book_title", "").lower()
            if book in ["صحيح البخاري", "صحيح مسلم"]:
                score += 0.3
            elif "سنن" in book:
                score += 0.2
            
            scores.append(score)
        
        return sum(scores) / len(scores)
```

---

## 7. Suite Builder

### 7.1 الوصف

يبني مجموعات التحقق لكل وكيل.

```python
# في src/verifiers/suite_builder.py

class VerificationSuite(BaseModel):
    """مجموعة التحقق."""
    checks: list[VerificationCheck]


class VerificationCheck(BaseModel):
    """فحص واحد."""
    name: str
    fail_policy: str  # "abstain" | "warn" | "proceed"
    enabled: bool = True


def build_suite(agent_name: str) -> VerificationSuite:
    """بناء مجموعة التحقق."""
    
    suites = {
        "fiqh": VerificationSuite(checks=[
            VerificationCheck(
                name="exact_quote",
                fail_policy="abstain"
            ),
            VerificationCheck(
                name="source_attribution",
                fail_policy="warn"
            ),
            VerificationCheck(
                name="contradiction_detector",
                fail_policy="proceed"
            ),
            VerificationCheck(
                name="evidence_sufficiency",
                fail_policy="abstain"
            ),
        ]),
        
        "hadith": VerificationSuite(checks=[
            VerificationCheck(
                name="exact_quote",
                fail_policy="abstain"
            ),
            VerificationCheck(
                name="hadith_grade",
                fail_policy="abstain"
            ),
            VerificationCheck(
                name="source_attribution",
                fail_policy="warn"
            ),
        ]),
        
        "tafsir": VerificationSuite(checks=[
            VerificationCheck(
                name="exact_quote",
                fail_policy="abstain"
            ),
            VerificationCheck(
                name="source_attribution",
                fail_policy="warn"
            ),
        ]),
    }
    
    return suites.get(agent_name, VerificationSuite(checks=[]))
```

---

## 8. ملخص

### 8.1 جدول الفحوصات

| الفحص | الوصف |_policy |
|------|-------|---------|
| Exact Quote | التحقق من الاقتباس | abstain |
| Source Attribution | التحقق من المصدر | warn |
| Hadith Grade | التحقق من الدرجة | abstain |
| Contradiction | التحقق من التناقض | proceed |
| Evidence Sufficiency | التحقق من كفاية | abstain |

### 8.2 جدول السياسات

| Policy | الإجراء |
|--------|-----------|
| abstain | التوقف وإرجاع "no |
| warn | إكمال مع تحذير |
| proceed | إكمال بدون توقف |

---

**آخر تحديث**: أبريل 2026

**الإصدار**: 1.0