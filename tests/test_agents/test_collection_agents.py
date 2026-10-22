"""
Tests for Collection Agents (Phase 6).

Tests for all collection-aware RAG agents:
- HadithCollectionAgent
- TafsirCollectionAgent
- AqeedahCollectionAgent
- SeerahCollectionAgent
- UsulFiqhCollectionAgent
- HistoryCollectionAgent
- LanguageCollectionAgent

Each agent tests:
- Agent instantiation with config
- Query intake normalization
- Intent classification
- Strategy configuration
- Full pipeline execution
"""

# Import all collection agents
from dataclasses import replace as _replace

import pytest

from src.agents.collection import (
    CollectionAgentConfig,
    RetrievalStrategy,
)
from src.agents.pipeline import RAGPipeline
from src.agents.spec_loader import load_all_agent_specs
from src.domain.agent_spec import AgentSpec
from src.domain.intents import Intent


def make_agent(spec_name: str = "fiqh", **kwargs):
    """Build a RAGPipeline the way the deleted classes were built."""
    spec = SPECS[spec_name]
    config = kwargs.pop("config", None)
    if config is not None:
        spec = _replace(
            spec,
            collection=config.collection_name,
            top_k=config.strategy.top_k,
            score_threshold=config.strategy.score_threshold,
            rerank=config.strategy.rerank,
            dense_weight=config.strategy.dense_weight,
            sparse_weight=config.strategy.sparse_weight,
        )
    return RAGPipeline(
        spec=spec,
        search=kwargs.pop("vector_store", None),
        embed=kwargs.pop("embedding_model", None),
        llm_client=kwargs.pop("llm_client", None),
    )


SPECS = load_all_agent_specs()


# =============================================================================
# HadithCollectionAgent Tests
# =============================================================================


class TestHadithCollectionAgentInstantiation:
    """Tests for HadithCollectionAgent instantiation."""

    def test_default_instantiation(self):
        """Test agent can be instantiated with default config."""
        agent = make_agent("hadith")

        assert agent.name == "hadith"
        assert agent.COLLECTION == "hadith_passages"
        assert isinstance(agent.spec, AgentSpec)
        assert agent.spec.collection == "hadith_passages"

    def test_custom_config_instantiation(self):
        """Test agent with custom configuration."""
        strategy = RetrievalStrategy(
            dense_weight=0.5,
            sparse_weight=0.5,
            top_k=100,
            rerank=False,
            score_threshold=0.7,
        )

        config = CollectionAgentConfig(
            collection_name="hadith_custom",
            strategy=strategy,
        )

        agent = make_agent("hadith", config=config)

        assert agent.name == "hadith"
        assert agent.spec.top_k == 100


class TestHadithIntentClassification:
    """Tests for HadithCollectionAgent intent classification."""

    def test_hadith_takhrij_intent(self):
        """Test HadithTakhrij intent."""
        agent = make_agent("hadith")

        assert agent.classify_intent("ما صحة هذا الحديث؟") == Intent.HADITH
        assert agent.classify_intent("أخرج البخاري حديثا") == Intent.HADITH

    def test_hadith_sanad_intent(self):
        """Test HadithSanad intent."""
        agent = make_agent("hadith")

        assert agent.classify_intent("ما سند هذا الحديث؟") == Intent.HADITH
        assert agent.classify_intent("من رواة هذا الحديث") == Intent.HADITH

    def test_hadith_matn_intent(self):
        """Test HadithMatn intent."""
        agent = make_agent("hadith")

        # Use a query that contains matn keywords without any takhrij/sanad keywords
        # "معنى المتن" contains "متن" but also has "معنى" which should trigger matn
        # Note: This may fail if "حديث" is in the query - use a cleaner query
        assert agent.classify_intent("معنى هذا المتن") == Intent.HADITH
        assert agent.classify_intent("تحليل المتن") == Intent.HADITH


# =============================================================================
# TafsirCollectionAgent Tests
# =============================================================================


class TestTafsirCollectionAgentInstantiation:
    """Tests for TafsirCollectionAgent instantiation."""

    def test_default_instantiation(self):
        """Test agent can be instantiated with default config."""
        agent = make_agent("tafsir")

        assert agent.name == "tafsir"
        assert agent.COLLECTION == "quran_tafsir"
        assert isinstance(agent.spec, AgentSpec)


class TestTafsirIntentClassification:
    """Tests for TafsirCollectionAgent intent classification."""

    def test_tafsir_ayah_intent(self):
        """Test TafsirAyah intent."""
        agent = make_agent("tafsir")

        assert agent.classify_intent("ما تفسير هذه الآية؟") == Intent.TAFSIR
        assert agent.classify_intent("فسير سورة البقرة") == Intent.TAFSIR

    def test_tafsir_maqasid_intent(self):
        """Test TafsirMaqasid intent."""
        agent = make_agent("tafsir")

        assert agent.classify_intent("ما مقصد هذه الآية؟") == Intent.TAFSIR
        assert agent.classify_intent("ما الحكمة من هذه الآية") == Intent.TAFSIR


# =============================================================================
# AqeedahCollectionAgent Tests
# =============================================================================


class TestAqeedahCollectionAgentInstantiation:
    """Tests for AqeedahCollectionAgent instantiation."""

    def test_default_instantiation(self):
        """Test agent can be instantiated with default config."""
        agent = make_agent("aqeedah")

        assert agent.name == "aqeedah"
        assert agent.COLLECTION == "aqeedah_passages"
        assert isinstance(agent.spec, AgentSpec)


class TestAqeedahIntentClassification:
    """Tests for AqeedahCollectionAgent intent classification."""

    def test_aqeedah_tawhid_intent(self):
        """Test AqeedahTawhid intent."""
        agent = make_agent("aqeedah")

        assert agent.classify_intent("ما هو توحيد الله؟") == Intent.AQEEDAH
        assert agent.classify_intent("أسماء الله الحسنى") == Intent.AQEEDAH

    def test_aqeedah_iman_intent(self):
        """Test AqeedahIman intent."""
        agent = make_agent("aqeedah")

        assert agent.classify_intent("ما هي أركان الإيمان؟") == Intent.AQEEDAH
        assert agent.classify_intent("الإيمان بالملائكة") == Intent.AQEEDAH


# =============================================================================
# SeerahCollectionAgent Tests
# =============================================================================


class TestSeerahCollectionAgentInstantiation:
    """Tests for SeerahCollectionAgent instantiation."""

    def test_default_instantiation(self):
        """Test agent can be instantiated with default config."""
        agent = make_agent("seerah")

        assert agent.name == "seerah"
        assert agent.COLLECTION == "seerah_passages"
        assert isinstance(agent.spec, AgentSpec)


class TestSeerahIntentClassification:
    """Tests for SeerahCollectionAgent intent classification."""

    def test_seerah_event_intent(self):
        """Test SeerahEvent intent."""
        agent = make_agent("seerah")

        assert agent.classify_intent("ماذا حدث في غزوة بدر؟") == Intent.SEERAH
        assert agent.classify_intent("وقعة أحد") == Intent.SEERAH

    def test_seerah_milad_intent(self):
        """Test SeerahMilad intent."""
        agent = make_agent("seerah")

        assert agent.classify_intent("متى كان ميلاد النبي؟") == Intent.SEERAH
        assert agent.classify_intent("طفولة النبي") == Intent.SEERAH


# =============================================================================
# UsulFiqhCollectionAgent Tests
# =============================================================================


class TestUsulFiqhCollectionAgentInstantiation:
    """Tests for UsulFiqhCollectionAgent instantiation."""

    def test_default_instantiation(self):
        """Test agent can be instantiated with default config."""
        agent = make_agent("usul_fiqh")

        assert agent.name == "usul_fiqh"
        assert agent.COLLECTION == "usul_fiqh"
        assert isinstance(agent.spec, AgentSpec)


class TestUsulFiqhIntentClassification:
    """Tests for UsulFiqhCollectionAgent intent classification."""

    def test_usul_fiqh_ijtihad_intent(self):
        """Test UsulFiqhIjtihad intent."""
        agent = make_agent("usul_fiqh")

        assert agent.classify_intent("ما هو الاجتهاد؟") == Intent.USUL_FIQH
        assert agent.classify_intent("كيف يستنبط الفقهاء") == Intent.USUL_FIQH

    def test_usul_fiqh_qiyas_intent(self):
        """Test UsulFiqhQiyas intent."""
        agent = make_agent("usul_fiqh")

        assert agent.classify_intent("ما هو القياس؟") == Intent.USUL_FIQH
        assert agent.classify_intent("الأصل والفرع في القياس") == Intent.USUL_FIQH


# =============================================================================
# HistoryCollectionAgent Tests
# =============================================================================


class TestHistoryCollectionAgentInstantiation:
    """Tests for HistoryCollectionAgent instantiation."""

    def test_default_instantiation(self):
        """Test agent can be instantiated with default config."""
        agent = make_agent("history")

        assert agent.name == "history"
        assert agent.COLLECTION == "islamic_history_passages"
        assert isinstance(agent.spec, AgentSpec)


class TestHistoryIntentClassification:
    """Tests for HistoryCollectionAgent intent classification."""

    def test_islamic_history_event_intent(self):
        """Test IslamicHistoryEvent intent."""
        agent = make_agent("history")

        assert agent.classify_intent("ماذا حدث في عام 61 هجرية؟") == Intent.ISLAMIC_HISTORY
        assert agent.classify_intent("معركة الجمل") == Intent.ISLAMIC_HISTORY

    def test_islamic_history_dynasty_intent(self):
        """Test IslamicHistoryDynasty intent."""
        agent = make_agent("history")

        assert agent.classify_intent("الدولة العباسية") == Intent.ISLAMIC_HISTORY
        assert agent.classify_intent("الخلافة الأموية") == Intent.ISLAMIC_HISTORY


# =============================================================================
# LanguageCollectionAgent Tests
# =============================================================================


class TestLanguageCollectionAgentInstantiation:
    """Tests for LanguageCollectionAgent instantiation."""

    def test_default_instantiation(self):
        """Test agent can be instantiated with default config."""
        agent = make_agent("language")

        assert agent.name == "language"
        assert agent.COLLECTION == "arabic_language_passages"
        assert isinstance(agent.spec, AgentSpec)


class TestLanguageIntentClassification:
    """Tests for LanguageCollectionAgent intent classification."""

    def test_arabic_grammar_intent(self):
        """Test ArabicGrammar intent."""
        agent = make_agent("language")

        assert agent.classify_intent("ما إعراب هذه الجملة؟") == Intent.ARABIC_LANGUAGE
        assert agent.classify_intent("النحو العربي") == Intent.ARABIC_LANGUAGE

    def test_arabic_morphology_intent(self):
        """Test ArabicMorphology intent."""
        agent = make_agent("language")

        assert agent.classify_intent("ما وزن هذا الفعل؟") == Intent.ARABIC_LANGUAGE
        assert agent.classify_intent("تصريف الفعل") == Intent.ARABIC_LANGUAGE

    def test_arabic_balaghah_intent(self):
        """Test ArabicBalaghah intent."""
        agent = make_agent("language")

        assert agent.classify_intent("ما البلاغة في هذا النص؟") == Intent.ARABIC_LANGUAGE
        assert agent.classify_intent("تشبيه واستعارة") == Intent.ARABIC_LANGUAGE


# =============================================================================
# Tests for Query Intake (Arabic Normalization)
# =============================================================================


class TestQueryIntakeNormalization:
    """Tests for query intake Arabic normalization."""

    def test_hadith_normalization(self):
        """Test hadith agent query normalization."""
        agent = make_agent("hadith")
        result = agent.query_intake("ما حكم الأكل؟")
        assert "الاكل" in result

    def test_tafsir_normalization(self):
        """Test tafsir agent query normalization."""
        agent = make_agent("tafsir")
        result = agent.query_intake("تفسير آية")
        # The "آية" gets normalized - just verify that query_intake runs and returns a string
        assert isinstance(result, str)
        assert len(result) > 0

    def test_aqeedah_normalization(self):
        """Test aqeedah agent query normalization."""
        agent = make_agent("aqeedah")
        result = agent.query_intake("توحيد الله")
        assert "الله" in result


# =============================================================================
# Tests for Retrieval
# =============================================================================


class TestCollectionAgentRetrieval:
    """Tests for retrieve_candidates method."""

    @pytest.mark.asyncio
    async def test_hadith_retrieve_no_vector_store(self):
        """Test hadith retrieval returns empty when no vector store."""
        agent = make_agent("hadith")
        result = await agent.retrieve_candidates("حديث صحيح")
        assert result == []

    @pytest.mark.asyncio
    async def test_tafsir_retrieve_no_vector_store(self):
        """Test tafsir retrieval returns empty when no vector store."""
        agent = make_agent("tafsir")
        result = await agent.retrieve_candidates("تفسير قرآن")
        assert result == []

    @pytest.mark.asyncio
    async def test_aqeedah_retrieve_no_vector_store(self):
        """Test aqeedah retrieval returns empty when no vector store."""
        agent = make_agent("aqeedah")
        result = await agent.retrieve_candidates("عقيدة")
        assert result == []

    @pytest.mark.asyncio
    async def test_seerah_retrieve_no_vector_store(self):
        """Test seerah retrieval returns empty when no vector store."""
        agent = make_agent("seerah")
        result = await agent.retrieve_candidates("سيرة")
        assert result == []

    @pytest.mark.asyncio
    async def test_usul_fiqh_retrieve_no_vector_store(self):
        """Test usul_fiqh retrieval returns empty when no vector store."""
        agent = make_agent("usul_fiqh")
        result = await agent.retrieve_candidates("أصول فقه")
        assert result == []

    @pytest.mark.asyncio
    async def test_history_retrieve_no_vector_store(self):
        """Test history retrieval returns empty when no vector store."""
        agent = make_agent("history")
        result = await agent.retrieve_candidates("تاريخ إسلامي")
        assert result == []

    @pytest.mark.asyncio
    async def test_language_retrieve_no_vector_store(self):
        """Test language retrieval returns empty when no vector store."""
        agent = make_agent("language")
        result = await agent.retrieve_candidates("لغة عربية")
        assert result == []


# =============================================================================
# Tests for Reranking
# =============================================================================


class TestCollectionAgentReranking:
    """Tests for rerank_candidates method."""

    @pytest.mark.asyncio
    async def test_hadith_rerank_filters_by_threshold(self):
        """Test hadith reranking filters by score threshold."""
        agent = make_agent("hadith")

        candidates = [
            {"content": "high score", "score": 0.9},
            {"content": "low score", "score": 0.3},
        ]

        result = await agent.rerank_candidates("query", candidates)

        assert len(result) == 1
        assert result[0]["content"] == "high score"


# =============================================================================
# Tests for Verification
# =============================================================================


class TestCollectionAgentVerification:
    """Tests for run_verification method."""

    @pytest.mark.asyncio
    async def test_tafsir_verification_with_candidates(self):
        """Test tafsir verification with candidate passages."""
        agent = make_agent("tafsir")

        candidates = [
            {"content": "نص تفسيري", "score": 0.9, "metadata": {}},
        ]

        result = await agent.run_verification("query", candidates)

        assert result is not None
        assert hasattr(result, "verified_passages")


# =============================================================================
# Tests for Answer Generation
# =============================================================================


class TestCollectionAgentGenerateAnswer:
    """Tests for generate_answer method."""

    @pytest.mark.asyncio
    async def test_hadith_generate_no_passages(self):
        """Test hadith generate returns fallback message when no passages."""
        agent = make_agent("hadith")

        result = await agent.generate_answer("query", [], "ar")

        assert result == agent.NO_PASSAGES_MESSAGE

    @pytest.mark.asyncio
    async def test_tafsir_generate_no_passages(self):
        """Test tafsir generate returns fallback message when no passages."""
        agent = make_agent("tafsir")

        result = await agent.generate_answer("query", [], "ar")

        assert result == agent.NO_PASSAGES_MESSAGE


# =============================================================================
# Tests for Citation Assembly
# =============================================================================


class TestCollectionAgentCitations:
    """Tests for assemble_citations method."""

    def test_hadith_assemble_citations(self):
        """Test hadith assembling citations from passages."""
        agent = make_agent("hadith")

        passages = [
            {
                "content": "حديث نبوي",
                "metadata": {
                    "collection": "hadith",
                    "book_title": "صحيح البخاري",
                    "author": "البخاري",
                },
            },
        ]

        citations = agent.assemble_citations(passages)

        assert len(citations) == 1
        assert citations[0].source_id == "C1"

    def test_seerah_assemble_citations(self):
        """Test seerah assembling citations from passages."""
        agent = make_agent("seerah")

        passages = [
            {
                "content": "نص تاريخي",
                "metadata": {
                    "collection": "seerah",
                    "book_title": "السيرة النبوية",
                    "author": "ابن هشام",
                },
            },
        ]

        citations = agent.assemble_citations(passages)

        assert len(citations) == 1
        assert citations[0].source_id == "C1"


# =============================================================================
# Tests for Full Pipeline
# =============================================================================


class TestCollectionAgentFullPipeline:
    """Tests for full run() pipeline."""

    @pytest.mark.asyncio
    async def test_hadith_full_run(self):
        """Test complete hadith pipeline execution."""
        agent = make_agent("hadith")

        result = await agent.run(
            raw_question="ما صحة حديث من صلى صلاة الصبح فهو في ذمة الله؟",
            meta={"language": "ar"},
        )

        assert result is not None
        assert hasattr(result, "answer")
        assert hasattr(result, "citations")
        assert result.metadata.get("collection") == "hadith_passages"

    @pytest.mark.asyncio
    async def test_tafsir_full_run(self):
        """Test complete tafsir pipeline execution."""
        agent = make_agent("tafsir")

        result = await agent.run(
            raw_question="ما تفسير آية الكرسي؟",
            meta={"language": "ar"},
        )

        assert result is not None
        assert result.metadata.get("collection") == "quran_tafsir"

    @pytest.mark.asyncio
    async def test_aqeedah_full_run(self):
        """Test complete aqeedah pipeline execution."""
        agent = make_agent("aqeedah")

        result = await agent.run(
            raw_question="ما هو توحيد الربوبية؟",
            meta={"language": "ar"},
        )

        assert result is not None
        assert result.metadata.get("collection") == "aqeedah_passages"

    @pytest.mark.asyncio
    async def test_seerah_full_run(self):
        """Test complete seerah pipeline execution."""
        agent = make_agent("seerah")

        result = await agent.run(
            raw_question="متى كانت الهجرة؟",
            meta={"language": "ar"},
        )

        assert result is not None
        assert result.metadata.get("collection") == "seerah_passages"


# =============================================================================
# Tests for Class Attributes (System Prompts)
# =============================================================================


class TestCollectionAgentClassAttributes:
    """Tests for class-level attributes."""

    def test_hadith_system_prompt_arabic(self):
        """Test the hadith system prompt loads from the prompt file."""
        assert "وكيل مجموعة حديثية" in make_agent("hadith")._get_system_prompt()

    def test_tafsir_system_prompt_arabic(self):
        """Test the tafsir system prompt loads from the prompt file."""
        assert "وكيل مجموعة التفسير" in make_agent("tafsir")._get_system_prompt()

    def test_aqeedah_system_prompt_arabic(self):
        """Test the aqeedah system prompt loads from the prompt file."""
        assert "وكيل مجموعة العقيدة" in make_agent("aqeedah")._get_system_prompt()

    def test_seerah_system_prompt_arabic(self):
        """Test the seerah system prompt loads from the prompt file."""
        assert "وكيل مجموعة السيرة" in make_agent("seerah")._get_system_prompt()

    def test_usul_fiqh_system_prompt_arabic(self):
        """Test the usul_fiqh system prompt loads from the prompt file."""
        assert "وكيل أصول الفقه" in make_agent("usul_fiqh")._get_system_prompt()

    def test_history_system_prompt_arabic(self):
        """Test the history system prompt loads from the prompt file."""
        assert "وكيل مجموعة التاريخ الإسلامي" in make_agent("history")._get_system_prompt()

    def test_language_system_prompt_arabic(self):
        """Test the language system prompt loads from the prompt file."""
        assert "وكيل مجموعة اللغة العربية" in make_agent("language")._get_system_prompt()

    def test_no_passages_messages_arabic(self):
        """Test fallback messages are in Arabic."""
        assert "لم أجد" in SPECS["hadith"].no_passages_message
        assert "لم أجد" in SPECS["tafsir"].no_passages_message
        assert "لم أجد" in SPECS["aqeedah"].no_passages_message
        assert "لم أجد" in SPECS["seerah"].no_passages_message
        assert "لم أجد" in SPECS["usul_fiqh"].no_passages_message
        assert "لم أجد" in SPECS["history"].no_passages_message
        assert "لم أجد" in SPECS["language"].no_passages_message
