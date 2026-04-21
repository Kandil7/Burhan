"""
Evaluation CLI for Athar RAG System.

Provides command-line interface to run evaluations on golden sets.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from src.evaluation.golden_set_schema import get_fiqh_golden_set, load_golden_set
from src.evaluation.metrics import run_evaluation


def load_agent(agent_name: str):
    """
    Load an agent by name.

    Args:
        agent_name: Name of the agent (e.g., 'fiqh', 'aqeedah', 'tafsir').

    Returns:
        Agent instance.
    """
    # Import from v2 collection agents
    from src.agents.collection import (
        AqeedahCollectionAgent,
        FiqhCollectionAgent,
        HadithCollectionAgent,
        TafsirCollectionAgent,
    )

    agent_map = {
        "fiqh": FiqhCollectionAgent,
        "hadith": HadithCollectionAgent,
        "tafsir": TafsirCollectionAgent,
        "aqeedah": AqeedahCollectionAgent,
    }

    agent_class = agent_map.get(agent_name)
    if agent_class:
        return agent_class()

    return None


async def run_cli(args):
    """
    Run evaluation from CLI arguments.

    Args:
        args: Parsed command-line arguments.
    """
    # Load golden set
    if args.golden_set:
        golden_set_path = Path(args.golden_set)
        if golden_set_path.exists():
            golden_set = load_golden_set(str(golden_set_path))
            print(f"Loaded golden set from {args.golden_set}: {len(golden_set)} items")
        else:
            print(f"Error: Golden set file not found: {args.golden_set}", file=sys.stderr)
            sys.exit(1)
    else:
        # Default to Fiqh golden set
        golden_set = get_fiqh_golden_set()
        print(f"Using default Fiqh golden set: {len(golden_set)} items")

    # Load agent
    agent = load_agent(args.agent)
    if agent is None:
        print(f"Error: Agent '{args.agent}' not found", file=sys.stderr)
        sys.exit(1)

    print(f"Running evaluation with agent: {args.agent}")
    print("-" * 60)

    # Run evaluation
    result = await run_evaluation(agent, golden_set, k=args.k)

    # Output results
    if args.output:
        output_path = Path(args.output)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)
        print(f"Results saved to: {args.output}")
    else:
        print(result)

    return result


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Run evaluation on Athar RAG system golden sets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.evaluation.cli --agent fiqh
  python -m src.evaluation.cli --agent fiqh --golden-set data/golden_set.json
  python -m src.evaluation.cli --agent fiqh --k 10 --output results.json
        """,
    )

    parser.add_argument(
        "--agent", type=str, required=True, help="Agent to evaluate (e.g., 'fiqh', 'aqeedah', 'tafsir', 'hadith')"
    )

    parser.add_argument(
        "--golden-set", type=str, default=None, help="Path to golden set JSON file (default: built-in Fiqh golden set)"
    )

    parser.add_argument("--k", type=int, default=5, help="Number of top retrieval results to consider (default: 5)")

    parser.add_argument("--output", type=str, default=None, help="Path to save results JSON file")

    args = parser.parse_args()

    # Run async evaluation
    asyncio.run(run_cli(args))


if __name__ == "__main__":
    main()
