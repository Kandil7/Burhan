"""
Query route for Athar Islamic QA system.

Main endpoint that receives user queries, classifies intent,
routes to appropriate agent/tool, and returns structured response.
"""

import uuid
import time
from fastapi import APIRouter, HTTPException, Depends
from src.api.schemas.request import QueryRequest
from src.api.schemas.response import QueryResponse, CitationResponse
from src.core.orchestrator import ResponseOrchestrator
from src.core.router import HybridQueryClassifier
from src.infrastructure.llm_client import get_llm_client
from src.config.logging_config import get_logger

logger = get_logger()
router = APIRouter(prefix="/query", tags=["Query"])


# Singleton orchestrator instance
_orchestrator_instance: ResponseOrchestrator | None = None


def get_orchestrator() -> ResponseOrchestrator:
    """
    Get singleton orchestrator instance.

    Reuses existing instance to avoid recreating agents/tools on each request.
    """
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = ResponseOrchestrator()
    return _orchestrator_instance


@router.post(
    "",
    response_model=QueryResponse,
    summary="Submit query to Athar Islamic QA system",
    description="""
Main query endpoint for Athar Islamic QA system.

Accepts user queries in Arabic or English, classifies intent,
routes to appropriate agent/tool, and returns structured response
with citations.

**Supported Intents:**
- fiqh: Islamic jurisprudence questions
- quran: Quranic verses, surahs, tafsir
- islamic_knowledge: General Islamic knowledge
- greeting: Greetings and salutations
- zakat: Zakat calculation
- inheritance: Inheritance distribution
- dua: Supplications and adhkar
- hijri_calendar: Islamic calendar dates
- prayer_times: Prayer times and qibla direction
    """,
    responses={
        200: {"description": "Successful response with answer and citations"},
        400: {"description": "Invalid request (empty query, bad parameters)"},
        422: {"description": "Validation error"},
        500: {"description": "Internal server error"},
    },
)
async def handle_query(request: QueryRequest, orchestrator: ResponseOrchestrator = Depends(get_orchestrator)):
    """
    Handle user query and return structured response.

    Flow:
    1. Classify intent using HybridQueryClassifier
    2. Route to appropriate agent/tool
    3. Assemble response with citations
    4. Return structured JSON response

    Args:
        request: QueryRequest with query text and optional parameters
        orchestrator: ResponseOrchestrator instance

    Returns:
        QueryResponse with answer, citations, and metadata
    """
    start_time = time.time()
    query_id = str(uuid.uuid4())

    try:
        logger.info(
            "query.received",
            query_id=query_id,
            query=request.query[:50],  # Log first 50 chars
            language=request.language,
            madhhab=request.madhhab,
        )

        # ==========================================
        # Step 1: Classify intent
        # ==========================================
        # Get LLM client for classification
        llm_client = await get_llm_client()
        classifier = HybridQueryClassifier(llm_client=llm_client)
        router_result = await classifier.classify(request.query)

        logger.info(
            "query.classified",
            query_id=query_id,
            intent=router_result.intent.value,
            confidence=router_result.confidence,
            method=router_result.method,
        )

        # ==========================================
        # Step 2: Route to appropriate agent/tool
        # ==========================================
        result = await orchestrator.route_query(
            query=request.query,
            intent=router_result.intent,
            language=request.language or router_result.language,
            location=request.location,
            madhhab=request.madhhab,
            session_id=request.session_id,
        )

        # ==========================================
        # Step 3: Calculate processing time
        # ==========================================
        processing_time = int((time.time() - start_time) * 1000)

        logger.info(
            "query.completed",
            query_id=query_id,
            intent=router_result.intent.value,
            processing_time_ms=processing_time,
            citations_count=len(result.citations),
        )

        # ==========================================
        # Step 4: Build response
        # ==========================================
        return QueryResponse(
            query_id=query_id,
            intent=router_result.intent.value,
            intent_confidence=router_result.confidence,
            answer=result.answer,
            citations=[
                CitationResponse(
                    id=c.id, type=c.type, source=c.source, reference=c.reference, url=c.url, text_excerpt=c.text_excerpt
                )
                for c in result.citations
            ],
            metadata={
                "agent": result.metadata.get("agent", "unknown"),
                "processing_time_ms": processing_time,
                "classification_method": router_result.method,
                **result.metadata,
            },
            follow_up_suggestions=result.metadata.get("follow_up_suggestions", []),
        )

    except ValueError as e:
        logger.warning("query.validation_error", query_id=query_id, error=str(e))
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error("query.error", query_id=query_id, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal error processing query: {str(e)}")
