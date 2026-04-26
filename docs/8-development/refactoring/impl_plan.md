بناءً على ما بنيته فعلاً في Burhan حتى الآن, و ما تعلمناه من Fanar-Sadiq ، هنا الـ **Full Implementation Plan** الكامل والمرتّب: [arxiv](https://arxiv.org/pdf/2603.08501.pdf)

***

## Burhan — Full Implementation Plan

### الحالة الراهنة (ما تم بالفعل)

قبل الخطة، ده ملخص ما موجود فعلاً:

| المكون | الحالة |
|---|---|
| FastAPI Backend + 15 API files | ✅ مكتمل |
| Hybrid Intent Classifier (15 intent) | ✅ مكتمل (يحتاج تحسين) |
| Verse Retrieval Tool (multi-format) | ✅ مكتمل |
| NL2SQL Quran Analytics | ✅ مكتمل |
| Quotation Validation Engine | ✅ مكتمل |
| Hijri Calendar Tool | ✅ مكتمل |
| Tafsir Retrieval (Ibn Kathir, Jalalayn, Qurtubi) | ✅ مكتمل |
| 13 Specialized Agents | ✅ موجودة |
| Qdrant + 10M passages (10 collections) | ✅ موجودة |
| Docker + Poetry + Makefile | ✅ موجودة |
| Fiqh/Seerah/General RAG Agents (BaseRAGAgent) | 🔄 Refactoring (Phases 4-9) |

***

## Phase 1 — Intent Classifier Hardening (أولوية قصوى)

المصنّف الحالي LLM-only عملياً رغم وصفه بـ "Hybrid". الإصلاح المطلوب: [perplexity](https://www.perplexity.ai/search/77d3c6e3-1005-4d5b-ab79-1041d521400e)

**1.1 Keyword Fast-Path (< 5ms)**
```python
KEYWORD_RULES = {
    Intent.QURAN: ["سورة", "آية", "quran", "surah", "ayah", "verse"],
    Intent.HADITH: ["حديث", "رواه", "صحيح", "hadith", "bukhari"],
    Intent.FIQH: ["حكم", "حلال", "حرام", "فقه", "ruling", "fatwa"],
    Intent.ZAKAT: ["زكاة", "نصاب", "zakat", "nisab"],
    Intent.INHERITANCE: ["ميراث", "وراثة", "inheritance", "تركة"],
    Intent.PRAYER_TIMES: ["صلاة", "فجر", "مواقيت", "prayer times"],
    Intent.GREETING: ["السلام", "مرحبا", "hello", "hi"],
}
# إذا confidence الكلمات المفتاحية > 0.8 → تخطّى LLM مباشرة
```

**1.2 LLM Classification (Primary)**
- Temperature = 0 مع structured JSON output [arxiv](https://arxiv.org/pdf/2603.08501.pdf)
- يرجع: `{intent, sub_intent, confidence, language, reasoning}`
- Retry مرة واحدة إذا JSON مشوّه

**1.3 Embedding Fallback**
- يُفعّل إذا confidence < 0.5
- Cosine similarity ضد exemplars لكل intent:
\[\text{confidence} = \frac{\text{sim}_1 - \text{sim}_2}{2} + 0.5\]

**1.4 Quran Sub-Classifier** (4 subtypes): [arxiv](https://arxiv.org/pdf/2603.08501.pdf)
- `specific_verse` → Verse Retrieval Tool
- `full_surah` → NL2SQL
- `statistics` → NL2SQL
- `interpretation` → Tafsir RAG Agent

***

## Phase 2 — Deterministic Tools (الأدوات الحتمية)

الأدوات الموجودة تحتاج **توحيد output format** وإضافة أداة واحدة ناقصة:

**2.1 توحيد StandardToolOutput**
```python
class ToolOutput(BaseModel):
    answer: str
    citations: list[Citation]        # [{ref, url, text_snippet}]
    metadata: dict                   # predicted_intent, tool_name, ...
    confidence: float
    execution_trace: list[str]       # للتدقيق
```
كل tool (Verse, NL2SQL, Calendar, Dua, Prayer) ترجع هذا النموذج بالضبط. [arxiv](https://arxiv.org/pdf/2603.08501.pdf)

**2.2 Dua Lookup Tool (ناقصة)**
- استرجاع من collection مخصصة في Qdrant: `dua_passages`
- مرحلتان: cosine similarity للمناسبة → LLM يختار الأنسب [arxiv](https://arxiv.org/pdf/2603.08501.pdf)
- يرجع النص الحرفي بالعربي + الترجمة + المرجع

**2.3 Prayer Times Tool (تأكد من الـ 4 طرق)**:
- Muslim World League، المصرية (19.5°/17.5°)، أم القرى، ISNA
- إضافة: حساب القبلة بنفس المعادلة الواردة في Fanar-Sadiq [arxiv](https://arxiv.org/pdf/2603.08501.pdf)

***

## Phase 3 — RAG Agents Refinement

المطلوب: كل RAG agent يرث من `BaseRAGAgent` (جاري التنفيذ)  مع إضافة:

**3.1 Fiqh Agent — Citation Tagging الإلزامي**
```python
SYSTEM_PROMPT = """
أنت فقيه إسلامي. لكل حكم تذكره:
1. ضع [CITE:N] بعد كل جملة مستندة لمرجع
2. اذكر الحكم، ثم الشرط، ثم الدليل
3. عند الخلاف: اذكر رأي الجمهور أولاً ثم الأقليات
4. إذا لم تجد دليلاً واضحاً: قل "لا أعلم" ولا تهلوس
Temperature = 0.1, max_tokens = 4500
"""
```

**3.2 Hadith Agent — Verbatim + Isnad**
- استرجاع من `hadith_passages` (2M+ passage)
- التحقق من صحة الإسناد بـ Quotation Validation Engine
- يرجع: متن الحديث حرفياً + الراوي + درجة الصحة

**3.3 Seerah Agent**
- Collection: `seerah_passages` (~100k)
- `MAX_TOKENS = 2048`, Temperature = 0.1
- Metadata: `{event_type, hijri_date, location, persons_mentioned}`

**3.4 General Islamic Agent**
- Fallback لكل ما لا يُصنَّف في الـ intents الأخرى
- يبحث في جميع الـ collections بترتيب الأولوية: quran → hadith → fiqh → seerah → general

***

## Phase 4 — Inheritance & Zakat Calculators

موجودان لكن يحتاجان اكتمالاً:

**4.1 Zakat Calculator**
```
النصاب = min(85g × سعر_الذهب, 595g × سعر_الفضة)
زكاة كل فئة = الأصول - الديون - الحاجات_الأساسية) × 2.5%
```
- استدعاء live gold/silver price API (أو allow manual input)
- فئات: ذهب، فضة، نقود، تجارة، زراعة (5% أو 10%)، ماشية

**4.2 Inheritance Calculator (الأعقد)**
3 مراحل كما في Fanar-Sadiq: [arxiv](https://arxiv.org/pdf/2603.08501.pdf)
1. **الفروض**: نصيب كل وارث المؤهل (½، ⅓، ¼، ⅙، ⅛، ⅔)
2. **التعصيب**: الباقي للعصبة بالترتيب
3. **العول أو الرد**: تعديل عند تجاوز أو نقصان التركة

**المهم**: للمسائل الخلافية → **رأيان متوازيان** (الحنفي + الجمهور) بدون اختيار. [arxiv](https://arxiv.org/pdf/2603.08501.pdf)

***

## Phase 5 — Response Assembler

هذا المكون **غائب** في Burhan الحالي وهو حاسم: [arxiv](https://arxiv.org/pdf/2603.08501.pdf)

```python
class ResponseAssembler:
    def assemble(self, tool_output: ToolOutput) -> FinalResponse:
        return FinalResponse(
            answer=tool_output.answer,
            references=self._build_references(tool_output.citations),
            # مثال:  [arxiv](https://arxiv.org/pdf/2603.08501.pdf) البخاري، كتاب الصلاة، باب... https://...
            language=tool_output.metadata["language"],
            execution_trace=tool_output.execution_trace,
            metadata={
                "intent": ...,
                "sub_intent": ...,
                "tools_invoked": [...],
                "retrieval_sources": [...],
                "confidence": ...,
            }
        )
```

***

## Phase 6 — Binary Islamic Classifier (Orchestrator)

قبل أي شيء، يجب **فلترة الأسئلة غير الإسلامية** كما في Fanar: [arxiv](https://arxiv.org/pdf/2603.08501.pdf)

```python
# Lightweight binary classifier
# Model: linear head على bge-m3 مجمّد
# Train: Islamic vs. Non-Islamic queries
# هدف: Precision/Recall > 90%
# يرفض: "من هو ميسي؟" / "اطبخ لي عجة"
```

يمكن البداية بـ **keyword-based** (بسيط وفعّال) ثم ترقية للـ embedding classifier لاحقاً.

***

## Phase 7 — Evaluation Suite

**7.1 Datasets (جاهزة)**

| Dataset | النوع | الاستخدام |
|---|---|---|
| Burhan-Mini-Dataset-v2 | Q&A pairs | End-to-end accuracy |
| QIAS 2025 | MCQ Inheritance | Inheritance Calculator |
| PalmX 2025 (Islamic subtask) | MCQ | General Knowledge |
| IslamTrust | MCQ | Alignment |

**7.2 Metrics**

- **Denotational Correctness**: للـ NL2SQL (exact match) [arxiv](https://arxiv.org/pdf/2603.08501.pdf)
- **Citation Recall**: % الجمل المستندة لمرجع حقيقي قابل للتحقق
- **Hallucination Rate**: عدد الأحاديث/الآيات المنسوبة خطأً
- **LLM-as-Judge**: لـ open-ended Fiqh/Tafsir بنفس أسلوب Fanar [arxiv](https://arxiv.org/pdf/2603.08501.pdf)

***

## Phase 8 — Configuration Hierarchy

```
config/
├── database.json          # Qdrant URLs, SQLite paths, model names
├── .env                   # API keys, secrets
└── defaults.py            # hardcoded fallbacks

# Parameters:
greeting.temperature = 0.2
greeting.max_tokens = 256
fiqh.temperature = 0.1
fiqh.max_tokens = 4500
nl2sql.temperature = 0.1     # max: 0.5
general.temperature = 0.1
max_sources = 12              # range: 5-50
```

***

## Roadmap الزمني المقترح

```
الأسبوع 1:  Phase 1 — Intent Classifier Hardening
             Phase 5 — Response Assembler (skeleton)
الأسبوع 2:  Phase 2 — Dua Tool + توحيد ToolOutput
             Phase 6 — Binary Islamic Classifier (keyword-based)
الأسبوع 3:  Phase 3 — Fiqh Agent citations + Hadith verbatim
             Phase 4 — Inheritance Calculator (العول + الرد)
الأسبوع 4:  Phase 7 — Evaluation Suite
             Phase 8 — Config Hierarchy + Docker production
```

***

## الأولويات الحرجة (Quick Wins)

هذه الـ 3 تغييرات تحسّن الجودة فوراً:

1. **توحيد ToolOutput** — بدونه كل agent يرجع format مختلف ويصعب الـ assembly
2. **Mandatory `[CITE:N]` في Fiqh Agent** — يمنع الهلوسة على مستوى الجملة [arxiv](https://arxiv.org/pdf/2603.08501.pdf)
3. **Quran Sub-Classifier** → ربط `statistics/full_surah` بـ NL2SQL مباشرة بدل RAG