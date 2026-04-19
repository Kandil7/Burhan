"""
Chatbot Agent for greeting and casual conversation.

This agent handles simple greetings, salam exchanges, and basic conversation
that doesn't require Islamic scholarly retrieval.
"""

import random

from src.agents.base import AgentInput, AgentOutput
from src.config.logging_config import get_logger

logger = get_logger(__name__)


# Greeting responses
SALAM_RESPONSES = [
    "وعليكم السلام ورحمة الله وبركاته",
    "السلام عليكم ورحمة الله",
    "وعليكم السلام، أهلاً وسهلاً",
    "وعليكم السلام ورحمة الله وبركاته، بخدمتكم",
]

# Welcome messages
WELCOME_MESSAGES = [
    "أهلاً بك في نظام أثار للاستشارات الإسلامية",
    "مرحباً بك، أنا في خدمتك للإجابة على أسئلتك الشرعية",
    "أهلاً وسهلاً، تفضل بطرح سؤالك",
]

# Help prompts
HELP_PROMPTS = [
    "يمكنني الإجابة على أسئلتك في:",
    "إليك بعض الموضوعات التي أساعدك فيها:",
    "أساعدك في المواضيع التالية:",
]


class ChatbotAgent:
    """
    Simple chatbot agent for greetings and basic conversation.

    This agent doesn't do RAG - it just responds to greetings and
    provides helpful prompts for Islamic questions.
    """

    def __init__(self):
        self.name = "chatbot_agent"
        self._greetings = SALAM_RESPONSES
        self._welcome = WELCOME_MESSAGES
        self._help = HELP_PROMPTS

    async def execute(self, input: AgentInput) -> AgentOutput:
        """
        Process greeting/chat input.

        Args:
            input: AgentInput with query and metadata

        Returns:
            AgentOutput with response
        """
        query = input.query.lower().strip()

        logger.info("chatbot_agent.execute", query=query[:50])

        # Check for greetings
        if self._is_greeting(query):
            return self._handle_greeting()

        # Check for thanks
        if self._is_thanks(query):
            return self._handle_thanks()

        # Check for help request
        if self._is_help_request(query):
            return self._handle_help()

        # Default - suggest using the system
        return self._handle_default(input)

    def _is_greeting(self, query: str) -> bool:
        """Check if query is a greeting."""
        greeting_patterns = [
            "سلام",
            "salam",
            "aleikum",
            "السلام",
            "مرحبا",
            "أهل",
            "hello",
            "hi",
            "كيف حالك",
            "كيف خبرك",
        ]
        return any(p in query for p in greeting_patterns)

    def _is_thanks(self, query: str) -> bool:
        """Check if query is thanks."""
        thanks_patterns = [
            "شكرا",
            "شكراً",
            "shukran",
            "thanks",
            "thank",
            "جزاك الله",
            "بارك الله",
        ]
        return any(p in query for p in thanks_patterns)

    def _is_help_request(self, query: str) -> bool:
        """Check if user is asking for help."""
        help_patterns = [
            "مساعدة",
            "help",
            "what can",
            "what do you",
            "what can you",
            "ما الذي",
            "كيف يمكنك",
            "tell me about",
            "Tell me about",
        ]
        return any(p in query for p in help_patterns)

    def _handle_greeting(self) -> AgentOutput:
        """Handle greeting response."""
        response = random.choice(self._greetings)

        return AgentOutput(
            answer=response,
            citations=[],
            confidence=0.95,
            metadata={"type": "greeting"},
        )

    def _handle_thanks(self) -> AgentOutput:
        """Handle thanks response."""
        response = "جزاك الله خيراً، أنا في خدمة الإسلام والمسلمين"

        return AgentOutput(
            answer=response,
            citations=[],
            confidence=0.95,
            metadata={"type": "thanks"},
        )

    def _handle_help(self) -> AgentOutput:
        """Handle help request."""
        response = """\
مرحباً! أنا أثار، مساعدك الإسلامي.

إليك ما يمكنني مساعدتك فيه:

1. **الفقه**: أحكام العبادات والمعاملات
2. **الحديث**: أسئلة عن الأحاديث وتفسيرها  
3. **التفسير**: تفسير القرآن الكريم
4. **العقيدة**: التوحيد وصفات الله
5. **السيرة**: سيرة النبي ﷺ
6. **التاريخ**: التاريخ الإسلامي
7. **اللغة**: قواعد العربية
8. **الأدوات**: حساب الزكاة والميراث

Just ask your question!\
"""

        return AgentOutput(
            answer=response,
            citations=[],
            confidence=0.95,
            metadata={"type": "help"},
        )

    def _handle_default(self, input: AgentInput) -> AgentOutput:
        """Handle non-greeting by suggesting the proper system."""
        response = """\
شكراً لتواصلك! 

يمكنني الإجابة على أسئلتك الشرعية فور طرحها.

مثال: "ما حكم الزكاة؟" أو "ما صحة حديث كذا؟"

Just ask your question!\
"""

        return AgentOutput(
            answer=response,
            citations=[],
            confidence=0.7,
            metadata={"type": "suggestion"},
        )


# Singleton instance
chatbot_agent = ChatbotAgent()


__all__ = ["ChatbotAgent", "chatbot_agent"]
