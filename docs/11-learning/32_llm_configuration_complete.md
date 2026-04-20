# 🕌 دليل تكوين LLM مفصل جداً

## شرح تكوين النماذج اللغوية

---

## جدول المحتويات

1. [/مقدمة](#1-مقدمة)
2. [/LLM Providers](#2-llm-providers)
3. [/OpenAI](#3-openai)
4. [/Groq](#4-groq)
5. [/Prompt Templates](#5-prompt-templates)
6. [/ملخص](#6-ملخص)

---

## 1. مقدمة

### 1.1 ما هو LLM?

LLM (Large Language Model) هو النموذج الذي يولد الإجابات.

---

## 2. LLM Providers

### 2.1 المزودون المدعومون

```
OpenAI          ← GPT-4, GPT-3.5
Groq           ← LLama, Mixtral
Anthropic      ← Claude (قريباً)
```

---

## 3. OpenAI

### 3.1 التكوين

```python
# src/generation/llm_client.py

class LLMClient:
    """عميل OpenAI."""
    
    def __init__(self, api_key: str):
        import openai
        openai.api_key = api_key
    
    async def generate(
        self,
        messages: list,
        model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """توليد."""
        response = await openai.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        return response.choices[0].message.content
```

### 3.2 النماذج

| النموذج | الوصف | السياق | التكلفة |
|---------|------|---------|---------|
| gpt-4 | أفضل جودة | 8K | $$$ |
| gpt-4-turbo | سريع | 128K | $$ |
| gpt-3.5-turbo | سريع | 16K | $ |

---

## 4. Groq

### 4.1 التكوين

```python
from groq import AsyncGroq

class GroqClient:
    """عميل Groq."""
    
    def __init__(self, api_key: str):
        self._client = AsyncGroq(api_key=api_key)
    
    async def generate(
        self,
        messages: list,
        model: str = "mixtral-8x7b-32768",
        temperature: float = 0.7,
    ) -> str:
        """توليد."""
        response = await self._client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
        )
        
        return response.choices[0].message.content
```

### 4.2 النماذج

| النموذج | الوصف | السياق |
|---------|------|---------|
| llama-3-70b | Llama 3 | 8K |
| mixtral-8x7b | Mixtral | 32K |

---

## 5. Prompt Templates

### 5.1 Files

```
prompts/
├── fiqh_agent.txt
├── hadith_agent.txt
├── tafsir_agent.txt
├── aqeedah_agent.txt
├── seerah_agent.txt
├── general_agent.txt
└── abstain.txt
```

### 5.2 FiQH Agent Prompt

```
# سؤال المستخدم
{{query}}

# المصادر
{{context}}

# التعليمات
- أجب باللغة العربية
- استخدم المذاهب الأربعة
-اذكر المصادر بوضوح
- إذا لم تجد إجابة، قل "لا أعرف"
```

### 5.3 System Prompt - FiQH

```
أنت عالم إسلامي متخصص في الفقه على المذاهب الأربعة:
- الحنفي
- المالكي
- الشافعي
- الحنبلي

التزاماتك:
1. أجب باللغة العربية
2. استخدم الدليل من القرآن والسنة
3.اذكر المذهب عند الخلاف
4. فضل القول الأقوى
5.تجنب الآراء الشاذة
```

---

## 6. ملخص

### 6.1 Models Used

| Agent | Provider | Model | Temperature |
|-------|----------|------|-----------|
| FiQH | OpenAI | gpt-4 | 0.3 |
| Hadith | OpenAI | gpt-4 | 0.2 |
| Tafsir | OpenAI | gpt-4 | 0.2 |
| General | Groq | mixtral | 0.5 |

### 6.2 Costs

```
gpt-4: $0.03/1K tokens
gpt-3.5: $0.002/1K tokens
Groq: Free
```

---

**آخر تحديث**: أبريل 2026