"""
Quran Agent for Athar Islamic QA system.

Integrates all Quran components:
- Verse Retrieval
- NL2SQL Analytics
- Quotation Validation
- Tafsir Retrieval

Routes queries via QuranSubRouter and assembles responses.
Phase 3: Complete Quran pipeline agent.
"""

from typing import Optional

from sqlalchemy.orm import Session

from src.agents.base import BaseAgent, AgentInput, AgentOutput, Citation
from src.quran.quran_router import QuranSubRouter, QuranSubIntent
from src.quran.verse_retrieval import VerseRetrievalEngine
from src.quran.nl2sql import NL2SQLEngine
from src.quran.quotation_validator import QuotationValidator
from src.quran.tafsir_retrieval import TafsirRetrievalEngine
from src.config.logging_config import get_logger

logger = get_logger()


class QuranAgent(BaseAgent):
    """
    Agent for handling all Quran-related queries.

    Routes queries to specialized components:
    - Verse lookup → VerseRetrievalEngine
    - Analytics → NL2SQLEngine
    - Validation → QuotationValidator
    - Tafsir → TafsirRetrievalEngine

    Usage:
        agent = QuranAgent(session)
        result = await agent.execute(AgentInput(query="كم عدد آيات سورة البقرة؟"))
    """

    name = "quran_agent"

    def __init__(self, session: Session, llm_client=None):
        """
        Initialize Quran agent with all sub-components.

        Args:
            session: Database session
            llm_client: LLM client for NL2SQL and routing
        """
        self.session = session
        self.router = QuranSubRouter(llm_client)
        self.verse_engine = VerseRetrievalEngine(session)
        self.nl2sql_engine = NL2SQLEngine(session)
        self.quotation_validator = QuotationValidator(session)
        self.tafsir_engine = TafsirRetrievalEngine(session)

    async def execute(self, input: AgentInput) -> AgentOutput:
        """
        Execute Quran agent logic.

        Routes query to appropriate component based on sub-intent.

        Args:
            input: AgentInput with query

        Returns:
            AgentOutput with answer and metadata
        """
        query = input.query

        try:
            # Step 1: Classify sub-intent
            sub_intent = await self.router.classify(query)
            logger.info("quran_agent.classified", query=query[:50], sub_intent=sub_intent.value)

            # Step 2: Route to appropriate handler
            if sub_intent == QuranSubIntent.VERSE_LOOKUP:
                result = await self._handle_verse_lookup(query, input)
            elif sub_intent == QuranSubIntent.INTERPRETATION:
                result = await self._handle_interpretation(query, input)
            elif sub_intent == QuranSubIntent.ANALYTICS:
                result = await self._handle_analytics(query, input)
            elif sub_intent == QuranSubIntent.QUOTATION_VALIDATION:
                result = await self._handle_quotation_validation(query, input)
            else:
                result = await self._handle_verse_lookup(query, input)

            logger.info("quran_agent.completed", sub_intent=sub_intent.value, confidence=result.confidence)

            return result

        except Exception as e:
            logger.error("quran_agent.error", error=str(e), exc_info=True)
            return AgentOutput(
                answer=f"Error processing Quran query: {str(e)}", confidence=0.0, metadata={"error": str(e)}
            )

    async def _handle_verse_lookup(self, query: str, input: AgentInput) -> AgentOutput:
        """Handle verse lookup queries."""
        # Extract reference from query
        import re

        ref_match = re.search(r"(\d+)\s*[:\-]\s*(\d+)", query)

        if ref_match:
            surah = ref_match.group(1)
            ayah = ref_match.group(2)
            ref = f"{surah}:{ayah}"
        else:
            ref = query  # Let engine auto-detect

        verse = await self.verse_engine.lookup(ref, include_translation=True)

        answer = (
            f"**{verse['surah_name_en']} ({verse['surah_number']}:{verse['ayah_number']})**\n\n"
            f"{verse['text_uthmani']}\n\n"
        )

        if verse.get("translations"):
            for trans in verse["translations"]:
                answer += f"*{trans['text']}*\n"

        answer += f"\n🔗 {verse['quran_url']}"

        return AgentOutput(
            answer=answer,
            citations=[
                Citation(
                    id="C1",
                    type="quran",
                    source=f"Quran {verse['surah_number']}:{verse['ayah_number']}",
                    reference=f"{verse['surah_name_en']} - Ayah {verse['ayah_number']}",
                    url=verse["quran_url"],
                    text_excerpt=verse["text_uthmani"][:100],
                )
            ],
            metadata={"sub_intent": "verse_lookup", "surah": verse["surah_number"], "ayah": verse["ayah_number"]},
            confidence=1.0,
        )

    async def _handle_interpretation(self, query: str, input: AgentInput) -> AgentOutput:
        """Handle tafsir/interpretation queries."""
        # Try to extract verse reference
        import re

        ref_match = re.search(r"(\d+)\s*[:\-]\s*(\d+)", query)

        if ref_match:
            ref = f"{ref_match.group(1)}:{ref_match.group(2)}"
            tafsir = await self.tafsir_engine.get_tafsir(ref)

            answer = f"**Tafsir for {tafsir['ayah']['surah_name_en']} ({tafsir['ayah']['surah_number']}:{tafsir['ayah']['ayah_number']})**\n\n"

            for t in tafsir["tafsirs"]:
                answer += f"**{t['author']}:**\n{t['text'][:300]}...\n\n"

            answer += f"🔗 {tafsir['ayah']['quran_url']}"

            return AgentOutput(
                answer=answer,
                citations=[
                    Citation(
                        id="C1",
                        type="tafsir",
                        source=tafsir["tafsirs"][0]["source"] if tafsir["tafsirs"] else "Unknown",
                        reference=f"Tafsir for {tafsir['ayah']['surah_name_en']} {tafsir['ayah']['ayah_number']}",
                        text_excerpt=tafsir["tafsirs"][0]["text"][:100] if tafsir["tafsirs"] else "",
                    )
                ],
                metadata={"sub_intent": "interpretation"},
                confidence=0.9,
            )
        else:
            return AgentOutput(
                answer="Please specify a verse reference for tafsir (e.g., '2:255' or 'البقرة 255')",
                confidence=0.5,
                metadata={"sub_intent": "interpretation", "needs_reference": True},
            )

    async def _handle_analytics(self, query: str, input: AgentInput) -> AgentOutput:
        """Handle analytics/statistics queries via NL2SQL."""
        result = await self.nl2sql_engine.execute(query)

        answer = result["formatted_answer"]

        return AgentOutput(
            answer=answer,
            citations=[],
            metadata={"sub_intent": "analytics", "sql": result["sql"], "row_count": result["row_count"]},
            confidence=1.0,  # NL2SQL is deterministic
        )

    async def _handle_quotation_validation(self, query: str, input: AgentInput) -> AgentOutput:
        """Handle quotation validation queries."""
        # Extract text from query
        import re

        text_match = re.search(r'["""](.+?)["""]', query)
        text = text_match.group(1) if text_match else query

        validation = await self.quotation_validator.validate(text)

        if validation["is_quran"]:
            ayah = validation["matched_ayah"]
            answer = (
                f"✅ **Yes, this is a Quranic verse.**\n\n"
                f"**Match:** {ayah['surah_name_en']} {ayah['surah_number']}:{ayah['ayah_number']}\n\n"
                f"{ayah['text_uthmani']}\n\n"
                f"🔗 {ayah['quran_url']}"
            )
            confidence = validation["confidence"]
        else:
            answer = f"❌ **This text is not from the Quran.**\n\n{validation.get('suggestion', '')}"
            confidence = 0.0

        return AgentOutput(
            answer=answer,
            citations=[
                Citation(
                    id="C1",
                    type="quran",
                    source="Quran Verification",
                    reference="Quotation Validation",
                )
            ]
            if validation["is_quran"]
            else [],
            metadata={
                "sub_intent": "quotation_validation",
                "is_quran": validation["is_quran"],
                "confidence_score": validation["confidence"],
            },
            confidence=confidence,
        )
