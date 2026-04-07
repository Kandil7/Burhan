#!/usr/bin/env python3
"""
Sanadset Hadith Agent Test Script.

Tests the SanadsetHadithAgent with sample queries to verify:
- Agent initialization (embedding model, vector store, LLM)
- Hadith retrieval from Qdrant
- Response generation with citations
- Error handling

Usage:
    python scripts/tests/test_sanadset_agent.py
    python scripts/tests/test_sanadset_agent.py --query "صلاة الجمعة"
    python scripts/tests/test_sanadset_agent.py --verbose

Author: Athar Engineering Team
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.utils import (
    setup_script_logger,
    add_project_root_to_path,
)

add_project_root_to_path()

from src.agents.sanadset_hadith_agent import SanadsetHadithAgent
from src.agents.base import AgentInput

logger = setup_script_logger("test-sanadset-agent")

# ── Test Queries ─────────────────────────────────────────────────────────

TEST_QUERIES = [
    ("صلاة الجمعة", "Friday prayer ruling"),
    ("الوضوء", "Ablution"),
    ("الزكاة", "Zakat"),
    ("الصيام", "Fasting"),
    ("الحج", "Hajj"),
]


# ── Terminal Colors ──────────────────────────────────────────────────────


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    END = "\033[0m"


# ── Test Functions ───────────────────────────────────────────────────────


async def test_agent_initialization(agent: SanadsetHadithAgent, verbose: bool = False) -> bool:
    """
    Test agent initialization.

    Args:
        agent: SanadsetHadithAgent instance.
        verbose: Show detailed output.

    Returns:
        True if initialization succeeded.
    """
    print(f"\n{Colors.CYAN}{'─' * 60}{Colors.END}")
    print(f"{Colors.BOLD}Testing Agent Initialization{Colors.END}")
    print(f"{'─' * 60}")

    try:
        await agent.initialize()

        checks = {
            "Initialized": agent._initialized,
            "Embedding model": agent.embedding_model is not None,
            "Vector store": agent.vector_store is not None,
            "LLM available": agent._llm_available,
            "Hybrid searcher": agent.hybrid_searcher is not None,
        }

        all_passed = True
        for name, value in checks.items():
            icon = f"{Colors.GREEN}✓{Colors.END}" if value else f"{Colors.YELLOW}⚠{Colors.END}"
            print(f"  {icon} {name}: {value}")
            if not value and name in ("Embedding model", "Vector store"):
                all_passed = False

        return all_passed

    except Exception as e:
        print(f"  {Colors.RED}✗ Initialization failed: {e}{Colors.END}")
        logger.error("init_failed", error=str(e), exc_info=True)
        return False


async def test_query(
    agent: SanadsetHadithAgent,
    query: str,
    description: str = "",
    verbose: bool = False,
) -> bool:
    """
    Test a single query against the agent.

    Args:
        agent: SanadsetHadithAgent instance.
        query: Arabic query text.
        description: Human-readable description.
        verbose: Show detailed output.

    Returns:
        True if query returned results.
    """
    label = f"Query: {query}"
    if description:
        label += f" ({description})"

    print(f"\n{Colors.CYAN}{'─' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{label}{Colors.END}")
    print(f"{'─' * 60}")

    try:
        result = await agent.execute(AgentInput(query=query, language="ar"))

        # Show answer preview
        answer_preview = result.answer[:200] + "..." if len(result.answer) > 200 else result.answer
        print(f"  {Colors.BLUE}Answer:{Colors.END}")
        print(f"    {answer_preview}")

        # Show confidence
        print(f"  {Colors.BLUE}Confidence:{Colors.END} {result.confidence:.2f}")

        # Show retrieval stats
        meta = result.metadata
        retrieved = meta.get("retrieved_count", 0)
        used = meta.get("used_count", 0)
        scores = meta.get("scores", [])

        print(f"  {Colors.BLUE}Retrieval:{Colors.END} {retrieved} retrieved, {used} used")

        if scores:
            print(f"  {Colors.BLUE}Top scores:{Colors.END} {scores[:3]}")

        if result.citations:
            print(f"  {Colors.BLUE}Citations:{Colors.END} {len(result.citations)}")

        # Determine success
        if retrieved > 0:
            print(f"\n  {Colors.GREEN}✓ Retrieval working!{Colors.END}")
            return True
        else:
            print(f"\n  {Colors.YELLOW}⚠ No passages retrieved (collection may be empty){Colors.END}")
            return False

    except Exception as e:
        print(f"  {Colors.RED}✗ Error: {e}{Colors.END}")
        logger.error("query_error", query=query, error=str(e), exc_info=True)
        return False


async def run_all_tests(
    queries: Optional[list[tuple[str, str]]] = None,
    verbose: bool = False,
) -> dict:
    """
    Run all agent tests.

    Args:
        queries: List of (query, description) tuples.
        verbose: Show detailed output.

    Returns:
        Stats dict with test results.
    """
    test_queries = queries or TEST_QUERIES

    print(f"\n{'=' * 60}")
    print(f"  {Colors.BOLD}TESTING SANADSET HADITH AGENT{Colors.END}")
    print(f"{'=' * 60}")

    # Initialize agent
    agent = SanadsetHadithAgent()

    # Test initialization
    init_ok = await test_agent_initialization(agent, verbose)

    if not init_ok:
        print(f"\n  {Colors.RED}✗ Agent initialization failed. Cannot run queries.{Colors.END}")
        return {"init_ok": False, "queries_tested": 0, "queries_passed": 0}

    # Test queries
    queries_tested = 0
    queries_passed = 0

    for query, description in test_queries:
        queries_tested += 1
        if await test_query(agent, query, description, verbose):
            queries_passed += 1

    # Summary
    print(f"\n{'=' * 60}")
    print(f"  {Colors.BOLD}TEST SUMMARY{Colors.END}")
    print(f"{'=' * 60}")
    print(f"  Initialization: {f'{Colors.GREEN}✓{Colors.END}' if init_ok else f'{Colors.RED}✗{Colors.END}'}")
    print(f"  Queries tested: {queries_tested}")
    print(f"  Queries passed: {queries_passed}")
    print(f"  Queries failed: {queries_tested - queries_passed}")
    print(f"{'=' * 60}\n")

    return {
        "init_ok": init_ok,
        "queries_tested": queries_tested,
        "queries_passed": queries_passed,
        "queries_failed": queries_tested - queries_passed,
    }


# ── Main ─────────────────────────────────────────────────────────────────


def main():
    """Run Sanadset agent tests."""
    parser = argparse.ArgumentParser(
        description="Test Sanadset Hadith Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/tests/test_sanadset_agent.py
  python scripts/tests/test_sanadset_agent.py --query "صلاة الجمعة"
  python scripts/tests/test_sanadset_agent.py --verbose
        """,
    )
    parser.add_argument("--query", type=str, default=None, help="Single query to test")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    args = parser.parse_args()

    # Build query list
    queries: Optional[list[tuple[str, str]]] = None
    if args.query:
        queries = [(args.query, "Custom query")]

    try:
        stats = asyncio.run(run_all_tests(queries=queries, verbose=args.verbose))

        if stats["queries_failed"] > 0:
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n  Interrupted by user.")
        sys.exit(1)
    except Exception as e:
        logger.error("fatal_error", error=str(e), exc_info=True)
        print(f"\n{Colors.RED}Fatal error: {e}{Colors.END}")
        sys.exit(1)


if __name__ == "__main__":
    main()
