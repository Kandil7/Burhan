# 🕌 دليل التكوين الكامل

## شرح كل ملفات التكوين

---

## جدول المحتويات

1. [/ملفات التكوين](#1-ملفات-التكوين)
2. [/Agent Configs](#2-agent-configs)
3. [/Prompts](#3-prompts)
4. [/Settings](#4-settings)
5. [/Environment](#5-environment)
6. [/Docker](#6-docker)

---

## 1. ملفات التكوين

### 1.1 Structure

```
config/
├── agents/
│   ├── fiqh.yaml
│   ├── hadith.yaml
│   ├── tafsir.yaml
│   ├── aqeedah.yaml
│   ├── seerah.yaml
│   ├── history.yaml
│   ├── usul_fiqh.yaml
│   ├── language.yaml
│   ├── general.yaml
│   └── tazkiyah.yaml
│
prompts/
├── fiqh_agent.txt
├── hadith_agent.txt
├── tafsir_agent.txt
├── aqeedah_agent.txt
├── seerah_agent.txt
├── history_agent.txt
├── general_agent.txt
└── abstain.txt
```

---

## 2. Agent Configs

### 2.1 FiQH Config

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
max_tokens: 2000

max_citations: 5
min_confidence: 0.5

description: "FiQH Collection Agent - Islamic Jurisprudence"

keywords:
  - حكم
  - هل يجوز
  - فريضة
  - واجب
  - سنة
```

---

## 3. Prompts

### 3.1 FiQH Prompt

```
# fiqh_agent.txt

# سؤال المستخدم
{{query}}

# المصادر
{{context}}

# التعليمات
- أجب باللغة العربية الفصحى
- استخدم المذاهب الأربعة عند وجود خلاف
-اذكر رقم المصدر لكل معلومة
- إذا لم تجد إجابة واضحة، قل "لا أعرف"
- تجنب الآراء الشاذة
-اذكر المذهب عند وجود الخلاف الفقهي
```

---

## 4. Settings

### 4.1 Application Settings

```python
# src/config/settings.py

class Settings(BaseSettings):
    """إعدادات التطبيق."""
    
    # API
    api_v1_prefix: str = "/api/v1"
    
    # Database
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    postgres_url: str = "postgresql://user:pass@localhost:5432"
    redis_url: str = "redis://localhost:6379"
    
    # LLM
    openai_api_key: str
    groq_api_key: str
    default_llm: str = "gpt-4"
    
    # Embeddings
    embedding_model: str = "BAAI/bge-m3"
    
    # Agent Config
    agent_config_dir: str = "config/agents"
    prompt_dir: str = "prompts"
    
    class Config:
        env_file = ".env"
```

---

## 5. Environment

### 5.1 .env Example

```
# .env

# API
API_V1_PREFIX=/api/v1

# Database
QDRANT_HOST=localhost
QDRANT_PORT=6333
POSTGRES_URL=postgresql://user:pass@localhost:5432

# LLM
OPENAI_API_KEY=sk-...
GROQ_API_KEY=gsk_...

# Embeddings
EMBEDDING_MODEL=BAAI/bge-m3
```

---

## 6. Docker

### 6.1 docker-compose.yml

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - QDRANT_HOST=qdrant
      - POSTGRES_URL=postgres://postgres:5432
  
  qdrant:
    image: qdrant/qdrant
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage
  
  postgres:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  qdrant_data:
  postgres_data:
```

---

## ملخص

### جدول المتغيرات

| المتغير | الوصف | الافتراضي |
|---------|-------|---------|
| QDRANT_HOST |主机 Qdrant | localhost |
| QDRANT_PORT | منفذ Qdrant | 6333 |
| OPENAI_API_KEY | مفتاح OpenAI | - |
| GROQ_API_KEY | مفتاح Groq | - |
| EMBEDDING_MODEL | نموذج التضمين | BAAI/bge-m3 |

---

**آخر تحديث**: أبريل 2026