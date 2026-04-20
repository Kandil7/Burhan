# 🕌 دليل التكوين والإعدادات

## شرح التكوين

---

## 1. Settings

### 1.1 Settings

```python
# src/config/settings.py

class Settings(BaseSettings):
    """إعدادات التطبيق."""
    
    # API Settings
    api_v1_prefix: str = "/api/v1"
    api_title: str = "Athar Islamic QA API"
    api_version: str = "0.5.0"
    
    # Qdrant Settings
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_grpc_port: int = 6334
    qdrant_api_key: Optional[str]
    
    # Database Settings
    postgres_url: str = "postgresql://postgres:postgres@localhost:5432/postgres"
    redis_url: str = "redis://localhost:6379"
    
    # LLM Settings
    openai_api_key: Optional[str]
    groq_api_key: Optional[str]
    default_llm: str = "gpt-4"
    llm_temperature: float = 0.3
    llm_max_tokens: int = 2000
    
    # Embedding Settings
    embedding_model: str = "BAAI/bge-m3"
    embedding_device: str = "cuda"
    embedding_batch_size: int = 32
    
    # Agent Config
    agent_config_dir: str = "config/agents"
    prompt_dir: str = "prompts"
    
    # Verification
    verification_enabled: bool = True
    verification_fail_policy: str = "abstain"
    
    # Search Settings
    default_top_k: int = 10
    max_top_k: int = 100
    search_rerank: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

---

## 2. Config Loader

### 2.1 ConfigManager

```python
# src/config/loader.py

class ConfigManager:
    """مدير التكوين."""
    
    def __init__(self, config_dir: str):
        self._config_dir = config_dir
        self._configs: dict = {}
    
    def load(self, name: str) -> dict:
        """تحميل تكوين."""
        if name not in self._configs:
            config_path = f"{self._config_dir}/{name}.yaml"
            with open(config_path) as f:
                self._configs[name] = yaml.safe_load(f)
        return self._configs[name]
    
    def list_agents(self) -> list[str]:
        """قائمة الوكلاء."""
        return [f.stem for f in Path(self._config_dir).glob("*.yaml")]
```

---

## 3. Constants

### 3.1 Constants

```python
# src/config/constants.py

# API
API_VERSION = "0.5.0"
API_TITLE = "Athar Islamic QA API"

# Default values
DEFAULT_TOP_K = 10
MAX_TOP_K = 100

# Collections
DEFAULT_COLLECTION = "default"
FIQH_COLLECTION = "fiqh_passages"
HADITH_COLLECTION = "hadith_passages"

# Embedding
EMBEDDING_MODEL = "BAAI/bge-m3"
EMBEDDING_DIMENSION = 1024

# LLM
DEFAULT_LLM = "gpt-4"
DEFAULT_TEMPERATURE = 0.3
MAX_TOKENS = 2000
```

---

## 4. Environment Validation

### 4.1 validate_environment

```python
# src/config/environment_validation.py

REQUIRED_ENV_VARS = [
    "OPENAI_API_KEY",
]

OPTIONAL_ENV_VARS = [
    "QDRANT_HOST",
    "QDRANT_PORT",
    "GROQ_API_KEY",
]

def validate_environment() -> list[str]:
    """التحقق من البيئة."""
    missing = []
    for var in REQUIRED_ENV_VARS:
        if not os.environ.get(var):
            missing.append(var)
    return missing
```

---

**آخر تحديث**: أبريل 2026