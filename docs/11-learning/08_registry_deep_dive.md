# 📂 الملف 4: `src/core/registry.py` - مسجل الوكلاء (190 سطر)

## 1️⃣ وظيفة الملف

هذا الملف يحتوي على **AgentRegistry** - النظام الذي **يسجل** كل الوكلاء والأدوات ثم **يجدهم** عند الحاجة.

بدون Registry، لا يمكن للنظام معرفة أي وكيل يستخدم لكل سؤال.

---

## 2️⃣ نظرة عامة

| القسم | الأسطر | المحتوى |
|-------|--------|---------|
| Imports | 1-15 | مكتبات أساسية |
| AgentRegistration | 16-30 | dataclass للتسجيل |
| AgentRegistry class | 31-170 | الفئة الرئيسية |
| Global functions | 171-190 | دوال عالمية |

---

## 3️⃣ شرح سطر بسطر

### الأسطر 1-15: Imports

```python
from typing import Optional, Type
from dataclasses import dataclass, field

from src.config.logging_config import get_logger
from src.config.intents import Intent, INTENT_ROUTING
from src.agents.base import BaseAgent
from src.tools.base import BaseTool

logger = get_logger()
```

**شرح**:

| الاستيراد | السبب |
|-----------|-------|
| `Optional` | للقيم التي قد تكون None |
| `Type` | لأنواع الفئات |
| `dataclass, field` | لإنشاء dataclasses بسهولة |
| `get_logger` | لتسجيل الأحداث |
| `Intent, INTENT_ROUTING` | لأنواع النية والتوجيه |
| `BaseAgent` | الفئة الأساسية للوكلاء |
| `BaseTool` | الفئة الأساسية للأدوات |

---

### الأسطر 16-30: AgentRegistration dataclass

```python
@dataclass
class AgentRegistration:
    """Registration info for an agent or tool."""

    name: str
    instance: BaseAgent | BaseTool
    is_agent: bool
    intents: list[Intent] = field(default_factory=list)
    description: str = ""
```

**شرح كل حقل**:

| الحقل | النوع | الوصف | مثال |
|-------|-------|-------|------|
| `name` | str | اسم الوكيل/الأداة | "fiqh_agent", "zakat_tool" |
| `instance` | BaseAgent \| BaseTool | النفسة الفعلية | FiqhAgent() |
| `is_agent` | bool | هل هو وكيل (وليس أداة)؟ | True, False |
| `intents` | list[Intent] | النيات التي يتعامل معها | [Intent.FIQH] |
| `description` | str | وصف مختصر | "Answers fiqh questions" |

**لماذا dataclass؟**:
- يسهل إنشاء كائنات بسيطة
- يولد `__init__`, `__repr__` تلقائياً
- يحفظ البيانات فقط (بدون منطق معقد)

---

### الأسطر 31-70: فئة AgentRegistry

```python
class AgentRegistry:
    """
    Central registry for all agents and tools.

    Provides:
    - Registration of agents and tools
    - Lookup by name
    - Lookup by intent
    - Status reporting
    """

    def __init__(self):
        self.agents: dict[str, BaseAgent] = {}
        self.tools: dict[str, BaseTool] = {}
        self._registrations: dict[str, AgentRegistration] = {}
        self._initialized = False
```

**شرح المتغيرات**:

| المتغير | النوع | الوصف | مثال |
|---------|-------|-------|------|
| `agents` | dict[str, BaseAgent] | قاموس الوكلاء بالاسم | {"fiqh_agent": FiqhAgent()} |
| `tools` | dict[str, BaseTool] | قاموس الأدوات بالاسم | {"zakat_tool": ZakatCalculator()} |
| `_registrations` | dict[str, AgentRegistration] | معلومات التسجيل الكاملة | {"fiqh_agent": AgentRegistration(...)} |
| `_initialized` | bool | هل تم التهيئة؟ | True, False |

**كيف يعمل**:

```python
# بعد التهيئة:
registry.agents = {
    "fiqh_agent": <Agent: fiqh_agent>,
    "chatbot_agent": <Agent: chatbot_agent>,
    "hadith_agent": <Agent: hadith_agent>,
    "seerah_agent": <Agent: seerah_agent>,
}

registry.tools = {
    "zakat_tool": <Tool: zakat_tool>,
    "inheritance_tool": <Tool: inheritance_tool>,
    "prayer_tool": <Tool: prayer_tool>,
    "hijri_tool": <Tool: hijri_tool>,
    "dua_tool": <Tool: dua_tool>,
}
```

---

### الأسطر 71-100: register_agent()

```python
    def register_agent(self, name: str, agent: BaseAgent, intents: list[Intent] = None, description: str = ""):
        """
        Register an agent.

        Args:
            name: Agent name (e.g., "fiqh_agent")
            agent: Agent instance
            intents: List of intents this agent handles
            description: Agent description
        """
        if intents is None:
            # Auto-detect from INTENT_ROUTING
            intents = [i for i, target in INTENT_ROUTING.items() if target == name]

        self.agents[name] = agent
        self._registrations[name] = AgentRegistration(
            name=name, instance=agent, is_agent=True, intents=intents, description=description
        )

        logger.info("registry.agent_registered", name=name, intents=[i.value for i in intents])
```

**شرح**:

```python
# مثال استخدام:
registry.register_agent("fiqh_agent", FiqhAgent())

# ما يحدث:
# 1. intents is None → True
# 2. auto-detect من INTENT_ROUTING:
#    - INTENT_ROUTING[Intent.FIQH] = "fiqh_agent" → ✅
#    - intents = [Intent.FIQH]
# 3. self.agents["fiqh_agent"] = FiqhAgent()
# 4. self._registrations["fiqh_agent"] = AgentRegistration(...)
# 5. logger.info("registry.agent_registered", name="fiqh_agent", intents=["fiqh"])
```

**لماذا auto-detect؟**:
- لا يحتاج المطور لتمرير intents يدوياً
- يقرأ من INTENT_ROUTING تلقائياً
- يقلل الأخطاء

---

### الأسطر 101-130: register_tool()

```python
    def register_tool(self, name: str, tool: BaseTool, intents: list[Intent] = None, description: str = ""):
        """
        Register a tool.

        Args:
            name: Tool name (e.g., "zakat_tool")
            tool: Tool instance
            intents: List of intents this tool handles
            description: Tool description
        """
        if intents is None:
            # Auto-detect from INTENT_ROUTING
            intents = [i for i, target in INTENT_ROUTING.items() if target == name]

        self.tools[name] = tool
        self._registrations[name] = AgentRegistration(
            name=name, instance=tool, is_agent=False, intents=intents, description=description
        )

        logger.info("registry.tool_registered", name=name, intents=[i.value for i in intents])
```

**شرح**:

```python
# مثال استخدام:
registry.register_tool("zakat_tool", ZakatCalculator(gold_price=75, silver_price=0.9))

# ما يحدث:
# 1. auto-detect من INTENT_ROUTING:
#    - INTENT_ROUTING[Intent.ZAKAT] = "zakat_tool" → ✅
#    - intents = [Intent.ZAKAT]
# 2. self.tools["zakat_tool"] = ZakatCalculator(...)
# 3. self._registrations["zakat_tool"] = AgentRegistration(is_agent=False, ...)
```

**الفرق بين register_agent و register_tool**:

| الوجه | register_agent | register_tool |
|-------|---------------|---------------|
| `is_agent` | True | False |
| يخزن في | self.agents | self.tools |
| مثال | FiqhAgent | ZakatCalculator |

---

### الأسطر 131-150: get_agent() و get_tool()

```python
    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """Get agent by name."""
        return self.agents.get(name)

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get tool by name."""
        return self.tools.get(name)
```

**شرح**:

```python
agent = registry.get_agent("fiqh_agent")
# يرجع: FiqhAgent()

agent = registry.get_agent("unknown_agent")
# يرجع: None

tool = registry.get_tool("zakat_tool")
# يرجع: ZakatCalculator()
```

**لماذا Optional؟**:
- قد لا يكون الوكيل موجود
- يرجع None بدلاً من رمي خطأ

---

### الأسطر 151-180: get_for_intent()

```python
    def get_for_intent(self, intent: Intent) -> tuple[Optional[BaseAgent | BaseTool], bool]:
        """
        Get agent or tool for an intent.

        Args:
            intent: The intent to look up

        Returns:
            Tuple of (instance, is_agent)
        """
        target = INTENT_ROUTING.get(intent)
        if not target:
            return None, False

        # Try agents first
        if target in self.agents:
            return self.agents[target], True

        # Then tools
        if target in self.tools:
            return self.tools[target], False

        return None, False
```

**شرح**:

```python
# مثال 1: Intent.FIQH
# 1. target = INTENT_ROUTING[Intent.FIQH] = "fiqh_agent"
# 2. "fiqh_agent" in self.agents → ✅ True
# 3. يرجع: (FiqhAgent(), True)

# مثال 2: Intent.ZAKAT
# 1. target = INTENT_ROUTING[Intent.ZAKAT] = "zakat_tool"
# 2. "zakat_tool" in self.agents → False
# 3. "zakat_tool" in self.tools → ✅ True
# 4. يرجع: (ZakatCalculator(), False)

# مثال 3: Intent.TAFSIR (محذوف)
# 1. target = INTENT_ROUTING[Intent.TAFSIR] = "general_islamic_agent"
# 2. "general_islamic_agent" في self.agents → True
# 3. يرجع: (GeneralIslamicAgent(), True)
```

**لماذا tuple؟**:
- يحتاج لمعرفة هل هو Agent أم Tool
- المعاملة مختلفة (Agent يحتاج RAG, Tool لا يحتاج)

---

### الأسطر 181-200: دوال مساعدة

```python
    def is_available(self, name: str) -> bool:
        """Check if agent or tool is available."""
        return name in self.agents or name in self.tools

    def list_agents(self) -> list[str]:
        """List all registered agent names."""
        return list(self.agents.keys())

    def list_tools(self) -> list[str]:
        """List all registered tool names."""
        return list(self.tools.keys())

    def get_status(self) -> dict:
        """Get registry status."""
        return {
            "agents": list(self.agents.keys()),
            "tools": list(self.tools.keys()),
            "total": len(self.agents) + len(self.tools),
            "initialized": self._initialized,
        }
```

**شرح**:

```python
registry.is_available("fiqh_agent")       # True
registry.is_available("unknown_agent")    # False

registry.list_agents()  # ["fiqh_agent", "chatbot_agent", "hadith_agent", "seerah_agent"]
registry.list_tools()   # ["zakat_tool", "inheritance_tool", "prayer_tool", "hijri_tool", "dua_tool"]

registry.get_status()
# {
#     "agents": ["fiqh_agent", "chatbot_agent", "hadith_agent", "seerah_agent"],
#     "tools": ["zakat_tool", "inheritance_tool", "prayer_tool", "hijri_tool", "dua_tool"],
#     "total": 9,
#     "initialized": True
# }
```

---

### الأسطر 201-230: Global functions

```python
# Global registry instance
_registry: Optional[AgentRegistry] = None


def get_registry() -> AgentRegistry:
    """Get global agent registry instance."""
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
    return _registry
```

**شرح**:

```python
# Singleton pattern
registry1 = get_registry()
registry2 = get_registry()

# registry1 is registry2 → True (نفس النفسة!)
```

**لماذا Singleton؟**:
- نريد نسخة واحدة فقط في التطبيق
- كل الوكلاء يسجلون في نفس النفسة
- يوفر الذاكرة

---

### الأسطر 231-270: initialize_registry()

```python
def initialize_registry() -> AgentRegistry:
    """
    Initialize registry with default agents and tools.

    Call this during application startup.
    """
    global _registry
    _registry = AgentRegistry()

    # Import and register defaults
    from src.tools.zakat_calculator import ZakatCalculator
    from src.tools.inheritance_calculator import InheritanceCalculator
    from src.tools.prayer_times_tool import PrayerTimesTool
    from src.tools.hijri_calendar_tool import HijriCalendarTool
    from src.tools.dua_retrieval_tool import DuaRetrievalTool
    from src.agents.chatbot_agent import ChatbotAgent

    # Register tools
    _registry.register_tool("zakat_tool", ZakatCalculator(gold_price_per_gram=75.0, silver_price_per_gram=0.9))
    _registry.register_tool("inheritance_tool", InheritanceCalculator())
    _registry.register_tool("prayer_tool", PrayerTimesTool())
    _registry.register_tool("hijri_tool", HijriCalendarTool())
    _registry.register_tool("dua_tool", DuaRetrievalTool())

    # Register chatbot agent
    _registry.register_agent("chatbot_agent", ChatbotAgent())

    _registry._initialized = True
    logger.info("registry.initialized", status=_registry.get_status())

    return _registry
```

**شرح**:

```python
# ما يحدث عند الاستدعاء:
# 1. _registry = AgentRegistry()  ← ينشئ نسخة جديدة
# 2. يستورد الوكلاء والأدوات
# 3. يسجل 5 أدوات:
#    - zakat_tool
#    - inheritance_tool
#    - prayer_tool
#    - hijri_tool
#    - dua_tool
# 4. يسجل 1 وكيل:
#    - chatbot_agent
# 5. _registry._initialized = True
# 6. logger.info("registry.initialized", status={...})
```

**لماذا imports داخل الدالة؟**:
- يؤجل الاستيراد حتى الحاجة (lazy import)
- يتجنب circular dependencies
- يسرع بدء التطبيق

**ملاحظة**: FiqhAgent, HadithAgent, GeneralIslamicAgent **غير مسجلين هنا**!
- يسجلون ديناميكياً عند الحاجة
- أو يجب إضافتهم يدوياً

---

## 5️⃣ الخلاصة العملية

### ما الذي يجب أن تفهمه فعلاً؟

1. **Registry يدير كل الوكلاء والأدوات**
2. **Singleton pattern** - نسخة واحدة فقط
3. **Auto-detect** من INTENT_ROUTING
4. **get_for_intent()** يستخدم في Orchestrator

### 📝 تمرين صغير

1. ما الفرق بين `register_agent()` و `register_tool()`؟
2. لماذا `is_agent` في الـ tuple؟
3. لماذا imports داخل `initialize_registry()`؟

### 🔜 الخطوة التالية

اقرأ الملف 5: `src/core/citation.py`

---

**📖 الدليل الكامل:** [`docs/mentoring/`](docs/mentoring/)
