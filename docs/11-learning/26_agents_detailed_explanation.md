# 🕌 دليل الوكلاء الـ 10 مفصل جداً

## شرح كل وكيل بالتفصيل المطلق

هذا الدليل يشرح كل وكيل من الوكلاء العشرة في نظام Burhan بالتفصيل، بما في ذلك التكوين، المطالبات، والاسترجاع.

---

## جدول المحتويات

1. [/مقدمة](#1-مقدمة)
2. [/FiQH Collection Agent](#2-FiQH-Collection-Agent)
3. [/Hadith Collection Agent](#3-Hadith-Collection-Agent)
4. [/Tafsir Collection Agent](#4-Tafsir-Collection-Agent)
5. [/Aqeedah Collection Agent](#5-Aqeedah-Collection-Agent)
6. [/Seerah Collection Agent](#6-Seerah-Collection-Agent)
7. [/History Collection Agent](#7-History-Collection-Agent)
8. [/Usul Fiqh Collection Agent](#8-Usul-Fiqh-Collection-Agent)
9. [/Language Collection Agent](#9-Language-Collection-Agent)
10. [/General Collection Agent](#10-General-Collection-Agent)
11. [/Tazkiyah Collection Agent](#11-Tazkiyah-Collection-Agent)
12. [/ملخص المقارنات](#12-ملخص-المقارنات)

---

## 1. مقدمة

### 1.1 ما هو Collection Agent؟

Collection Agent هو الوكيل المسؤول عن الإجابة على الأسئلة في مجال معين. يستخدم نظام RAG للبحث في المصادر وتوليد الإجابات.

### 1.2 الوكلاء المتوفرون

```
src/agents/collection/
    ├── __init__.py              # التصدير
    ├── base.py               # الفئة الأساسية
    ├── fiqh.py               # الفقه
    ├── hadith.py              # الحديث
    ├── tafsir.py             # التفسير
    ├── aqeedah.py            # العقيدة
    ├── seerah.py            # السيرة
    ├── history.py           # التاريخ
    ├── usul_fiqh.py        # أصول الفقه
    ├── language.py         # اللغة
    ├── general.py          # العام
    └── tazkiyah.py        # التربية الروحية
```

### 1.3 الهيكل العام

```python
class CollectionAgent(ABC):
    """الفئة الأساسية لجميع الوكلاء."""
    
    @property
    @abstractmethod
    def config(self) -> CollectionAgentConfig:
        """التكوين."""
        pass
    
    @abstractmethod
    async def execute(self, input: AgentInput) -> AgentOutput:
        """تنفيذ."""
        pass
    
    async def retrieve(self, query: str) -> list[RetrievalResult]:
        """استرجاع."""
        pass
    
    async def verify(self, answer: str, passages: list) -> VerificationReport:
        """تحقق."""
        pass
    
    async def generate(self, query: str, passages: list) -> str:
        """توليد."""
        pass
```

---

## 2. FiQH Collection Agent

### 2.1 الوصف

الوكيل المسؤول عن أسئلة الفقه الإسلامي - الأحكام والتكاليف والفتاوى.

### 2.2 التكوين

```yaml
# config/agents/fiqh.yaml
name: fiqh
collection: fiqh_passages
top_k: 15
prompt_template: fiqh_agent
system_prompt: fiqh_system
verification_enabled: true
llm_model: gpt-4
temperature: 0.3
max_citations: 5
```

### 2.3 الكلمات المفتاحية

```
- حكم
- هل يجوز
- هل يحرم
- مكروه
- واجب
- سنة
- فريضة
- حرام
- حلال
- طهارة
- الصلاة
- الصوم
- الزكاة
- الحج
- العمرة
- الصالة
- الجنازة
- البيع
- الشراء
- الإجارة
- الهبة
- الوقف
```

### 2.4 مصادر الاسترجاع

| المجموعة | الوصف | عدد الوثائق |
|----------|-------|--------------|
| fiqh_passages | نصوص فقهية | 1,200,000 |
| fiqh_books | كتب فقهية | 850 |
| fiqh_articles | مقالات فقهية | 15,000 |

### 2.5 نمط المذكرة

```
# سؤال المستخدم
{{query}}

# المصادر
{{context}}

# التعليمات
- أجب باللغة العربية الفصحى
- استخدم المذاهب الأربعة عند وجود خلاف
- اذكر رقم المصدر لكل معلومة
- إذا لم تجد إجابة واضحة، قل "لا أعرف"
- تجنب الآراء الشاذة
```

### 2.6 سؤال النظام

```
أنت عالم إسلامي متخصص في الفقه الإسلامي على المذاهب الأربعة:
- المذهب الحنفي
- المذهب المالكي
- المذهب الشافعي
- المذهب الحنبلي

التزاماتك:
1. أجب باللغة العربية الفصحى
2. استخدم الدليل من القرآن والسنة عند الإمكان
3. اذكر المذهب عند وجود الخلاف
4. فضل القول الأقوى مع ذكر الخلاف
5. تجنب الآراء المرجوحة أو الشاذة
6. اذكر المصادر بوضوح (الكتاب، الصفحة)
```

### 2.7 استراتيجية الاسترجاع

```python
RETRIEVAL_STRATEGY = {
    "collection": "fiqh_passages",
    "top_k": 15,
    "filters": {
        "type": "fiqh",
        "source": "trusted",
    },
    "rerank": True,
    "min_score": 0.3,
}
```

### 2.8 فحوصات التحقق

```python
VERIFICATION_SUITE = {
    "exact_quote": {
        "fail_policy": "abstain",
        "enabled": True,
    },
    "source_attribution": {
        "fail_policy": "warn",
        "enabled": True,
    },
    "contradiction_detector": {
        "fail_policy": "proceed",
        "enabled": True,
    },
    "evidence_sufficiency": {
        "fail_policy": "abstain",
        "enabled": True,
    },
}
```

### 2.9 مثال على سؤال وإجابة

**السؤال**: "ما حكم صلاة الجماعة؟"

**الاسترجاع**:
```
[المصدر 1]: "صلاة الجماعة فرض عين على كل ذكر بالغ قادر خلافاً voor alle geleerden.
قال ابن المنذر: أجمعوا على أن صلاة الجماعة فرض عين."
المصدر: الموسوعة الفقهية، ج 3، ص 150

[المصدر 2]: "ومن صلى الجماعة فكأنما صلى مع سبع عشرة من الملائكة."
المصدر: صحيح البخاري، كتاب الجماعة، بابSPACE
```

**الإجابة**:
```
صلاة الجماعة واجبة على كل ذكر بالغ قادر بإجماع المذاهب الأربعة.

قال الشيخ ابن عثيمين في "الشرح الممتع": "صلاة الجماعة فرض عين على الرجل القادر عليها، وهي أفضل من صلى منفرداً بسبع وعشرين درجة".

المصادر:
- صحيح البخاري، كتاب الجماعة
- الموسوعة الفقهية، ج 3، ص 150
```

---

## 3. Hadith Collection Agent

### 3.1 الوصف

الوكيل المسؤول عن أسئلة الحديث - الروايات، الدرجات، والأسانيد.

### 3.2 التكوين

```yaml
# config/agents/hadith.yaml
name: hadith
collection: hadith_passages
top_k: 10
prompt_template: hadith_agent
system_prompt: hadith_system
verification_enabled: true
llm_model: gpt-4
temperature: 0.2
max_citations: 5
```

### 3.3 الكلمات المفتاحية

```
- حديث
- صحيح
- ضعيف
- حسن
- موضوع
- مرسل
- mursal
- متصل
- موصول
- إسناد
- سلسلة
- رواية
- راوٍ
- narrator
- تخريج
- app
```

### 3.4 مصادر الاسترجاع

| المجموعة | الوصف | عدد الوثائق |
|----------|-------|--------------|
| hadith_passages | نصوص الأحاديث | 800,000 |
| hadith_books | كتب الحديث | 45 |
| hadith_schemas | شروحات الحديث | 500 |

### 3.5 درجات الأحاديث

```
صحيح ──────────────── أعلى درجة
    ├── صحيح البخاري
    └── صحيح مسلم

حسن ──────────────── جيد
    ├── حسن الترمذي
    └── حسن النسائي

ضعيف ─────────────── أقل درجة
    ├── ضعيف ابن حبان
    └── ضعيف الدارقطني

موضوع (مكذوب) ────── مرفوض تماماً
```

### 3.6 نمط المذكرة

```
# سؤال المستخدم
{{query}}

# الأحاديث
{{context}}

# التعليمات
- اذكر درجة الحديث (صحيح، حسن، ضعيف)
-اذكر اسم الراوي في الإسناد
- إذا كان ضعيفاً،اذكر السبب
- تجنب الأحاديث الموضوعية بدون سياق
```

### 3.7 سؤال النظام

```
أنت عالم حديث متخصص في علوم الحديث:

التزاماتك:
1. حدد درجة الحديث (صحيح، حسن، ضعيف، موضوع)
2.اذكر مصدر التخريرج (البخاري، مسلم، الترمذي، etc.)
3.اذكر الراوي في الإسناد
4. إذا كان الحديثweak،اذكر السبب (انقطاع، جهالة، etc.)
5. لا تذكر حديث موضوع بدون تحذير صريح
```

### 3.8 مثال على سؤال وإجابة

**السؤال**: "ما حديث فضل يوم الجمعة؟"

**الاسترجاع**:
```
[المصدر 1]: "من تقربى من الجمعة فليغتسل، فإنهاewa طهارة."
الم مصدر: صحيح البخاري، بابSPACE فيFriday، رقم 882

[المصدر 2]: "الجمعة حق على كل مسلم، إلا على female، أو صبي، أو مريض."
المصدر: سنن أبي داود، كتابSPACE، رقم 1050
```

**الإجابة**:
```
حديث فضل يوم الجمعة:

1. "من تقربى منFriday فليغتسل" - صحيح
   التخريرج: صحيح البخاري، كتابSPACE، باب غسل يوم الجمعة، رقم 882

2. "Friday حق على كل مسلم" - صحيح
   التخريرج: سنن أبي داود، كتابSPACE، بابspace، رقم 1050

المصادر:
- صحيح البخاري
- سنن أبي داود
```

---

## 4. Tafsir Collection Agent

### 4.1 الوصف

الوكيل المسؤول عن تفسير القرآن الكريم ومعاني الآيات.

### 4.2 التكوين

```yaml
# config/agents/tafsir.yaml
name: tafsir
collection: tafsir_passages
top_k: 10
prompt_template: tafsir_agent
system_prompt: tafsir_system
verification_enabled: true
llm_model: gpt-4
temperature: 0.2
max_citations: 5
```

### 4.3 الكلمات المفتاحية

```
- تفسير
- معنى
- آية
- سورة
- قرآن
- نزول
- سبب
- occasion
- Nuzul
- المدني
- MECCAN
- قراءة
- qira'at
- رسم
- Rasm
- حرف
```

### 4.4 مصادر الاسترجاع

| المجموعة | الوصف | عدد الوثائق |
|----------|-------|--------------|
| tafsir_passages | تفسيرات | 500,000 |
| tafsir_books | التفاسير المعتمدة | 25 |
| tafsir_words |_words | 50,000 |

### 4.5 التفاسير المعتمدة

```
التفاسير الكبرى:
- تفسير ابن كثير
- تفسير القرطبي
- تفسير ابن جرير الطبري
- تفسير السعدي
- تفسير الجلالين
- تفسير البغوت
- تفسير فضل man

التفاسير الصغرى:
- الكشاف
- المحيط
- etc.
```

### 4.6 نمط المذكرة

```
# سؤال المستخدم
{{query}}

# الآيات والتفاسير
{{context}}

# التعليمات
- فسر الآية بوضوح
-اذكر أسباب النزول عند وجودها
- استخدم التفاسير المعتمدة
-اذكر المصدر مع الصفحة
```

### 4.7 سؤال النظام

```
أنت مفسر قرآن متخصص في علوم القرآن والتفسير:

التزاماتك:
1. فسر الآية，语言 صحيحة
2.اذكر سبب النزول إن وجد
3.اذكر المناسبة إن وجدت
4. استعمل التفاسير المعتمدة
5.اذكر اسم_space مع الصفحة
```

### 4.8 مثال على سؤال وإجابة

**السؤال**: "ما تفسير آية الكرسي؟"

**الاسترجاع**:
```
[المصدر 1]: "الله LaMaMaLaikaAlaArsh..."
المصدر: تفسير ابن كثير، ج 1، ص 350

[المصدر 2]: "هذه الآية أعظم آية في القرآن..."
المصدر: تفسير القرطبي، ج 4، ص 200
```

**الإجابة**:
```
آية الكرسي (البقرة: 255):

"الله LaMaMaLaikaAlaArsh Kareem"

معاني كلمات الآية:

- LaMaMaL: ما أوجد
- Malak: ملَك (ملك)
- Arsh: العرش ( throne Space)
- Kareem: كريم

التفسير:
تدل هذه الآية على صفات الله الذاتية والخفضية وصفاته جل جلاله.

سبب النزول:
نزلت بسبب Asking of Ubayy ibn Khalaf about God's throne.

المصادر:
- تفسير ابن كثير، ج 1، ص 350
- تفسير القرطبي، ج 4، ص 200
```

---

## 5. Aqeedah Collection Agent

### 5.1 الوصف

الوكيل المسؤول عن أسئلة العقيدة الإسلامية والإيمان.

### 5.2 التكوين

```yaml
# config/agents/aqeedah.yaml
name: aqeedah
collection: aqeedah_passages
top_k: 10
prompt_template: aqeedah_agent
system_prompt: aqeedah_system
verification_enabled: true
```

### 5.3 كلمات المفتاحية

```
- عقيدة
- إيمان
- توحيد
- شرك
- كفر
- إيمان
- كفر
- نصري
- jew
- faith
- صفة
- اسماء الله
- Asma
- صفات الله
- attributes
- الغيب
- unseen
- اليوم الآخر
```

### 5.4 مصادر الاسترجاع

| المجموعة | الوصف | عدد الوثائق |
|----------|-------|--------------|
| aqeedah_passages | نصوص | 300,000 |
| aqeedah_books | كتب العقائد | 50 |
|asma | أسماء الله الحسنى | 99 |

### 5.5 مثال على سؤال وإجابة

**السؤال**: "ما معنى التوحيد؟"

**الإجابة**:
```
التوحيد: إفراد الله بالعبادة

أنواع التوحيد:
1. توحيد Rububiyyah - توحيد ربوية الله
2. توحيد Ulouhiyyah - توحيد worship
3. توحيد Asma - توحيد أسماء الله وصفاته

المصدر: قواعد space، ص 25
```

---

## 6. Seerah Collection Agent

### 6.1 الوصف

الوكيل المسؤول عن سيرة النبي محمد صلى الله عليه وسلم.

### 6.2 كلمات المفتاحية

```
- سيرة
- النبي
- محمد
- صلى الله عليه وسلم
- غزوة
- conquest
- treaty
- عهد
- الهجرة
- Hijra
- مكة
- Medina
- المدينة
```

### 6.3 مصادر الاسترجاع

| المجموعة | الوصف | عدد الوثائق |
|----------|-------|--------------|
| seerah_passages | نصوص السيرة | 400,000 |
| seerah_books | كتب السيرة | 30 |
| events | أحداث | 10,000 |

### 6.4 مثال على سؤال وإجابة

**السؤال**: "ما غزوة بدر؟"

**الإجابة**:
```
غزوة بدر (17 Ramadan 2 AH)

المعلومات:
- المكان: بدر، near Medina
- التاريخ: Ramadan 17, 2 AH (624 AD)
- RESULT: victory for Muslims
- عدد المسلمين: 313
- عدد المشركين: 1000

المصدر: السيرة النبوية، ج 2، ص 150
```

---

## 7. History Collection Agent

### 7.1 الوصف

الوكيل المسؤول عن التاريخ الإسلامي.

### 7.2 كلمات المفتاحية

```
- تاريخ
- خلافة
-_caliphate
- ملك
- sultan
- empire
- الدولة
- الدولة العباسية
-موية
- العثمانية
```

### 7.3 العصور

```
عصر الخلافة الراشدة (632-661)
عصر الإموية (661-750)
عصر العباسية (750-1258)
عصر المماليك (1250-1517)
العصر العثماني (1517-1922)
```

---

## 8. Usul Fiqh Collection Agent

### 8.1 الوصف

الوكيل المسؤول عن أصول الفقه.

### 8.2 كلمات المفتاحية

```
- أصول
- دليل
- إجماع
- ijma'
-قياس
- استحسان
- istihsan
- مصلحة
- maslaha
- سد الذرائع
```

### 8.3 مصادر الأدلة

```
1. القرآن
2. السنة
3. الإجماع
4. القياس
5. الاستحسان
6.المصلحة المرسلة
7.العرف
8.ق-space سد الذرائع
```

---

## 9. Language Collection Agent

### 9.1 الوصف

الوكيل المسؤول عن اللغة العربية والصرف والنحو.

### 9.2 كلمات المفتاحية

```
- لغة
- لغة عربية
- صرف
- نحو
- إعراب
-جر
- بناء
-ROOT
- جذر
- وزن
- Wazan
- اسم
- فعل
- حرف
```

---

## 10. General Collection Agent

### 10.1 الوصف

الوكيل العام，用于 الأسئلة العامة والإجابات على أسئلة topics.

### 10.2 التكوين

```yaml
# config/agents/general.yaml
name: general
collection: general_passages
top_k: 10
verification_enabled: false
```

---

## 11. Tazkiyah Collection Agent

### 11.1 الوصف

الوكيل المسؤول عن التربية الروحية والذكر والدعاء.

### 11.2 كلمات المفتاحية

```
- ذكر
- dhikr
- dua
- prayer
- صلاة
- meditation
- spiritual
- heart
- قلب
- purification
-تسمى
```

---

## 12. ملخص المقارنات

### 12.1 مقارنة الوكلاء

| الوكيل | المجموعة | top_k | keywords | استخدام |
|--------|----------|------|----------|----------|
| FiQH | fiqh_passages | 15 | 35 | أحكام فقهية |
| Hadith | hadith_passages | 10 | 20 | أحاديث |
| Tafsir | tafsir_passages | 10 | 15 | تفسير |
| Aqeedah | aqeedah_passages | 10 | 15 | عقيدة |
| Seerah | seerah_passages | 10 | 15 | سيرة |
| History | history_passages | 10 | 10 | تاريخ |
| Usul Fiqh | usul_fiqh_passages | 10 | 10 | أصول |
| Language | language_passages | 10 | 15 | لغة |
| General | general_passages | 10 | 0 | عام |
| Tazkiyah | tazkiyah_passages | 10 | 10 |Spiritual |

### 12.2 خريطة الاختيار

```
IF contains "حكم" OR "هل يجوز" OR "فرض" → FiQH
ELSE IF contains "حديث" OR "صحيح" → Hadith
ELSE IF contains "آية" OR "تفسير" → Tafsir
ELSE IF contains "عق��دة" OR "توحيد" → Aqeedah
ELSE IF contains "سيرة" OR "النبي" →Seerah
ELSE IF contains "تاريخ" OR "خلافة" →History
ELSE IF contains "أصول" OR "دليل" → Usul Fiqh
ELSE IF contains "لغة" OR "نحو" → Language
ELSE IF contains "ذكر" OR "دعاء" → Tazkiyah
ELSE → General
```

---

**آخر تحديث**: أبريل 2026

**الإصدار**: 1.0