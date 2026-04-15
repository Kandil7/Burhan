"""
Chatbot Agent (Greeting Agent) for Athar Islamic QA system.


"""
import random

from src.agents.base import AgentInput, AgentOutput, BaseAgent
from src.config.logging_config import get_logger

logger = get_logger()

# ── Greeting templates ────────────────────────────────────────────────────────

GREETINGS_AR = [
    {"text": "وعليكم السلام ورحمة الله وبركاته",    "translation": "And upon you be peace, mercy, and blessings of Allah"},
    {"text": "أهلاً وسهلاً",                         "translation": "Welcome"},
    {"text": "حياك الله",                            "translation": "May Allah greet you"},
]

GREETINGS_EN = [
    {"text": "Wa alaikum assalam wa rahmatullahi wa barakatuh", "translation": "And upon you be peace, mercy, and blessings of Allah"},
    {"text": "Welcome! How can I help you today?",              "translation": None},
    {"text": "Assalamu alaikum! May Allah bless you",           "translation": "Peace be upon you"},
]

RAMADAN_GREETINGS = [
    {"text": "رمضان مبارك! تقبل الله منا ومنكم",                              "translation": "Ramadan Mubarak! May Allah accept from us and you"},
    {"text": "Ramadan Kareem! May this blessed month bring you closer to Allah", "translation": None},
]

EID_GREETINGS = [
    {"text": "عيد مبارك! تقبل الله منا ومنكم صالح الأعمال", "translation": "Eid Mubarak! May Allah accept our good deeds"},
    {"text": "Eid Mubarak! May Allah bless you and your family", "translation": None},
]

# ── Small talk templates ──────────────────────────────────────────────────────

SMALL_TALK_AR = {
    "how_are_you": [
        {"text": "الحمد لله، بخير والحمد لله. كيف يمكنني مساعدتك؟",
         "translation": "Praise be to Allah, I'm well. How can I help you?"},
    ],
    "thank_you": [
        {"text": "العفو، جزاك الله خيراً",
         "translation": "You're welcome, may Allah reward you with good"},
    ],
    "unknown": [
        {"text": "كيف يمكنني مساعدتك في أمور الدين؟",
         "translation": "How can I assist you with religious matters?"},
    ],
}

SMALL_TALK_EN = {
    "how_are_you": [
        {"text": "Alhamdulillah, I'm well. How can I assist you today?", "translation": None},
    ],
    "thank_you": [
        {"text": "You're welcome! JazakAllahu khayran (may Allah reward you with good)", "translation": None},
    ],
    "unknown": [
        {"text": "How can I help you with Islamic knowledge today?", "translation": None},
    ],
}


class ChatbotAgent(BaseAgent):
    """
    Agent for handling greetings and small conversation.
    Template-based — no LLM generation required.
    """

    name = "chatbot"

    def __init__(self) -> None:
        super().__init__()

    async def execute(self, input: AgentInput) -> AgentOutput:
        
        meta       = input.metadata or {}
        is_ramadan = meta.get("is_ramadan", False)
        is_eid     = meta.get("is_eid",     False)

        query    = input.query.lower()
        language = input.language or self._detect_language(input.query)

        is_greeting   = self._is_greeting(query)
        is_small_talk = self._is_small_talk(query)

        if is_greeting:
            response_type = "greeting"
            if is_ramadan:
                response = random.choice(RAMADAN_GREETINGS)
            elif is_eid:
                response = random.choice(EID_GREETINGS)
            elif language == "ar":
                response = random.choice(GREETINGS_AR)
            else:
                response = random.choice(GREETINGS_EN)

        elif is_small_talk:
            response_type = "small_talk"
            intent    = self._classify_small_talk(query)   
            templates = SMALL_TALK_AR if language == "ar" else SMALL_TALK_EN
            response  = random.choice(templates.get(intent, templates["unknown"]))

        else:
            response_type = "unrecognized"
            response = {
                "text": (
                    "أعتذر، لم أفهم سؤالك بشكل كامل. يرجى السؤال عن:\n"
                    "- أحكام فقهية\n- آيات قرآنية\n- زكاة أو ميراث\n- أذكار وأدعية\n\n"
                    "I apologize, I didn't fully understand. Please ask about:\n"
                    "- Islamic rulings\n- Quran verses\n- Zakat or inheritance\n- Duas and adhkar"
                ),
                "translation": None,
            }

        # Build answer
        answer = response["text"]
        if response.get("translation"):
            answer += f"\n\n({response['translation']})"

        logger.info(
            "chatbot.response",
            query=input.query[:50],
            language=language,
            response_type=response_type,   
        )

        return AgentOutput(
            answer=answer,
            citations=[],
            metadata={
                "agent":         self.name,
                "language":      language,
                "response_type": response_type,   
            },
            confidence=0.95,
        )

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _is_greeting(self, query: str) -> bool:
        keywords = [
            "سلام", "السلام", "مرحبا", "اهلا", "هلا",
            "hello", "hi", "hey", "greetings", "assalam",
            "ramadan", "eid", "رمضان", "عيد",
        ]
        return any(kw in query.lower() for kw in keywords)

    def _is_small_talk(self, query: str) -> bool:
        keywords = [
            "كيف حالك", "كيفك", "شلونك", "عامل",
            "how are you", "how do you do",
            "شكراً", "شكرا", "ممنون", "جزاك",
            "thank", "thanks", "jazak",
        ]
        return any(kw in query.lower() for kw in keywords)

    def _classify_small_talk(self, query: str) -> str:
        """
        Fix #2 + #6 — applies .lower() internally; returns 'unknown' not None.
        """
        q = query.lower()
        if any(k in q for k in ["كيف حالك", "كيفك", "how are you"]):
            return "how_are_you"
        if any(k in q for k in ["شكر", "thank", "جزاك"]):
            return "thank_you"
        return "unknown"   

    def _detect_language(self, query: str) -> str:
        arabic_chars = sum(1 for c in query if "\u0600" <= c <= "\u06FF")
        total_chars  = len(query.replace(" ", ""))
        if total_chars == 0:
            return "ar"
        return "ar" if (arabic_chars / total_chars) > 0.3 else "en"