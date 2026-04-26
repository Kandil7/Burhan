# 📚 دليل أهم 10 ملفات في Burhan - شرح سطر بسطر

## 🕌 مرحباً بك في الدليل الشامل

هذا الدليل يشرح **أهم 10 ملفات** في مشروع Burhan **سطر بسطر** بالتفصيل الكامل.

---

## 📋 الملفات المتاحة

| الدليل | الملف | المحتوى | الحجم |
|--------|-------|---------|-------|
| **الفهرس الرئيسي** | [`06_top_10_files_index.md`](06_top_10_files_index.md) | روابط كل الملفات | متوسط |
| **الملخص الشامل** | [`07_top_10_files_summary.md`](07_top_10_files_summary.md) | ملخص سريع لكل الملفات | قصير |
| **الشرح التفصيلي 1** | [`04_top_10_files_deep_explanation.md`](04_top_10_files_deep_explanation.md) | شرح ملفي settings.py و intents.py | طويل |
| **الشرح التفصيلي 2** | [`05_router_deep_dive.md`](05_router_deep_dive.md) | شرح router.py بالتفصيل | طويل |

---

## 🎯 أهم 10 ملفات بالترتيب

| الأولوية | الملف | السطور | الحالة |
|----------|-------|--------|--------|
| **1** | `src/config/settings.py` | 140 | ✅ مشروح |
| **2** | `src/config/intents.py` | 180 | ✅ مشروح |
| **3** | `src/core/router.py` | 250 | ✅ مشروح |
| **4** | `src/core/registry.py` | 190 | 📝 قريباً |
| **5** | `src/core/citation.py` | 350 | 📝 قريباً |
| **6** | `src/agents/base.py` | 90 | 📝 قريباً |
| **7** | `src/agents/chatbot_agent.py` | 160 | 📝 قريباً |
| **8** | `src/agents/fiqh_agent.py` | 280 | 📝 قريباً |
| **9** | `src/tools/base.py` | 70 | 📝 قريباً |
| **10** | `src/tools/zakat_calculator.py` | 350 | 📝 قريباً |

---

## 📖 كيف تستخدم هذا الدليل

### للمبتدئين (ابدأ من هنا)

```
1. اقرأ: 07_top_10_files_summary.md      ← ملخص سريع
2. اقرأ: 06_top_10_files_index.md        ← فهرس الملفات
3. اقرأ: 04_top_10_files_deep_explanation.md ← شرح تفصيلي (ملف 1-2)
4. اقرأ: 05_router_deep_dive.md          ← شرح تفصيلي (ملف 3)
```

### للمتوسطين

```
1. اقرأ الملفات بالترتيب من 1 إلى 10
2. طبق التمارين في نهاية كل ملف
3. افتح الملفات واقرأها بنفسك
```

### للمتقدمين

```
1. اقرأ الكود أولاً دون الشرح
2. قارن فهمك مع الشرح
3. اقترح تحسينات
```

---

## 📊 ملخص كل ملف

### 1. `settings.py` (140 سطر)

**الوظيفة:** كل إعدادات التطبيق في مكان واحد

**يحتوي على:**
- 37 متغير بيئة
- PostgreSQL, Redis, Qdrant settings
- LLM provider (Groq/OpenAI)
- Embedding model (BAAI/bge-m3)
- Validators للتحقق

**📖 الشرح:** [`04_top_10_files_deep_explanation.md`](04_top_10_files_deep_explanation.md#الملف-1-srcconfigsettingspy-140-سطر)

---

### 2. `intents.py` (180 سطر)

**الوظيفة:** تعريف 16 نوع نية + كلمات مفتاحية

**يحتوي على:**
- Intent Enum (16 نوع)
- QuranSubIntent Enum (4 أنواع فرعية)
- INTENT_ROUTING (توجيه للوكلاء)
- KEYWORD_PATTERNS (للتصنيف السريع)

**📖 الشرح:** [`04_top_10_files_deep_explanation.md`](04_top_10_files_deep_explanation.md#الملف-2-srcconfigintentspy-180-سطر)

---

### 3. `router.py` (250 سطر)

**الوظيفة:** تصنيف نية المستخدم (3-tier)

**يحتوي على:**
- HybridQueryClassifier
- Tier 1: Keyword matching
- Tier 2: LLM classification
- Tier 3: Embedding fallback
- Language detection

**📖 الشرح:** [`05_router_deep_dive.md`](05_router_deep_dive.md)

---

### 4-10. الملفات المتبقية

📝 **قريباً** - سيتم إضافة الشرح التفصيلي

---

## 🎯 تمارين شاملة

### تمرين 1: تتبع سؤال

```
سؤال: "ما حكم صلاة العيد؟"

1. settings.py:      ما الإعدادات المستخدمة؟
2. intents.py:       ما النية؟ ما الكلمات المفتاحية؟
3. router.py:        كيف صُنف؟ ما الـ confidence؟
4. registry.py:      ما الوكيل المسؤول؟
5. fiqh_agent.py:    كيف يبحث ويجيب؟
```

### تمرين 2: إضافة نية جديدة

أضف نية `fatwa` مع:
- keyword patterns
- agent routing
- description

### تمرين 3: تحسين الأداء

اقترح تحسينات على:
- caching
- error handling
- performance

---

## 🔗 روابط ذات صلة

### دليل التوجيه الشامل
- [`INDEX.md`](INDEX.md) - الفهرس الرئيسي
- [`01_project_overview.md`](01_project_overview.md) - نظرة عامة
- [`02_folder_structure.md`](02_folder_structure.md) - شرح المجلدات
- [`03_api_main_entrypoint.md`](03_api_main_entrypoint.md) - نقطة الدخول
- [`learning_path.md`](learning_path.md) - خطة التعلم
- [`quick_reference.md`](quick_reference.md) - ملخص سريع

### ملفات الشرح التفصيلي
- [`04_top_10_files_deep_explanation.md`](04_top_10_files_deep_explanation.md) - شرح ملف 1-2
- [`05_router_deep_dive.md`](05_router_deep_dive.md) - شرح ملف 3
- [`06_top_10_files_index.md`](06_top_10_files_index.md) - فهرس الملفات
- [`07_top_10_files_summary.md`](07_top_10_files_summary.md) - ملخص شامل

---

## 📈 خطة إكمال الملفات

| الأسبوع | الملفات | الحالة |
|---------|---------|--------|
| **الأسبوع 1** | settings.py, intents.py, router.py | ✅ مكتمل |
| **الأسبوع 2** | registry.py, citation.py, base.py (agents) | 📝 قريباً |
| **الأسبوع 3** | chatbot_agent.py, fiqh_agent.py | 📝 قريباً |
| **الأسبوع 4** | base.py (tools), zakat_calculator.py | 📝 قريباً |

---

## 💡 نصائح سريعة

### اقرأ بالترتيب
لا تقفز بين الملفات. كل ملف يبني على سابقه.

### طبق التمارين
في نهاية كل ملف يوجد تمرين صغير. حله قبل المتابعة.

### اقرأ الكود
بعد قراءة الشرح، افتح الملف واقرأه بنفسك.

### جرب التغييرات
بعد فهم ملف، جرب تغيير بسيط وشاهد ماذا يحدث.

### اسأل الأسئلة
إذا لم تفهم شيئاً، اطلب شرحاً إضافياً.

---

## 📊 إحصائيات الدليل

| المقياس | القيمة |
|---------|--------|
| **الملفات المشروحة** | 3 من 10 |
| **الأسطر المشروحة** | 570 من 2,060 |
| **نسبة الإكمال** | 27.7% |
| **التمارين** | 9 تمارين |
| **الأمثلة** | 50+ مثال |

---

**🚀 ابدأ الآن:** اقرأ [`07_top_10_files_summary.md`](07_top_10_files_summary.md) للملخص السريع

**📖 ثم:** اقرأ [`04_top_10_files_deep_explanation.md`](04_top_10_files_deep_explanation.md) للتفصيل

**🔗 الفهرس:** [`06_top_10_files_index.md`](06_top_10_files_index.md)

---

**مُعد الدليل:** AI Mentor System  
**التاريخ:** أبريل 2026  
**الإصدار:** 1.0
