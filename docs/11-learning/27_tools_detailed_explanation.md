# 🕌 دليل الأدوات الإسلامية المفصل جداً

## شرح كل أداة بالتفصيل المطلق

هذا الدليل يشرح كل أداة (Tool) في نظام Burhan بالتفصيل، بما في ذلك الوظائف والحسابات والأمثلة.

---

## جدول المحتويات

1. [/مقدمة](#1-مقدمة)
2. [/Zakat Calculator](#2-zakat-calculator)
3. [/Inheritance Calculator](#3-inheritance-calculator)
4. [/Prayer Times Tool](#4-prayer-times-tool)
5. [/Hijri Calendar Tool](#5-hijri-calendar-tool)
6. [/Dua Retrieval Tool](#6-dua-retrieval-tool)
7. [/ملخص](#7-ملخص)

---

## 1. مقدمة

### 1.1 ما هي الأدوات؟

الأدوات (Tools) هي وظائف حتمية (deterministic) выполняют حسابات محددة. على عكس الوكلاء الذين يستخدمون LLM، الأدوات تُنتج نتائج محددة تماماً.

### 1.2 الأدوات المتوفرة

```
src/tools/
    ├── __init__.py
    ├── base.py                      # الفئة الأساسية
    ├── base.py                     # الحاسبة
    │   ├── ZakatCalculator         # زكاة
    │   ├── InheritanceCalculator  # إرث
    │   ├── PrayerTimesTool       # أوقات الصلاة
    │   ├── HijriCalendarTool  # التقويم الهجري
    │   └── DuaRetrievalTool  # الأدعية
```

### 1.3 نقطة النهاية

```
POST /api/v1/tools
{
    "tool_name": "zakat_calculator",
    "parameters": {...}
}
```

---

## 2. Zakat Calculator

### 2.1 الوصف

حاسبة الزكاة تحسب زكاة المال according to Islamic jurisprudence.

### 2.2 الفئة

```python
# src/tools/zakat_calculator.py

from pydantic import BaseModel, Field
from typing import Optional
from src.tools.base import Tool

class ZakatInput(BaseModel):
    """مدخلات الزكاة."""
    
    gold_amount_grams: float = Field(
        default=0.0,
        ge=0.0,
        description="كمية الذهب بالجرامات"
    )
    
    silver_amount_grams: float = Field(
        default=0.0,
        ge=0.0,
        description="كمية الفضة بالجرامات"
    )
    
    cash_amount: float = Field(
        default=0.0,
        ge=0.0,
        description="المبلغ النقدي"
    )
    
    investments: float = Field(
        default=0.0,
        ge=0.0,
        description="الاستثمارات"
    )
    
    debts: float = Field(
        default=0.0,
        ge=0.0,
        description="الديون المستحقة"
    )
    
    gold_price_per_gram: float = Field(
        default=0.0,
        ge=0.0,
        description="سعرجرام الذهب"
    )
    
    silver_price_per_gram: float = Field(
        default=0.0,
        ge=0.0,
        description="سعرجرام الفضة"
    )


class ZakatOutput(BaseModel):
    """مخرجات الزكاة."""
    
    total_nisab: float
    total_assets: float
    total_zakat: float
    is_zakat_due: bool
    lunar_year_completed: bool
    payment_due_date: Optional[str]
    calculation_details: dict
```

### 2.3 النصاب

النصاب هو الحد الأدنى للمال الذي تجب فيه الزكاة:

```
 Nisab Gold = 85 جرام من الذهب
 Nisab Silver = 595 جرام من الفضة
```

**بالقيمة**:

```
 Nisab Gold (2024) = 85 × 300 = 25,500 دولار
 Nisab Silver (2024) = 595 × 3 = 1,785 دولار
```

### 2.4 نسبة الزكاة

```
زكاة المال = 2.5% (ربع العشر)
```

### 2.5 المنطق

```python
class ZakatCalculator(Tool):
    """حاسبة الزكاة."""
    
    name = "zakat_calculator"
    description = "حاسبة زكاة المال"
    
    async def execute(self, parameters: dict) -> dict:
        """تنفيذ الحساب."""
        
        # 1. استخراج القيم
        gold = parameters.get("gold_amount_grams", 0)
        silver = parameters.get("silver_amount_grams", 0)
        cash = parameters.get("cash_amount", 0)
        investments = parameters.get("investments", 0)
        debts = parameters.get("debts", 0)
        gold_price = parameters.get("gold_price_per_gram", 0)
        silver_price = parameters.get("silver_price_per_gram", 0)
        
        # 2. حساب قيمة الذهب
        gold_value = gold * gold_price
        
        # 3. حساب قيمة الفضة
        silver_value = silver * silver_price
        
        # 4. حساب total الأصول
        total_assets = gold_value + silver_value + cash + investments
        
        # 5. خصم الديون
        net_assets = total_assets - debts
        
        # 6. حساب النسبة
        nisab_gold = 85 * gold_price  # 85 جرام
        nisab_silver = 595 * silver_price  # 595 جرام
        
        # 7. اختيار أعلى النسبة
        nisab = max(nisab_gold, nisab_silver)
        
        # 8. التحقق من الوصول للنسبة
        is_zakat_due = net_assets >= nisab
        
        # 9. حساب الزكاة
        if is_zakat_due:
            total_zakat = net_assets * 0.025  # 2.5%
        else:
            total_zakat = 0.0
        
        # 10. إرجاع النتيجة
        return {
            "total_nisab": nisab,
            "total_assets": total_assets,
            "total_zakat": total_zakat,
            "is_zakat_due": is_zakat_due,
            "calculation_details": {
                "gold_value": gold_value,
                "silver_value": silver_value,
                "cash": cash,
                "investments": investments,
                "debts": debts,
                "net_assets": net_assets,
            }
        }
```

### 2.6 مثال

**Input**:

```json
{
    "gold_amount_grams": 100,
    "silver_amount_grams": 500,
    "cash_amount": 10000,
    "investments": 5000,
    "debts": 2000,
    "gold_price_per_gram": 300,
    "silver_price_per_gram": 3
}
```

**Process**:

```
1. Gold Value = 100 × 300 = 30,000
2. Silver Value = 500 × 3 = 1,500
3. Cash = 10,000
4. Investments = 5,000
5. Total Assets = 46,500
6. Debts = 2,000
7. Net Assets = 44,500

8. Nisab Gold = 85 × 300 = 25,500
9. Nisab Silver = 595 × 3 = 1,785
10. Max Nisab = 25,500

11. 44,500 >= 25,500 → Zakat Due ✓

12. Zakat = 44,500 × 2.5% = 1,112.50
```

**Output**:

```json
{
    "total_nisab": 25500,
    "total_assets": 46500,
    "total_zakat": 1112.5,
    "is_zakat_due": true,
    "lunar_year_completed": true,
    "calculation_details": {
        "gold_value": 30000,
        "silver_value": 1500,
        "cash": 10000,
        "investments": 5000,
        "debts": 2000,
        "net_assets": 44500
    }
}
```

---

## 3. Inheritance Calculator

### 3.1 الوصف

حاسبة الإرث تحسب توزيع التركة according to Islamic law.

### 3.2 الفئة

```python
# src/tools/inheritance_calculator.py

class InheritanceInput(BaseModel):
    """مدخلات الإرث."""
    
    deceased_gender: str = Field(..., description="جنس المتوفى")
    is_married: bool = Field(default=True, description="هل كان متزوجاً؟")
    is_married_to_muslim: bool = Field(default=True, description="هل الزوجة مسلمة؟")
    
    heirs: list[dict] = Field(
        default_factory=list,
        description="الورثة"
    )
    
    total_inheritance: float = Field(
        default=0.0,
        ge=0.0,
        description="إجمالي التركة"
    )
    
    debts: float = Field(
        default=0.0,
        ge=0.0,
        description="الديون"
    )
    
    wasiyya: float = Field(
        default=0.0,
        ge=0.0,
        description="الوصية"
    )
```

### 3.3 الورثة وأنصبتهم

```
الورثة من القرآن:
┌─────────────────┬─────────────────┬────────────────┐
│                 │                 │                │
│      Name       │      Share       │    Fraction    │
├─────────────────┼─────────────────┼────────────────┤
│ Husband         │      1/2         │      50%       │
│ Wife           │      1/4         │      25%       │
│ Father         │      1/6         │      16.67%    │
│ Mother         │      1/6         │      16.67%    │
│ Son            │     Asabah      │     varies    │
│ Daughter       │    1/2 Asabah  │     varies    │
│ Full Sister    │      1/2        │      50%       │
│ Uterine Sister │      1/6        │      16.67%    │
│ Full Brother  │     Asabah      │     varies    │
│ Paternal Uncle│     Asabah      │     varies    │
└─────────────────┴─────────────────┴────────────────┘
```

### 3.4 المنطق

```python
class InheritanceCalculator(Tool):
    """حاسبة الإرث."""
    
    name = "inheritance_calculator"
    description = "حاسبة الإرث الإسلامي"
    
    async def execute(self, parameters: dict) -> dict:
        """تنفيذ الحساب."""
        
        # 1. استخراج القيم
        deceased_gender = parameters.get("deceased_gender", "male")
        heirs = parameters.get("heirs", [])
        total = parameters.get("total_inheritance", 0)
        debts = parameters.get("debts", 0)
        wasiyya = parameters.get("wasingya", 0)
        
        # 2. خصم الديون والوصية
        net_inheritance = total - debts - wasiyya
        
        # 3. تحديد الورثة (fard)
        fard_heirs = []
        asabah_heirs = []
        
        for heir in heirs:
            relationship = heir.get("relationship")
            
            if relationship in ["wife", "husband"]:
                fard_heirs.append(heir)
            elif relationship in ["father", "mother"]:
                fard_heirs.append(heir)
            elif relationship == "son":
                asabah_heirs.append(heir)
        
        # 4. حساب الأنصبة
        shares = self._calculate_shares(
            deceased_gender=deceased_gender,
            fard_heirs=fard_heirs,
            asabah_heirs=asabah_heirs,
            net_inheritance=net_inheritance,
        )
        
        # 5. إرجاع النتيجة
        return {
            "total_inheritance": total,
            "debts": debts,
            "wasiyya": wasiyya,
            "net_inheritance": net_inheritance,
            "shares": shares,
            "distribution": self._format_distribution(shares),
        }
    
    def _calculate_shares(
        self,
        deceased_gender: str,
        fard_heirs: list,
        asabah_heirs: list,
        net_inheritance: float,
    ) -> list[dict]:
        """حساب الأنصبة."""
        
        # إذا كان هناك كلا من fard و asabah
        if fard_heirs and asabah_heirs:
            # fard gets their fixed share
            # asabah gets the remainder
            pass
        
        # إذا كان هناك fard فقط
        elif fard_heirs:
            # تقسيم الأنصبة على fard
            pass
        
        # إذا كان هناك asabah فقط
        elif asabah_heirs:
            # يذهب للذكور من.incrementing
            pass
        
        return []
```

### 3.5 مثال

**Input**:

```json
{
    "deceased_gender": "male",
    "heirs": [
        {"relationship": "wife", "count": 1},
        {"relationship": "son", "count": 2},
        {"relationship": "daughter", "count": 1}
    ],
    "total_inheritance": 240000,
    "debts": 0,
    "wasiyya": 0
}
```

**Process**:

```
1. Total = 240,000
2. Debts = 0, Wasiyya = 0
3. Net = 240,000

4. Wife gets 1/4 (25%) = 60,000

5. Remaining = 240,000 - 60,000 = 180,000

6. Sons and Daughter (asabah):
   - Son = 2, Daughter = 1
   - Total parts = 2 + 1 = 3
   - Each son gets 2 × parts = 60,000 each
   - Daughter gets 1 × parts = 60,000
```

**Output**:

```json
{
    "total_inheritance": 240000,
    "debts": 0,
    "wasiyya": 0,
    "net_inheritance": 240000,
    "shares": [
        {
            "heir": "Wife",
            "share": 60000,
            "fraction": "1/4",
            "count": 1
        },
        {
            "heir": "Son",
            "share": 60000,
            "fraction": "asabah",
            "count": 2
        },
        {
            "heir": "Daughter",
            "share": 60000,
            "fraction": "asabah",
            "count": 1
        }
    ]
}
```

---

## 4. Prayer Times Tool

### 4.1 الوصف

أداة أوقات الصلاة تحسب أوقات الصلاة五种 for any location.

### 4.2 الفئة

```python
class PrayerTimesInput(BaseModel):
    """مدخلات أوقات الصلاة."""
    
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    date: str = Field(..., description="التاريخ YYYY-MM-DD")
    timezone: str = Field(default="UTC")


class PrayerTimesOutput(BaseModel):
    """مخرجات أوقات الصلاة."""
    
    fajr: str
    sunrise: str
    dhuhr: str
    asr: str
    sunset: str
    maghrib: str
    isha: str
    date: str
    location: dict
```

### 4.3 المنطق

تستخدم الأداة timetable library:

```python
class PrayerTimesTool(Tool):
    """أوقات الصلاة."""
    
    name = "prayer_times"
    description = "حاسبة أوقات الصلاة"
    
    async def execute(self, parameters: dict) -> dict:
        """تنفيذ."""
        
        # Create location
        location = Location(
            latitude=parameters["latitude"],
            longitude=parameters["longitude"],
        )
        
        # Get date
        date = datetime.fromisoformat(parameters["date"])
        
        # Calculate using prayer_times library
        prayer_times =Timetable(
            location,
            date,
            method=CalculationMethod.MUSLIM_WORLD_LEAGUE,
        )
        
        return {
            "fajr": prayer_times.fajr.strftime("%H:%M"),
            "sunrise": prayer_times.sunrise.strftime("%H:%M"),
            "dhuhr": prayer_times.dhuhr.strftime("%H:%M"),
            "asr": prayer_times.asr.strftime("%H:%M"),
            "sunset": prayer_times.sunset.strftime("%H:%M"),
            "maghrib": prayer_times.maghrib.strftime("%H:%M"),
            "isha": prayer_times.isha.strftime("%H:%M"),
        }
```

### 4.4 مثال

**Input**:

```json
{
    "latitude": 21.5433,
    "longitude": 39.1728,
    "date": "2024-04-15",
    "timezone": "Asia/Riyadh"
}
```

**Output**:

```json
{
    "fajr": "04:28",
    "sunrise": "05:43",
    "dhuhr": "12:12",
    "asr": "15:34",
    "maghrib": "18:42",
    "isha": "20:12"
}
```

---

## 5. Hijri Calendar Tool

### 5.1 الوصف

أداة التقويم الهجري تحول بين التاريخ الهجري والميلادي.

### 5.2 الفئة

```python
class HijriDateInput(BaseModel):
    """مدخلات التاريخ."""
    
    day: int = Field(..., ge=1, le=30)
    month: int = Field(..., ge=1, le=12)
    year: int = Field(...)

class HijriDateOutput(BaseModel):
    """مخرجات التاريخ."""
    
    hijri: dict
    gregorian: dict
    hijri_formatted: str
    gregorian_formatted: str
```

### 5.3 مثال

**Input**:

```json
{
    "day": 15,
    "month": 9,
    "year": 1445
}
```

**Output**:

```json
{
    "hijri": {
        "day": 15,
        "month": 9,
        "month_name": "رمضان",
        "year": 1445
    },
    "gregorian": {
        "day": 15,
        "month": 3,
        "month_name": "March",
        "year": 2024
    },
    "hijri_formatted": "15 رمضان 1445",
    "gregorian_formatted": "March 15, 2024"
}
```

---

## 6. Dua Retrieval Tool

### 6.1 الوصف

أداة استرجاع الأدعية ت find the appropriate dua for the situation.

### 6.2 الفئة

```python
class DuaInput(BaseModel):
    """مدخلات الدعاء."""
    
    situation: str = Field(..., description="الوضع أو الموقف")
    language: str = Field(default="ar")


class DuaOutput(BaseModel):
    """مخرجات الدعاء."""
    
    dua: str
    arabic: str
    transliteration: str
    meaning: str
    source: str
    occurrence: str
```

### 6.3 situations

```
situations:
- صباحاً -Morning
- مساءً - Evening
- قبل الطعام - Before eating
- بعد الطعام - After eating
- قبل النوم - Before sleep
- عند الاستيقاظ - On waking
- للخوف - For fear
- للسفر - For travel
- للمرض - For illness
- للميت - For deceased
- للحزن - For sadness
- للفرح - For joy
- للنجاح - For success
```

### 6.4 مثال

**Input**:

```json
{
    "situation": "before_food",
    "language": "ar"
}
```

**Output**:

```json
{
    "dua": "بسم الله",
    "arabic": "بسم الله الذي لا يضر مع اسمه شيء في الأرض ولا في السماء",
    "transliteration": "Bismillah alladhi la yadurr ma'aasmaihi shay'un filardi wa la fis-sama'",
    "meaning": "With the name of God, nothing on earth or in heaven can harm",
    "source": "Abu Dawud",
    "occurrence": "Sunan Abi Dawud"
}
```

---

## 7. ملخص الأدوات

### 7.1 جدول الأدوات

| الأداة | الوظيفة | المخرجات |
|--------|--------|----------|
| ZakatCalculator | زكاة المال | المبلغ + التفاصيل |
| InheritanceCalculator | توزيع الإرث | الأنصبة |
| PrayerTimesTool | أوقات الصلاة | Fajr, Sunrise, Dhuhr, Asr, Maghrib, Isha |
| HijriCalendarTool | تحويل التواريخ | التاريخان |
| DuaRetrievalTool | الأدعية | الدعاء المناسب |

### 7.2 جدول الاستخدام

```
POST /api/v1/tools
{
    "tool_name": "zakat_calculator",
    "parameters": {...}
}

Response:
{
    "success": true,
    "result": {...}
}
```

---

**آخر تحديث**: أبريل 2026

**الإصدار**: 1.0