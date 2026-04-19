# Domain Keywords Reference

This document describes the keyword patterns used for rule-based routing in the ConfigRouter.

## Overview

The domain keywords system enables fast, rule-based routing without needing a classifier. It matches keywords in the user's query to determine which agent should handle the request.

## Keyword Categories

### Fiqh (فقه)

**Arabic Keywords:**
```
حكم, يجوز, لا يجوز, حرام, حلال, فتوى, مكروه, واجب
صلاة, صيام, زكاة, حج, طهارة, نجاسة, وضوء, غسل
إمامة, جماعة, مسجد, أذان, الإقامة, الجماعة
```

**English Keywords:**
```
fiqh, halal, haram, fatwa, prayer, fasting, zakat
hajj, purification, ablution, impurity, imam
```

### Hadith (حديث)

**Arabic Keywords:**
```
حديث, الحديث, سند, إسناد, تخريج, صحيح, ضعيف, موضوع
الرسول, النبي, البخاري, مسلم, الترمذي, النسائي
ابن ماجه, أبو داود, سنن, مسند, صحيحان
```

**English Keywords:**
```
hadith, sunnah, narrated, sanad, matn, narrator
bukhari, muslim, grade, narrator chain
```

### Tafsir (تفسير)

**Arabic Keywords:**
```
آية, اية, سورة, سوره, قرآن, تفسير, فسر
الله, تبارك, تعالي, قول, رب, تنزيل
```

**English Keywords:**
```
quran, surah, ayah, verse, tafsir, tafseer
interpretation, revelation
```

### Aqeedah (عقيدة)

**Arabic Keywords:**
```
عقيدة, عقيده, توحيد, إيمان, كفر, شرك, رمي
الله, الرب, الأسماء, الصفات, الأسماء والصفات
قدر, قضاء, رجحان, أهل السنة, السلفي
```

**English Keywords:**
```
aqeedah, tawhid, imaan, kufr, shirk, believe
sunni, salafi, attributes of Allah, destiny
```

### Seerah (سيرة)

**Arabic Keywords:**
```
سيرة, سيره, غزوة, غزوه, هجرة, نبوي
بدر, أحد, الخندق, فتح, مكة, الحديبية
الغزوات, السيرة النبوية, timeline
```

**English Keywords:**
```
seerah, sirah, prophet, biography, battle
hijra, migration, opening of makkah
```

### Usul Fiqh (أصول الفقه)

**Arabic Keywords:**
```
أصول الفقه, اصول الفقه, قياس, استحسان, استصحاب
المصلحة, المرسلة, العرف, الشرع, اجتهاد
تقليد, مذهب, خلاف, أدلة, نص, دليل
```

**English Keywords:**
```
usul, fiqh principles, qiyas, istihsan, istishab
maslaha, istihsan, ijma, qiyas
```

### History (تاريخ)

**Arabic Keywords:**
```
تاريخ, دولة, خلافة, حضارة, أحداث
الخلفاء, الراشدين, الأموي, العباسي, العثماني
معركة, حدث, عصر, فترة, دولة
```

**English Keywords:**
```
history, historical, dynasty, caliphate, empire
caliph, era, period, civilization, battle
```

### Language (لغة)

**Arabic Keywords:**
```
نحو, صرف, بلاغة, إعراب, لغة, عربي
الصفة, المبتدأ, الخبر, الفعل, الاسم
إعراب, بناء, مفعول, فاعل, مصدر
```

**English Keywords:**
```
grammar, syntax, morphology, arabic language
nahw, sarf, balaghah, rhetoric
```

### Tazkiyah (تزكية)

**Arabic Keywords:**
```
تزكية, رقائق, أخلاق, معاملة, قلب, روح
صبر, شكر, توبة, إخلاص, رياء, قسوة
الخوف, الرجاء, المحبة, الزهد, الورع
```

**English Keywords:**
```
tazkiyah, spiritual, character, ethics, morals
patience, gratitude, repentance, sincerity
```

## Usage in ConfigRouter

The `ConfigRouter` uses these keywords to determine routing:

```python
from src.application.router.config_router import get_config_router

router = get_config_router()

# Returns ConfigRoutingDecision with:
# - agent_name: fiqh_agent, hadith_agent, etc.
# - confidence: based on number of matches
# - matched_keywords: list of matched keywords
# - primary_domain: the domain with most matches

result = router.route("ما حكم صلاة الجمعة في العيد؟")
# agent_name: fiqh_agent
# confidence: 0.85 (multiple fiqh keywords matched)
# matched_keywords: ['حكم', 'صلاة', 'جمعة']
# primary_domain: fiqh
```

## Multi-Agent Routing

For complex queries that span multiple domains:

```python
results = router.route_multi("ما حكم الصيام وما صحة هذا الحديث؟")
# Returns list of ConfigRoutingDecision for multiple agents
# Primary agent first, then secondary agents
```

## Confidence Calculation

Confidence is calculated based on the number of matched keywords:

```
confidence = min(0.3 + (num_matches * 0.15), 0.95)
```

- 1 match: 0.45
- 2 matches: 0.60
- 3 matches: 0.75
- 4+ matches: 0.90 (capped)

## Adding New Keywords

To add domain-specific keywords:

1. Edit `src/application/router/config_router.py`
2. Find `DOMAIN_KEYWORDS` dictionary
3. Add new keywords to the appropriate domain

```python
DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "fiqh": [
        # Existing keywords
        "حكم", " يجوز",
        # Add new keyword
        "جمعة",  # Friday prayer
    ],
}
```

## Keyword Priority

Keywords are matched in order of domain definition. The domain with the most keyword matches wins. For equal matches, the first domain in the dictionary takes priority.

## Performance Notes

- Keyword matching is O(n*m) where n=domains, m=keywords per domain
- Average routing time: < 1ms
- Suitable for production use as fast-path before classifier

## See Also

- [CONFIG_BACKED_AGENTS.md](./CONFIG_BACKED_AGENTS.md)
- [ORCHESTRATION_PATTERNS.md](./ORCHESTRATION_PATTERNS.md)