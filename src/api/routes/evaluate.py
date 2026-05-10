"""
Evaluation endpoint for Burhan Islamic QA system.

Runs evaluation on JSONL datasets using LLM-based intent classifier
and calculates retrieval/answer quality metrics.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from src.config.logging_config import get_logger

logger = get_logger("Burhan.api.evaluate")

evaluate_router = APIRouter(prefix="/evaluate", tags=["Evaluate"])

# =============================================================================
# Data Models
# =============================================================================


class EvaluationRunRequest(BaseModel):
    """Request to run evaluation on a dataset."""

    dataset: str = Field(..., description="Dataset name: 'seerah' or 'spirituality'")
    limit: int = Field(default=5, ge=1, le=50, description="Number of queries to evaluate")
    use_llm_classifier: bool = Field(default=True, description="Use LLM-based intent classifier")


class DatasetItem(BaseModel):
    """Single item from evaluation dataset."""

    query: str
    query_type: str
    collection: str
    gold_passages: list[dict[str, Any]]
    difficulty: str | None = None
    language: str | None = None


class QueryEvaluationResult(BaseModel):
    """Evaluation result for a single query."""

    query: str
    query_type: str
    detected_intent: str | None = None
    intent_confidence: float = 0.0
    intent_method: str | None = None
    collection: str
    retrieved_count: int = 0
    gold_passages_count: int = 0
    retrieved_ids: list[str] = []
    gold_ids: list[str] = []
    recall_at_k: float = 0.0
    precision_at_k: float = 0.0
    processing_time_ms: int = 0
    error: str | None = None


class EvaluationRunResponse(BaseModel):
    """Response for evaluation run."""

    dataset: str
    total_queries: int
    successful: int
    failed: int
    results: list[QueryEvaluationResult]
    metrics: dict[str, float]
    processing_time_ms: int


# =============================================================================
# Dataset Loading
# =============================================================================


def load_dataset(dataset_name: str, limit: int) -> list[DatasetItem]:
    """Load evaluation dataset from JSONL file."""
    base_path = Path(__file__).parent.parent.parent / "evaluation"

    if dataset_name == "seerah":
        file_path = base_path / "seerah_real_user_eval.jsonl"
    elif dataset_name == "spirituality":
        file_path = base_path / "spirituality_real_user_eval.jsonl"
    else:
        raise ValueError(f"Unknown dataset: {dataset_name}")

    if not file_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {file_path}")

    items = []
    with open(file_path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= limit:
                break
            try:
                data = json.loads(line.strip())
                items.append(DatasetItem(**data))
            except json.JSONDecodeError as e:
                logger.warning("Skipping invalid JSON line", line_number=i + 1, error=str(e))
                continue

    return items


# =============================================================================
# LLM Intent Classifier Integration
# =============================================================================


async def create_fresh_llm_classifier() -> "LLMIntentClassifier":
    """Create a fresh LLM classifier instance for each request."""
    import os

    from openai import AsyncOpenAI

    from src.config.settings import settings
    from src.infrastructure.llm.llm_classifier import LLMIntentClassifier

    try:
        os.environ["TOKENIZERS_PARALLELISM"] = "false"
        api_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY") or "dummy-key"

        client = AsyncOpenAI(
            api_key=api_key,
            base_url=settings.openai_base_url,
            timeout=60.0,
        )

        classifier = LLMIntentClassifier(
            client=client,
            model=settings.openai_model,
            temperature=0.0,
            max_tokens=350,
            raise_on_error=False,
        )
        return classifier

    except Exception as e:
        logger.error(f"Failed to create classifier: {e}")
        raise RuntimeError(f"Classifier init failed: {e}") from e


async def classify_direct_llm(query: str) -> tuple[str, float, str]:
    """Direct LLM classification using Groq API."""
    import json
    import os

    import httpx

    from src.config.settings import settings
    from src.domain.intents import Intent

    try:
        logger.info(f"=== DIRECT_LLM: Starting classification for: {query[:30]}...")
        import sys

        print(f"DEBUG START: Query = {query[:50]}", file=sys.stderr)

        # Use Groq API (configured in .env via settings)
        # Settings reads from .env file
        groq_key = getattr(settings, "groq_api_key", None) or os.environ.get("GROQ_API_KEY")

        if not groq_key:
            logger.warning("=== DIRECT_LLM: No Groq API key found - set GROQ_API_KEY in environment")
            return "unknown", 0.0, "no_api_key"

        base_url = "https://api.groq.com/openai/v1"
        model = "llama-3.3-70b-versatile"

        logger.info(f"=== DIRECT_LLM: Using Groq model: {model}")

        # Build the prompt - clear instructions to return ONLY JSON
        system_prompt = """You are an Islamic QA intent classifier. 
Your task is to classify the user's query into one of these intents:
- fiqh (Islamic jurisprudence)
- quran (Quranic verses/interpretation)
- hadith (Prophetic traditions)
- seerah (Prophet's biography)
- aqeedah (Islamic theology/beliefs)
- islamic_knowledge (general Islamic knowledge)
- islamic_tazkiyah (spiritual purification)

Return ONLY a valid JSON object with no additional text."""
        user_prompt = f"""Classify this query: "{query}"

Return ONLY this JSON (no markdown, no code blocks):
{{"intent": "intent_name", "confidence": 0.0-1.0, "language": "ar or en", "reason": "short explanation"}}

Examples:
- "كيف أصلي؟" → {{"intent": "fiqh", "confidence": 0.95, "language": "ar", "reason": "Asking about prayer details"}}
- "ما هي صفات الله؟" → {{"intent": "aqeedah", "confidence": 0.9, "language": "ar", "reason": "Asking about God's attributes"}}"""

        headers = {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}

        payload = {
            "model": model,
            "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            "temperature": 0.0,
            "max_tokens": 200,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(f"{base_url}/chat/completions", headers=headers, json=payload)

            logger.info(f"=== DIRECT_LLM: Response status: {response.status_code}")

            if response.status_code != 200:
                logger.error(f"=== DIRECT_LLM: API error: {response.text[:500]}")
                return "islamic_knowledge", 0.0, "fallback"

            result = response.json()
            content = result["choices"][0]["message"]["content"]
            logger.info(f"=== DIRECT_LLM: Response content: {content}")
            # Write to stderr for debugging
            import sys

            print(f"DEBUG LLM: {content}", file=sys.stderr)
            logger.info(f"=== DIRECT_LLM: Content type: {type(content)}")

            # Strip markdown code blocks if present (e.g., ```json ... ```)
            content = content.strip()
            if content.startswith("```"):
                # Find the end of the code block
                end_idx = content.find("```", 3)
                if end_idx > 0:
                    content = content[3:end_idx].strip()
                else:
                    content = content[3:].strip()
                # Remove language identifier (e.g., "json")
                if content.startswith("json"):
                    content = content[4:].strip()

            # Try to parse JSON, handle various formats
            parsed = None
            try:
                parsed = json.loads(content)
            except json.JSONDecodeError:
                # Try to extract JSON from the text using regex - more robust

                # Find the first { and last } to get the full JSON object
                start = content.find("{")
                end = content.rfind("}")
                if start >= 0 and end > start:
                    json_str = content[start : end + 1]
                    try:
                        parsed = json.loads(json_str)
                    except (json.JSONDecodeError, ValueError):
                        logger.warning(f"=== DIRECT_LLM: Regex extracted JSON failed: {json_str[:100]}")

                if not parsed:
                    logger.error(f"=== DIRECT_LLM: Failed to parse JSON from: {content[:200]}")
                    return "islamic_knowledge", 0.0, "fallback"

            if parsed is None:
                logger.error(f"=== DIRECT_LLM: No parsed JSON, content: {content[:200]}")
                return "islamic_knowledge", 0.0, "fallback"

            logger.info(f"=== DIRECT_LLM: Full parsed dict: {parsed}")

            intent_str = parsed.get("intent", parsed.get("classification", "islamic_knowledge"))
            raw_confidence = parsed.get("confidence", None)
            logger.info(f"=== DIRECT_LLM: Raw confidence from response: {raw_confidence}, type: {type(raw_confidence)}")

            # Convert confidence - handle string or other types
            if raw_confidence is None:
                confidence = 0.8
            else:
                try:
                    confidence = float(raw_confidence)
                except (TypeError, ValueError):
                    confidence = 0.8

            logger.info(f"=== DIRECT_LLM: Parsed intent_str: {intent_str}, confidence: {confidence}")

            # Validate intent
            valid_intent = True
            try:
                Intent(intent_str)
            except ValueError:
                valid_intent = False
                intent_str = "islamic_knowledge"

            logger.info(
                f"=== DIRECT_LLM: Valid intent: {valid_intent}, final intent: {intent_str}, confidence: {confidence}"
            )

            logger.info(f"=== DIRECT_LLM: Final - intent={intent_str}, confidence={confidence}")

            return intent_str, confidence, "llm"

    except httpx.TimeoutException:
        logger.error("=== DIRECT_LLM: Request timeout")
        return "islamic_knowledge", 0.0, "fallback"
    except Exception as e:
        logger.error(f"=== DIRECT_LLM: Error: {e}", exc_info=True)
        return "islamic_knowledge", 0.0, "fallback"


async def classify_with_llm(
    query: str,
    request: Request,
) -> tuple[str, float, str]:
    """
    Classify query using LLM-based intent classifier.

    Returns:
        Tuple of (intent, confidence, method)
    """
    import time

    start = time.time()

    try:
        logger.info(f"=== CLASSIFY: Starting for query: {query[:30]}...")

        # Use direct LLM classification
        intent, confidence, method = await classify_direct_llm(query)

        elapsed = (time.time() - start) * 1000
        logger.info(
            f"=== CLASSIFY: Result after {elapsed:.0f}ms - intent={intent}, confidence={confidence}, method={method}"
        )

        return intent, confidence, method

    except Exception as e:
        elapsed = (time.time() - start) * 1000
        logger.warning(f"=== CLASSIFY: Failed after {elapsed:.0f}ms with exception: {str(e)[:200]}", exc_info=True)
        return "islamic_knowledge", 0.0, "fallback"


# =============================================================================
# Retrieval and Evaluation
# =============================================================================


async def run_query_evaluation(
    query: str,
    collection: str,
    gold_passages: list[dict],
    request: Request,
    k: int = 5,
) -> QueryEvaluationResult:
    """Run evaluation for a single query."""
    start_time = time.time()

    try:
        # 1. Classify using LLM classifier
        intent, confidence, method = await classify_with_llm(query, request)

        # 2. Get the appropriate collection agent based on collection name
        # Use the registry to get properly initialized agents
        from src.core.registry import get_registry

        registry = get_registry()

        # Map collection name to agent name in registry
        collection_to_agent_name = {
            "seerah_passages": "seerah_agent",
            "spirituality_passages": "tazkiyah_agent",
            "fiqh_passages": "fiqh_agent",
            "hadith_passages": "hadith_agent",
            "quran_tafsir": "tafsir_agent",
            "aqeedah_passages": "aqeedah_agent",
            "general_islamic": "general_islamic_agent",
        }

        agent_name = collection_to_agent_name.get(collection, "general_islamic_agent")
        logger.info(f"=== EVAL: Using agent '{agent_name}' for collection '{collection}'")

        # Get agent from registry
        agent = registry.get_agent(agent_name)
        logger.info(f"=== EVAL: Agent retrieved: {agent}, type: {type(agent)}")

        if not agent:
            logger.warning(f"=== EVAL: Agent '{agent_name}' not found, using fallback")
            return QueryEvaluationResult(
                query=query,
                query_type="",
                detected_intent=intent,
                intent_confidence=confidence,
                intent_method=method,
                collection=collection,
                retrieved_count=0,
                gold_passages_count=len(gold_passages),
                retrieved_ids=[],
                gold_ids=[],
                recall_at_k=0.0,
                precision_at_k=0.0,
                processing_time_ms=int((time.time() - start_time) * 1000),
                error=f"Agent '{agent_name}' not found",
            )
            return QueryEvaluationResult(
                query=query,
                query_type="",
                detected_intent=intent,
                intent_confidence=confidence,
                intent_method=method,
                collection=collection,
                retrieved_count=0,
                gold_passages_count=len(gold_passages),
                retrieved_ids=[],
                gold_ids=[],
                recall_at_k=0.0,
                precision_at_k=0.0,
                processing_time_ms=int((time.time() - start_time) * 1000),
                error=f"Agent '{agent_name}' not found",
            )

        # 3. Run the agent's RAG pipeline directly
        output = await agent.run(query, meta={"language": "ar", "madhhab": "general"})

        # 4. Extract retrieved IDs from output metadata
        retrieved_ids = []
        if hasattr(output, "metadata") and output.metadata:
            retrieved_ids = output.metadata.get("retrieved_ids", [])

        # If not in metadata, try to get from citation_chunks
        if not retrieved_ids and hasattr(output, "citation_chunks"):
            for chunk in output.citation_chunks:
                # Try to extract ID from chunk metadata
                if isinstance(chunk, dict):
                    meta = chunk.get("metadata", {})
                    book_id = meta.get("book_id", "")
                    page = meta.get("page_number", "")
                    if book_id and page:
                        retrieved_ids.append(f"{book_id}_{page}")

        logger.info(f"=== EVAL: Retrieved {len(retrieved_ids)} passages")

        # 5. Extract gold passage IDs (using book_id + page_number as ID)
        gold_ids = []
        for passage in gold_passages:
            book_id = passage.get("book_id", "")
            page = passage.get("page_number", "")
            if book_id and page:
                gold_ids.append(f"{book_id}_{page}")

        # 6. Calculate retrieval metrics
        top_k_retrieved = set(retrieved_ids[:k]) if retrieved_ids else set()
        gold_set = set(gold_ids)

        # Recall@k: how many gold items were retrieved
        if gold_set:
            recall = len(top_k_retrieved & gold_set) / len(gold_set)
        else:
            recall = 1.0 if not gold_ids else 0.0

        # Precision@k: proportion of retrieved that are relevant
        if top_k_retrieved:
            precision = len(top_k_retrieved & gold_set) / k
        else:
            precision = 0.0

        processing_time_ms = int((time.time() - start_time) * 1000)

        # DEBUG: Log what we got from classification
        logger.info(f"=== EVAL: Got from classify_with_llm: intent={intent}, confidence={confidence}, method={method}")

        return QueryEvaluationResult(
            query=query,
            query_type="",  # Will be filled from dataset
            detected_intent=intent,
            intent_confidence=confidence,
            intent_method=method,
            collection=collection,
            retrieved_count=len(retrieved_ids),
            gold_passages_count=len(gold_passages),
            retrieved_ids=retrieved_ids[:k],
            gold_ids=gold_ids,
            recall_at_k=round(recall, 4),
            precision_at_k=round(precision, 4),
            processing_time_ms=processing_time_ms,
            error=None,
        )

    except Exception as e:
        processing_time_ms = int((time.time() - start_time) * 1000)
        logger.error("Query evaluation failed", query=query[:50], error=str(e))
        return QueryEvaluationResult(
            query=query,
            query_type="",
            detected_intent=None,
            intent_confidence=0.0,
            intent_method=None,
            collection=collection,
            retrieved_count=0,
            gold_passages_count=len(gold_passages),
            retrieved_ids=[],
            gold_ids=[],
            recall_at_k=0.0,
            precision_at_k=0.0,
            processing_time_ms=processing_time_ms,
            error=str(e),
        )


# =============================================================================
# Metrics Calculation
# =============================================================================


def calculate_metrics(results: list[QueryEvaluationResult]) -> dict[str, float]:
    """Calculate aggregated metrics from evaluation results."""
    if not results:
        return {
            "mean_recall_at_k": 0.0,
            "mean_precision_at_k": 0.0,
            "success_rate": 0.0,
            "mean_processing_time_ms": 0.0,
        }

    successful = [r for r in results if r.error is None]
    failed = [r for r in results if r.error is not None]

    if successful:
        avg_recall = sum(r.recall_at_k for r in successful) / len(successful)
        avg_precision = sum(r.precision_at_k for r in successful) / len(successful)
        avg_time = sum(r.processing_time_ms for r in successful) / len(successful)
    else:
        avg_recall = 0.0
        avg_precision = 0.0
        avg_time = 0.0

    success_rate = len(successful) / len(results) if results else 0.0

    # Intent classification metrics
    intent_classified = len([r for r in successful if r.detected_intent])
    intent_success_rate = intent_classified / len(successful) if successful else 0.0

    return {
        "mean_recall_at_k": round(avg_recall, 4),
        "mean_precision_at_k": round(avg_precision, 4),
        "success_rate": round(success_rate, 4),
        "failed_count": len(failed),
        "mean_processing_time_ms": round(avg_time, 2),
        "intent_classification_rate": round(intent_success_rate, 4),
    }


# =============================================================================
# Route: POST /evaluate/run
# =============================================================================


@evaluate_router.post(
    "/run",
    response_model=EvaluationRunResponse,
    summary="Run evaluation on a dataset",
    responses={
        400: {"model": dict, "description": "Invalid dataset name"},
        500: {"model": dict, "description": "Evaluation failed"},
    },
)
async def run_evaluation(
    request: Request,
    req: EvaluationRunRequest,
) -> EvaluationRunResponse:
    """
    Run evaluation on a dataset using LLM-based intent classifier.

    This endpoint:
    1. Loads queries from the specified JSONL dataset
    2. Classifies each query using the LLM-based intent classifier
    3. Runs each query through the RAG pipeline
    4. Calculates retrieval metrics (Recall@k, Precision@k)
    5. Returns aggregated results and metrics
    """
    start_time = time.time()

    try:
        # Load dataset
        logger.info("Loading dataset", dataset=req.dataset, limit=req.limit)
        dataset_items = load_dataset(req.dataset, req.limit)

        if not dataset_items:
            raise HTTPException(status_code=400, detail="No items found in dataset")

        # Run evaluation on each query
        results = []
        for i, item in enumerate(dataset_items):
            logger.info(f"Evaluating query {i + 1}/{len(dataset_items)}", query=item.query[:50])
            result = await run_query_evaluation(
                query=item.query,
                collection=item.collection,
                gold_passages=item.gold_passages,
                request=request,
                k=5,
            )
            result.query_type = item.query_type
            results.append(result)

        # Calculate metrics
        metrics = calculate_metrics(results)

        processing_time_ms = int((time.time() - start_time) * 1000)

        successful = len([r for r in results if r.error is None])
        failed = len([r for r in results if r.error is not None])

        logger.info(
            "Evaluation completed",
            dataset=req.dataset,
            total=len(results),
            successful=successful,
            failed=failed,
            processing_time_ms=processing_time_ms,
        )

        return EvaluationRunResponse(
            dataset=req.dataset,
            total_queries=len(results),
            successful=successful,
            failed=failed,
            results=results,
            metrics=metrics,
            processing_time_ms=processing_time_ms,
        )

    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error("Evaluation failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}") from e


# =============================================================================
# Route: GET /evaluate/datasets
# =============================================================================


@evaluate_router.get("/datasets")
async def list_datasets() -> dict:
    """
    List available evaluation datasets.
    """
    base_path = Path(__file__).parent.parent.parent / "evaluation"
    datasets = []

    for file_path in base_path.glob("*.jsonl"):
        dataset_name = file_path.stem.replace("_real_user_eval", "")
        # Count lines in file
        with open(file_path, encoding="utf-8") as f:
            line_count = sum(1 for _ in f)
        datasets.append(
            {
                "name": dataset_name,
                "file": file_path.name,
                "item_count": line_count,
            }
        )

    return {"datasets": datasets}
