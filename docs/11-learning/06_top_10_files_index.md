# 📚 فهرس شرح أهم 10 ملفات في Athar

## 🕌 نظرة عامة

هذا الفهرس يربط **كل ملفات الشرح التفصيلي** لأهم 10 ملفات في مشروع Athar.

---

## 📋 الملفات المتاحة

| الرقم | الملف | الحجم | الحالة |
|-------|-------|-------|--------|
| **1** | [`settings.py`](#الملف-1-settingspy-140-سطر) | 140 سطر | ✅ مكتمل |
| **2** | [`intents.py`](#الملف-2-intentspy-180-سطر) | 180 سطر | ✅ مكتمل |
| **3** | [`router.py`](#الملف-3-routerpy-250-سطر) | 250 سطر | ✅ مكتمل |
| **4** | [`registry.py`](#الملف-4-registerypy-190-سطر) | 190 سطر | 📝 قريباً |
| **5** | [`citation.py`](#الملف-5-citationpy-350-سطر) | 350 سطر | 📝 قريباً |
| **6** | [`base.py (agents)`](#الملف-6-basepy-agents-90-سطر) | 90 سطر | 📝 قريباً |
| **7** | [`chatbot_agent.py`](#الملف-7-chatbot_agentpy-160-سطر) | 160 سطر | 📝 قريباً |
| **8** | [`fiqh_agent.py`](#الملف-8-fiqh_agentpy-280-سطر) | 280 سطر | 📝 قريباً |
| **9** | [`base.py (tools)`](#الملف-9-basepy-tools-70-سطر) | 70 سطر | 📝 قريباً |
| **10** | [`zakat_calculator.py`](#الملف-10-zakat_calculatorpy-350-سطر) | 350 سطر | 📝 قريباً |

---

## 🔗 روابط الملفات التفصيلية

### الملف 1: `settings.py` (140 سطر)

**الملف:** [`04_top_10_files_deep_explanation.md`](04_top_10_files_deep_explanation.md#الملف-1-srcconfigsettingspy-140-سطر)

**المحتوى:**
- كل إعدادات التطبيق في مكان واحد
- Pydantic BaseSettings
- 37 متغير بيئة
- Validators للتحقق من الإعدادات

**أهم النقاط:**
1. يقرأ من `.env` تلقائياً
2. يدعم PostgreSQL, Redis, Qdrant
3. يدعم Groq و OpenAI
4. Singleton instance

---

### الملف 2: `intents.py` (180 سطر)

**الملف:** [`04_top_10_files_deep_explanation.md`](04_top_10_files_deep_explanation.md#الملف-2-srcconfigintentspy-180-سطر)

**المحتوى:**
- 16 نوع نية (Intent)
- 4 نيات فرعية للقرآن
- توصيف كل نية للـ LLM
- توجيه كل نية لوكيل
- كلمات مفتاحية لكل نية

**أهم النقاط:**
1. Intent Enum يحدد القيم المسموحة
2. INTENT_ROUTING يربط النية بالوكيل
3. KEYWORD_PATTERNS للتصنيف السريع
4. بعض الوكلاء محذوفون (fallback إلى general)

---

### الملف 3: `router.py` (250 سطر)

**الملف:** [`05_router_deep_dive.md`](05_router_deep_dive.md)

**المحتوى:**
- HybridQueryClassifier (3-tier)
- RouterResult (نموذج النتيجة)
- LLM classification prompt
- Keyword matching
- Language detection

**أهم النقاط:**
1. **Tier 1**: Keyword (0.92 confidence, سريع)
2. **Tier 2**: LLM (0.75 threshold, دقيق)
3. **Tier 3**: Embedding (fallback)
4. يكشف اللغة (Arabic/English)

---

### الملف 4: `registry.py` (190 سطر)

📝 **قريباً** - سيتم إضافة الشرح التفصيلي

**ما يغطيه:**
- AgentRegistration dataclass
- AgentRegistry class
- register_agent(), register_tool()
- get_for_intent()
- initialize_registry()

---

### الملف 5: `citation.py` (350 سطر)

📝 **قريباً** - سيتم إضافة الشرح التفصيلي

**ما يغطيه:**
- CitationNormalizer class
- 6 regex patterns للاقتباسات
- Quran, Hadith, Fatwa citations
- External URLs (quran.com, sunnah.com)
- Era classification (prophetic → modern)

---

### الملف 6: `base.py (agents)` (90 سطر)

📝 **قريباً** - سيتم إضافة الشرح التفصيلي

**ما يغطيه:**
- Citation model
- AgentInput model
- AgentOutput model
- BaseAgent abstract class
- __call__() magic method

---

### الملف 7: `chatbot_agent.py` (160 سطر)

📝 **قريباً** - سيتم إضافة الشرح التفصيلي

**ما يغطيه:**
- Greeting templates (AR/EN)
- Ramadan/Eid greetings
- Small talk templates
- _is_greeting(), _is_small_talk()
- Language detection

---

### الملف 8: `fiqh_agent.py` (280 سطر)

📝 **قريباً** - سيتم إضافة الشرح التفصيلي

**ما يغطيه:**
- Fiqh RAG Agent (كامل)
- Lazy initialization
- Retrieve → Generate → Cite
- Hybrid search integration
- Citation normalization
- Fallback mechanisms

---

### الملف 9: `base.py (tools)` (70 سطر)

📝 **قريباً** - سيتم إضافة الشرح التفصيلي

**ما يغطيه:**
- ToolInput model
- ToolOutput model
- BaseTool abstract class
- الفرق بين Agent و Tool

---

### الملف 10: `zakat_calculator.py` (350 سطر)

📝 **قريباً** - سيتم إضافة الشرح التفصيلي

**ما يغطيه:**
- ZakatType enum (7 أنواع)
- Madhhab enum (4 مذاهب)
- ZakatAssets dataclass
- ZakatResult dataclass
- calculate() method
- Livestock zakat (hadith rates)
- Crops zakat (5%/10%)

---

## 📊 ملخص سريع

### الإعدادات (ملفان)

| الملف | السطور | الوظيفة |
|-------|--------|---------|
| `settings.py` | 140 | كل إعدادات التطبيق |
| `intents.py` | 180 | 16 نوع نية + كلمات مفتاحية |

### التصنيف والتوجيه (ملفان)

| الملف | السطور | الوظيفة |
|-------|--------|---------|
| `router.py` | 250 | تصنيف النية (3-tier) |
| `registry.py` | 190 | تسجيل الوكلاء والأدوات |

### الاقتباسات (ملف واحد)

| الملف | السطور | الوظيفة |
|-------|--------|---------|
| `citation.py` | 350 | تطبيع الاقتباسات |

### الوكلاء (3 ملفات)

| الملف | السطور | الوظيفة |
|-------|--------|---------|
| `base.py` | 90 | الفئات الأساسية |
| `chatbot_agent.py` | 160 | وكيل الترحيب |
| `fiqh_agent.py` | 280 | وكيل الفقه (RAG) |

### الأدوات (ملفان)

| الملف | السطور | الوظيفة |
|-------|--------|---------|
| `base.py` | 70 | فئة الأدوات |
| `zakat_calculator.py` | 350 | حاسبة الزكاة |

---

## 🎯 كيف تستخدم هذا الفهرس

### للمبتدئين

```
1. اقرأ: settings.py         ← فهم الإعدادات
2. اقرأ: intents.py          ← فهم النيات
3. اقرأ: router.py           ← فهم التصنيف
4. جرب: شغل التطبيق
```

### للمتوسطين

```
1. اقرأ: registry.py         ← فهم التسجيل
2. اقرأ: citation.py         ← فهم الاقتباسات
3. اقرأ: base.py (agents)    ← فهم الفئات
4. اقرأ: chatbot_agent.py    ← أبسط وكيل
```

### للمتقدمين

```
1. اقرأ: fiqh_agent.py       ← وكيل RAG كامل
2. اقرأ: base.py (tools)     ← فئة الأدوات
3. اقرأ: zakat_calculator.py ← أداة حتمية
4. جرب: أضف نية جديدة
```

---

## 📝 تمارين عامة

### تمرين 1: تتبع إعداد

افتح `settings.py` وأجب:
1. كم متغير بيئة موجود؟
2. ما الفرق بين `llm_provider` و `llm_model`؟
3. لماذا `qdrant_api_key` Optional؟

### تمرين 2: تتبع نية

افتح `intents.py` وأجب:
1. ما الـ 16 نية؟
2. ما الوكيل المسؤول عن `hadith`؟
3. ما الكلمات المفتاحية لـ `zakat`؟

### تمرين 3: تتبع تصنيف

افتح `router.py` وأجب:
1. ما الـ 3 tiers؟
2. لماذا keyword confidence=0.92؟
3. ماذا يحدث إذا فشل الـ 3 tiers؟

### تمرين 4: رسم تدفق

ارسم diagram يوضح:
```
سؤال → settings → intents → router → registry → agent → إجابة
```

---

## 🔗 روابط ذات صلة

- [`01_project_overview.md`](01_project_overview.md) - نظرة عامة
- [`02_folder_structure.md`](02_folder_structure.md) - شرح المجلدات
- [`03_api_main_entrypoint.md`](03_api_main_entrypoint.md) - نقطة الدخول
- [`learning_path.md`](learning_path.md) - خطة التعلم
- [`quick_reference.md`](quick_reference.md) - ملخص سريع

---

## 📈 خطة إكمال الملفات

| الأسبوع | الملفات | الحالة |
|---------|---------|--------|
| **الأسبوع 1** | settings.py, intents.py, router.py | ✅ مكتمل |
| **الأسبوع 2** | registry.py, citation.py, base.py (agents) | 📝 قريباً |
| **الأسبوع 3** | chatbot_agent.py, fiqh_agent.py | 📝 قريباً |
| **الأسبوع 4** | base.py (tools), zakat_calculator.py | 📝 قريباً |

---

## 💡 نصائح للقراءة

### اقرأ بالترتيب
لا تقفز بين الملفات. كل ملف يبني على سابقه.

### طبق التمارين
في نهاية كل ملف يوجد تمرين صغير. حله قبل المتابعة.

### اقرأ الكود
بعد قراءة الشرح، افتح الملف واقرأه بنفسك.

### جرب التغييرات
بعد فهم ملف، جرب تغيير بسيط وشاهد ماذا يحدث.

---

**🚀 ابدأ الآن:** [`04_top_10_files_deep_explanation.md`](04_top_10_files_deep_explanation.md)

**📖 التالي:** [`05_router_deep_dive.md`](05_router_deep_dive.md)

---

## 🏗️ الإصدار v2 - المعمارية الجديدة

### ما الجديد في v2؟
مع الإصدار v2، появиت مسارات جديدة مهمة:

```
src/
├── agents/collection/    ← 10 وكلاء CollectionAgent جدد
├── config/agents/        ← 10 ملفات YAML للتكوين
├── prompts/              ← ملفات Prompts منفصلة
├── retrieval/            ← طبقة الاسترجاع الجديدة
├── verification/         ← طبقة التحقق الجديدة
├── application/routing/  ← نظام التوجيه الجديد
├── infrastructure/qdrant/ ← عميل Qdrant
└── generation/           ← طبقة التوليد الجديدة
```

### الملفات الجديدة في v2

| الملف | الوظيفة |
|-------|---------|
| `src/agents/collection/base.py` | CollectionAgent الأساسي |
| `src/application/routing/intent_router.py` | router الجديد |
| `src/retrieval/strategies.py` | استراتيجيات الاسترجاع |
| `src/verification/` | طبقة التحقق |

### لماذا v2؟
1. **فصل الاهتمامات**: كل طبقة مسئولة عن شيء واحد
2. **النظام التصريحي**: التكوين في ملفات YAML
3. **الصيانة**: تغيير الـ prompts بدون كود

### للمزيد من التفاصيل
- [`V2_MIGRATION_NOTES.md`](../../8-development/refactoring/V2_MIGRATION_NOTES.md)
- [`02_folder_structure.md`](02_folder_structure.md)

---

**مُعد الفهرس:** AI Mentor System  
**التاريخ:** أبريل 2026  
**الإصدار:** 1.0
