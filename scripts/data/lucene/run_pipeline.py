#!/usr/bin/env python3
"""
Run the complete Lucene extraction pipeline.

Orchestrates all four steps:
  A. Extract Lucene indexes
  B. Decode/clean content
  C. Merge with master catalog
  D. Verify quality

Usage:
    python scripts/data/lucene/run_pipeline.py
    python scripts/data/lucene/run_pipeline.py --step C
    python scripts/data/lucene/run_pipeline.py --steps A B
    python scripts/data/lucene/run_pipeline.py --dry-run
    python scripts/data/lucene/run_pipeline.py --resume
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional

from scripts.utils import (
    format_duration,
    get_project_root,
    setup_script_logger,
)

logger = setup_script_logger("lucene_pipeline")

PROJECT_ROOT = get_project_root()
SCRIPTS_DIR = PROJECT_ROOT / "scripts" / "data" / "lucene"

STEPS = {
    "A": {
        "name": "Extract Lucene indexes",
        "script": "extract_lucene_pages.py",
        "description": "Extract pages, titles, esnad, books from Lucene",
    },
    "B": {
        "name": "Decode & clean content",
        "script": "decode_lucene_content.py",
        "description": "Fix encoding, clean HTML, normalise Arabic",
    },
    "C": {
        "name": "Merge with master catalog",
        "script": "merge_lucene_with_master.py",
        "description": "Enrich with metadata, create collections",
    },
    "D": {
        "name": "Verify quality",
        "script": "verify_lucene_extraction.py",
        "description": "Check coverage, encoding, hierarchy",
    },
}


def run_step(step_id: str, dry_run: bool = False, resume: bool = False) -> bool:
    """
    Run a single pipeline step.

    Args:
        step_id: Step identifier (A, B, C, D).
        dry_run: If True, show command without running.
        resume: If True, add --resume flag.

    Returns:
        True if step succeeded.
    """
    step = STEPS.get(step_id)
    if not step:
        logger.error(f"Unknown step: {step_id}")
        return False

    script_path = SCRIPTS_DIR / step["script"]
    if not script_path.exists():
        logger.error(f"Script not found: {script_path}")
        return False

    cmd = [sys.executable, str(script_path)]
    if resume and step_id in ("A",):
        cmd.append("--resume")
    if dry_run:
        cmd.append("--dry-run")

    logger.info(f"{'=' * 60}")
    logger.info(f"Step {step_id}: {step['name']}")
    logger.info(f"  {step['description']}")
    logger.info(f"  Command: {' '.join(cmd)}")
    logger.info(f"{'=' * 60}")

    if dry_run:
        logger.info(f"DRY RUN: Would execute: {' '.join(cmd)}")
        return True

    start = time.time()
    result = subprocess.run(cmd, timeout=None)  # No timeout for long steps
    duration = time.time() - start

    if result.returncode != 0:
        logger.error(f"Step {step_id} FAILED after {format_duration(duration)}")
        return False

    logger.info(f"Step {step_id} completed in {format_duration(duration)}")
    return True


def main():
    """Main pipeline runner."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Run complete Lucene extraction pipeline"
    )
    parser.add_argument(
        "--step",
        choices=list(STEPS.keys()),
        help="Run a single step",
    )
    parser.add_argument(
        "--steps",
        nargs="+",
        choices=list(STEPS.keys()),
        help="Run specific steps in order",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show commands without executing",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from last checkpoint",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("Burhan - LUCENE EXTRACTION PIPELINE")
    print("=" * 70)

    # Determine steps to run
    if args.step:
        steps_to_run = [args.step]
    elif args.steps:
        steps_to_run = args.steps
    else:
        steps_to_run = list(STEPS.keys())

    print(f"Steps to run: {' -> '.join(steps_to_run)}")
    print(f"Dry run: {args.dry_run}")
    print(f"Resume: {args.resume}")
    print("=" * 70)

    overall_start = time.time()
    all_passed = True

    for step_id in steps_to_run:
        success = run_step(step_id, dry_run=args.dry_run, resume=args.resume)
        if not success:
            all_passed = False
            logger.error(f"Pipeline stopped at step {step_id}")
            break

    total_duration = time.time() - overall_start

    print(f"\n{'=' * 70}")
    if all_passed:
        print(f"PIPELINE COMPLETE - All {len(steps_to_run)} steps passed")
    else:
        print(f"PIPELINE FAILED - Stopped during execution")
    print(f"Total duration: {format_duration(total_duration)}")
    print(f"{'=' * 70}")

    if not all_passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
