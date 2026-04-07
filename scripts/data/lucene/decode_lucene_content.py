#!/usr/bin/env python3
"""
B. Decode and clean Lucene-extracted content.

Fixes encoding issues (mojibake), cleans HTML tags, normalises Arabic
text, and validates the output. Can be run as a standalone utility on
any JSON/JSONL file, or as a pipeline stage after extraction.

Usage:
    # Fix a single file
    python scripts/data/lucene/decode_lucene_content.py \
        --input data/processed/lucene_pages/raw/page_batch_1.jsonl \
        --output data/processed/lucene_pages/pages/cleaned/

    # Fix all files in a directory
    python scripts/data/lucene/decode_lucene_content.py \
        --input data/processed/lucene_pages/raw/ \
        --output data/processed/lucene_pages/cleaned/ \
        --recursive

    # Validate encoding of existing files
    python scripts/data/lucene/decode_lucene_content.py \
        --validate data/processed/lucene_pages/pages/

    # Show encoding diagnostics
    python scripts/data/lucene/decode_lucene_content.py \
        --diagnose data/processed/lucene_pages/raw/page_batch_1.jsonl
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from scripts.utils import (
    ensure_dir,
    format_size,
    get_project_root,
    setup_script_logger,
)

# -- Configuration --

logger = setup_script_logger("decode_lucene_content")

PROJECT_ROOT = get_project_root()

# Arabic Unicode ranges
ARABIC_RANGE = (0x0600, 0x06FF)
ARABIC_SUPPLEMENT = (0x0750, 0x077F)
ARABIC_EXTENDED_A = (0x08A0, 0x08FF)
ARABIC_PRESENTATION_A = (0xFB50, 0xFDFF)
ARABIC_PRESENTATION_B = (0xFE70, 0xFEFF)


# -- Data Classes --

@dataclass
class DecodeResult:
    """Result of decoding a single document."""
    success: bool
    original_arabic_chars: int = 0
    decoded_arabic_chars: int = 0
    encoding_detected: str = "utf-8"
    fields_processed: int = 0
    fields_fixed: int = 0
    error_message: Optional[str] = None


@dataclass
class FileDecodeStats:
    """Statistics for decoding a file."""
    file_path: str
    total_docs: int = 0
    decoded_docs: int = 0
    error_docs: int = 0
    mojibake_fixed: int = 0
    html_tags_removed: int = 0
    total_arabic_chars: int = 0
    input_size_bytes: int = 0
    output_size_bytes: int = 0
    encoding_issues: List[str] = field(default_factory=list)


# -- Decoding Functions --

def is_arabic_char(ch: str) -> bool:
    """Check if a character is Arabic."""
    cp = ord(ch)
    return (
        ARABIC_RANGE[0] <= cp <= ARABIC_RANGE[1]
        or ARABIC_SUPPLEMENT[0] <= cp <= ARABIC_SUPPLEMENT[1]
        or ARABIC_EXTENDED_A[0] <= cp <= ARABIC_EXTENDED_A[1]
    )


def count_arabic_chars(text: str) -> int:
    """Count Arabic characters in text."""
    return sum(1 for c in text if is_arabic_char(c))


def decode_mojibake_text(text: str) -> Tuple[str, str]:
    """
    Attempt to decode mojibake text.

    Tries multiple strategies and returns the one with the most Arabic chars.

    Returns:
        (decoded_text, encoding_used)
    """
    if not text:
        return text, "empty"

    original_arabic = count_arabic_chars(text)

    # Strategy 1: Already valid UTF-8 Arabic
    if original_arabic > len(text) * 0.2:
        return text, "utf-8"

    # Strategy 2: UTF-8 bytes -> Windows-1256
    try:
        raw_bytes = text.encode("utf-8")
        decoded = raw_bytes.decode("windows-1256")
        decoded_arabic = count_arabic_chars(decoded)
        if decoded_arabic > original_arabic * 1.5:
            return decoded, "utf8->cp1256"
    except (UnicodeDecodeError, UnicodeEncodeError):
        pass

    # Strategy 3: UTF-8 bytes -> Latin-1 -> Windows-1256
    try:
        raw_bytes = text.encode("utf-8")
        latin1 = raw_bytes.decode("latin-1")
        decoded = latin1.encode("latin-1").decode("windows-1256")
        decoded_arabic = count_arabic_chars(decoded)
        if decoded_arabic > original_arabic * 1.5:
            return decoded, "utf8->latin1->cp1256"
    except (UnicodeDecodeError, UnicodeEncodeError):
        pass

    return text, "utf-8 (unchanged)"


def clean_html_tags(text: str) -> Tuple[str, int]:
    """
    Remove HTML/XML tags from text.

    Returns:
        (cleaned_text, tags_removed_count)
    """
    if not text:
        return text, 0

    tags = re.findall(r"<[^>]+>", text)
    tag_count = len(tags)
    cleaned = re.sub(r"<[^>]+>", "", text)

    return cleaned, tag_count


def normalise_arabic_text(text: str) -> str:
    """
    Normalise Arabic text for consistency.

    - Remove zero-width characters
    - Collapse whitespace
    - Trim
    """
    if not text:
        return text

    # Remove zero-width chars and BOM
    text = text.replace("\u200c", "").replace("\u200d", "").replace("\ufeff", "")
    text = text.replace("\u200b", "")

    # Collapse horizontal whitespace (preserve newlines)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def decode_document(doc: Dict[str, Any]) -> Tuple[Dict[str, Any], DecodeResult]:
    """
    Decode and clean all text fields in a document.

    Args:
        doc: Raw document from Lucene extraction.

    Returns:
        (cleaned_document, decode_result)
    """
    result = DecodeResult(success=True)
    cleaned: Dict[str, Any] = {}

    for key, value in doc.items():
        if not isinstance(value, str):
            cleaned[key] = value
            continue

        result.fields_processed += 1

        # Decode mojibake
        decoded, encoding = decode_mojibake_text(value)
        if encoding != "utf-8" and encoding != "empty":
            result.fields_fixed += 1
            result.encoding_detected = encoding

        # Count Arabic chars
        arabic = count_arabic_chars(decoded)
        result.original_arabic_chars += arabic

        # Clean HTML tags
        decoded, tags_removed = clean_html_tags(decoded)

        # Normalise
        decoded = normalise_arabic_text(decoded)

        result.total_arabic_chars += count_arabic_chars(decoded)
        cleaned[key] = decoded

    return cleaned, result


# -- File Processing --

def process_jsonl_file(
    input_path: Path,
    output_path: Path,
    validate_only: bool = False,
) -> FileDecodeStats:
    """
    Process a single JSONL file: decode, clean, validate.

    Args:
        input_path: Path to input JSONL file.
        output_path: Path to output cleaned JSONL file.
        validate_only: If True, only validate without writing output.

    Returns:
        FileDecodeStats with processing results.
    """
    stats = FileDecodeStats(
        file_path=str(input_path),
        input_size_bytes=input_path.stat().st_size if input_path.exists() else 0,
    )

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return stats

    output_fh = None
    if not validate_only:
        ensure_dir(output_path.parent)
        output_fh = open(output_path, "w", encoding="utf-8")

    try:
        with open(input_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    doc = json.loads(line)
                    cleaned, result = decode_document(doc)

                    stats.total_docs += 1
                    if result.fields_fixed > 0:
                        stats.mojibake_fixed += 1
                    stats.total_arabic_chars += result.total_arabic_chars

                    if output_fh and not validate_only:
                        output_fh.write(
                            json.dumps(cleaned, ensure_ascii=False) + "\n"
                        )

                except json.JSONDecodeError as e:
                    stats.error_docs += 1
                    stats.encoding_issues.append(
                        f"Line {line_num}: JSON parse error: {e}"
                    )
                except Exception as e:
                    stats.error_docs += 1
                    stats.encoding_issues.append(
                        f"Line {line_num}: {type(e).__name__}: {e}"
                    )

                # Progress
                if line_num % 10000 == 0:
                    logger.info(
                        f"  {line_num:,} docs processed, "
                        f"{stats.mojibake_fixed} fixed, "
                        f"{stats.error_docs} errors"
                    )

    finally:
        if output_fh:
            output_fh.close()

    if output_path.exists():
        stats.output_size_bytes = output_path.stat().st_size

    return stats


def process_directory(
    input_dir: Path,
    output_dir: Path,
    pattern: str = "*.jsonl",
    recursive: bool = False,
    validate_only: bool = False,
) -> List[FileDecodeStats]:
    """
    Process all matching files in a directory.
    """
    all_stats: List[FileDecodeStats] = []

    if recursive:
        files = list(input_dir.rglob(pattern))
    else:
        files = list(input_dir.glob(pattern))

    logger.info(f"Found {len(files)} files matching '{pattern}' in {input_dir}")

    for input_file in sorted(files):
        if validate_only:
            output_file = input_file
        else:
            rel_path = input_file.relative_to(input_dir)
            output_file = output_dir / rel_path

        logger.info(f"Processing: {input_file.name}")
        file_stats = process_jsonl_file(input_file, output_file, validate_only)
        all_stats.append(file_stats)

    return all_stats


# -- Validation & Diagnostics --

def validate_encoding(file_path: Path) -> Dict[str, Any]:
    """
    Validate encoding of a file.
    """
    report: Dict[str, Any] = {
        "file": str(file_path),
        "size_bytes": file_path.stat().st_size,
        "valid_utf8": True,
        "encoding_issues": [],
        "arabic_ratio": 0.0,
        "mojibake_detected": False,
        "control_chars": 0,
        "sample_texts": [],
    }

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError as e:
        report["valid_utf8"] = False
        report["encoding_issues"].append(f"UTF-8 decode error: {e}")
        return report

    # Check for mojibake patterns
    mojibake_patterns = [
        "\u00d8\u00a7",
        "\u00d9\u0086",
        "\u00d8\u00b1",
    ]
    for pattern in mojibake_patterns:
        if pattern in content:
            report["mojibake_detected"] = True
            report["encoding_issues"].append(
                f"Mojibake pattern detected: {repr(pattern)}"
            )

    total_chars = len(content)
    arabic_chars = count_arabic_chars(content)
    control_chars = sum(1 for c in content if ord(c) < 32 and c not in "\n\r\t")

    report["arabic_ratio"] = arabic_chars / total_chars if total_chars > 0 else 0
    report["control_chars"] = control_chars

    if control_chars > 100:
        report["encoding_issues"].append(
            f"High control character count: {control_chars}"
        )

    if arabic_chars > 0:
        for i, ch in enumerate(content):
            if is_arabic_char(ch):
                report["sample_texts"].append(content[i:i+100])
                break

    return report


def diagnose_file(file_path: Path) -> None:
    """Print detailed encoding diagnostics for a file."""
    print(f"\n{'=' * 60}")
    print(f"Encoding diagnosis: {file_path}")
    print(f"{'=' * 60}")

    report = validate_encoding(file_path)

    print(f"  File size:        {format_size(report['size_bytes'])}")
    print(f"  Valid UTF-8:      {report['valid_utf8']}")
    print(f"  Arabic ratio:     {report['arabic_ratio']:.2%}")
    print(f"  Mojibake:         {report['mojibake_detected']}")
    print(f"  Control chars:    {report['control_chars']}")

    if report["encoding_issues"]:
        print(f"\n  Issues:")
        for issue in report["encoding_issues"]:
            print(f"    - {issue}")
    else:
        print(f"\n  No encoding issues detected")

    if report["sample_texts"]:
        print(f"\n  Sample text:")
        for sample in report["sample_texts"][:3]:
            print(f"    {sample}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i >= 3:
                    break
                line = line.strip()
                if not line:
                    continue
                doc = json.loads(line)
                print(f"\n  Document {i + 1} keys: {list(doc.keys())}")
                for key in ["body", "book", "author"]:
                    if key in doc:
                        text = doc[key][:100]
                        arabic = count_arabic_chars(text)
                        print(f"    {key}: {text}... ({arabic} Arabic chars)")
    except Exception as e:
        print(f"\n  Error reading documents: {e}")


# -- Summary --

def print_decode_summary(all_stats: List[FileDecodeStats]) -> None:
    """Print summary of decode operation."""
    total_docs = sum(s.total_docs for s in all_stats)
    total_errors = sum(s.error_docs for s in all_stats)
    total_fixed = sum(s.mojibake_fixed for s in all_stats)
    total_arabic = sum(s.total_arabic_chars for s in all_stats)
    total_input = sum(s.input_size_bytes for s in all_stats)
    total_output = sum(s.output_size_bytes for s in all_stats)

    print(f"\n{'=' * 60}")
    print("DECODE/CLEAN SUMMARY")
    print(f"{'=' * 60}")
    print(f"  Files processed:    {len(all_stats)}")
    print(f"  Total documents:    {total_docs:,}")
    print(f"  Errors:             {total_errors:,}")
    print(f"  Mojibake fixed:     {total_fixed:,}")
    print(f"  Arabic characters:  {total_arabic:,}")
    print(f"  Input size:         {format_size(total_input)}")
    print(f"  Output size:        {format_size(total_output)}")

    if total_errors > 0:
        print(f"\n  Files with issues:")
        for s in all_stats:
            if s.error_docs > 0 or s.encoding_issues:
                print(f"    {s.file_path}: {s.error_docs} errors")

    print(f"{'=' * 60}")


# -- Main --

def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Decode and clean Lucene-extracted content"
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--input",
        type=Path,
        help="Input file or directory to process",
    )
    group.add_argument(
        "--validate",
        type=Path,
        help="Validate encoding of file/directory (read-only)",
    )
    group.add_argument(
        "--diagnose",
        type=Path,
        help="Show detailed encoding diagnostics for a file",
    )

    parser.add_argument(
        "--output",
        type=Path,
        help="Output file or directory (default: input_cleaned/)",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Process directories recursively",
    )
    parser.add_argument(
        "--pattern",
        default="*.jsonl",
        help="File glob pattern (default: *.jsonl)",
    )

    args = parser.parse_args()

    # Diagnose mode
    if args.diagnose:
        if args.diagnose.is_file():
            diagnose_file(args.diagnose)
        else:
            for f in sorted(args.diagnose.glob("*.jsonl"))[:5]:
                diagnose_file(f)
        return

    # Validate mode
    if args.validate:
        if args.validate.is_file():
            report = validate_encoding(args.validate)
            print(json.dumps(report, indent=2, ensure_ascii=False))
        else:
            all_reports = []
            for f in sorted(args.validate.rglob(args.pattern)):
                report = validate_encoding(f)
                all_reports.append(report)
                if report["encoding_issues"] or report["mojibake_detected"]:
                    print(f"ISSUES: {f}")
                    for issue in report["encoding_issues"]:
                        print(f"  - {issue}")
            valid = sum(1 for r in all_reports if not r["encoding_issues"])
            print(f"\nValid files: {valid}/{len(all_reports)}")
        return

    # Process mode
    input_path = args.input
    output_path = args.output

    if input_path.is_file():
        if output_path is None or output_path.is_dir():
            output_path = (output_path or input_path.parent / "cleaned") / input_path.name
        logger.info(f"Processing file: {input_path} -> {output_path}")
        stats = process_jsonl_file(input_path, output_path)
        print_decode_summary([stats])
    elif input_path.is_dir():
        if output_path is None:
            output_path = input_path.parent / f"{input_path.name}_cleaned"
        logger.info(f"Processing directory: {input_path} -> {output_path}")
        all_stats = process_directory(
            input_path, output_path,
            pattern=args.pattern,
            recursive=args.recursive,
        )
        print_decode_summary(all_stats)
    else:
        logger.error(f"Input path not found: {input_path}")
        sys.exit(1)


if __name__ == "__main__":
    main()
