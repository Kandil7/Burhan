"""
Query route for Athar Islamic QA system.

Routes queries to appropriate agents based on intent:
- greeting/chatbot → ChatbotAgent
- fiqh → FiqhAgent (RAG)
- quran → Quran endpoints
- zakat/inheritance/dua/prayer/hijri → Tool endpoints
- general knowledge → GeneralIslamicAgent
"""

import uuid
import time
from fastapi import APIRouter, HTTPException, Depends
from src.api.schemas.request import QueryRequest
from src.api.schemas.response import QueryResponse, CitationResponse
from src.core.router import HybridQueryClassifier
from src.infrastructure.llm_client import get_llm_client
from src.agents.chatbot_agent import ChatbotAgent
from src.agents.fiqh_agent import FiqhAgent
from src.agents.general_islamic_agent import GeneralIslamicAgent
from src.agents.base import AgentInput
from src.config.intents import Intent
from src.config.logging_config import get_logger

logger = get_logger()
router = APIRouter(prefix="/query", tags=["Query"])

# Component instances (reuse across requests)
_chatbot = None
_classifier = None
_fiqh_agent = None
_general_agent = None
_agents_loaded = False

def get_chatbot() -> ChatbotAgent:
    """Get or create chatbot agent."""
    global _chatbot
    if _chatbot is None:
        _chatbot = ChatbotAgent()
    return _chatbot

async def get_classifier() -> HybridQueryClassifier:
    """Get or create query classifier."""
    global _classifier
    if _classifier is None:
        llm_client = await get_llm_client()
        _classifier = HybridQueryClassifier(llm_client=llm_client)
    return _classifier

async def get_fiqh_agent():
    """Get or create FiqhAgent with lazy initialization."""
    global _fiqh_agent, _agents_loaded
    if _fiqh_agent is None and not _agents_loaded:
        try:
            _fiqh_agent = FiqhAgent()
            await _fiqh_agent._initialize()
            _agents_loaded = True
            logger.info("query.fiqh_agent_initialized")
        except Exception as e:
            logger.warning("query.fiqh_agent_init_failed", error=str(e))
            _agents_loaded = True  # Don't retry
    return _fiqh_agent


@router.post(
    "",
    response_model=QueryResponse,
    summary="Submit query to Athar Islamic QA system",
)
async def handle_query(request: QueryRequest):
    """
    Handle user query with intent-based routing.

    Flow:
    1. Classify intent
    2. Route to appropriate agent based on intent
    3. Return structured response with citations
    """
    start_time = time.time()
    query_id = str(uuid.uuid4())

    try:
        logger.info("query.received", query_id=query_id, query=request.query[:50])

        # Get components
        chatbot = get_chatbot()
        classifier = await get_classifier()
        
        # Classify intent
        router_result = await classifier.classify(request.query)
        intent = router_result.intent
        language = request.language or router_result.language
        
        logger.info(
            "query.classified",
            query_id=query_id,
            intent=intent.value,
            confidence=router_result.confidence,
        )

        # Route based on intent
        if intent == Intent.GREETING:
            # Greeting → ChatbotAgent
            agent_result = await chatbot.execute(AgentInput(
                query=request.query,
                language=language,
                metadata={"madhhab": request.madhhab}
            ))
            agent_name = "chatbot_agent"
            
        elif intent == Intent.FIQH:
            # Fiqh → FiqhAgent (RAG with vector store)
            fiqh_agent = await get_fiqh_agent()
            if fiqh_agent and hasattr(fiqh_agent, 'embedding_model') and fiqh_agent.embedding_model:
                agent_result = await fiqh_agent.execute(AgentInput(
                    query=request.query,
                    language=language,
                    metadata={"madhhab": request.madhhab}
                ))
                agent_name = "fiqh_agent"
            else:
                # FiqhAgent not available, use chatbot with helpful message
                agent_result = await chatbot.execute(AgentInput(
                    query=f"أعتذر، لا تتوفر حالياً نصوص فقهية كافية للإجابة. يرجى السؤال عن موضوع آخر.\n\n{request.query}",
                    language=language,
                    metadata={"madhhab": request.madhhab}
                ))
                agent_name = "chatbot_fallback"
                
        elif intent == Intent.ISLAMIC_KNOWLEDGE:
            # General Islamic → GeneralIslamicAgent or Chatbot
            agent_result = await chatbot.execute(AgentInput(
                query=request.query,
                language=language,
                metadata={"madhhab": request.madhhab}
            ))
            agent_name = "general_islamic_agent"
            
        else:
            # Default → ChatbotAgent
            agent_result = await chatbot.execute(AgentInput(
                query=request.query,
                language=language,
                metadata={"madhhab": request.madhhab}
            ))
            agent_name = "chatbot_agent"

        processing_time = int((time.time() - start_time) * 1000)
        
        logger.info(
            "query.completed",
            query_id=query_id,
            intent=intent.value,
            agent=agent_name,
            processing_time_ms=processing_time,
        )

        return QueryResponse(
            query_id=query_id,
            intent=intent.value,
            intent_confidence=router_result.confidence,
            answer=agent_result.answer,
            citations=[
                CitationResponse(
                    id=c.id, type=c.type, source=c.source, reference=c.reference, url=c.url, text_excerpt=c.text_excerpt
                )
                for c in agent_result.citations
            ],
            metadata={
                "agent": agent_name,
                "processing_time_ms": processing_time,
                "classification_method": router_result.method,
                **agent_result.metadata,
            },
            follow_up_suggestions=agent_result.metadata.get("follow_up_suggestions", []),
        )

    except ValueError as e:
        logger.warning("query.validation_error", query_id=query_id, error=str(e))
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error("query.error", query_id=query_id, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/test")
async def test_query():
    """Test endpoint to verify query router is working."""
    chatbot = get_chatbot()
    result = await chatbot.execute(AgentInput(query="السلام عليكم", language="ar", metadata={}))
    return {"status": "ok", "chatbot": chatbot.name, "answer": result.answer, "agent_meta": result.metadata}
