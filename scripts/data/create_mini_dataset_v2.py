#!/usr/bin/env python3
"""
Create Mini Dataset from Lucene Pages Collections - FAST VERSION

Extracts first N samples from each collection in data/processed/lucene_pages/collections/
and saves them to data/mini_dataset_v2/

Each collection will have up to 10,000 sample records.
"""

import json
import shutil
from pathlib import Path


# Configuration
SOURCE_DIR = Path("data/processed/lucene_pages/collections")
OUTPUT_DIR = Path("data/mini_dataset_v2")
SAMPLES_PER_COLLECTION = 10000


def extract_first_n(source_path: Path, output_path: Path, n: int) -> int:
    """Extract first n lines from source and save to output."""

    output_path.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    with open(source_path, encoding="utf-8") as f_in, open(output_path, "w", encoding="utf-8") as f_out:
        for line in f_in:
            if count >= n:
                break
            f_out.write(line)
            count += 1

    return count


def main():
    """Main function to create mini dataset."""

    print("=" * 60)
    print("Creating Mini Dataset from Lucene Pages Collections")
    print("=" * 60)

    # Create output directory
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Get list of source files
    source_files = sorted(SOURCE_DIR.glob("*.jsonl"))

    if not source_files:
        print("No JSONL files found in %s" % SOURCE_DIR)
        return

    print("\nFound %d collections" % len(source_files))
    print("Extracting first %d records from each\n" % SAMPLES_PER_COLLECTION)

    # Process each collection
    total_records = 0
    stats = []

    for file_path in source_files:
        name = file_path.stem
        print("Processing: %s..." % name, end=" ", flush=True)

        # Extract samples
        output_path = OUTPUT_DIR / file_path.name
        sampled = extract_first_n(file_path, output_path, SAMPLES_PER_COLLECTION)

        print("%d records" % sampled)

        stats.append(
            {
                "collection": name,
                "sampled": sampled,
            }
        )

        total_records += sampled

    # Save stats
    stats_file = OUTPUT_DIR / "stats.json"
    with open(stats_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "total_records": total_records,
                "samples_per_collection": SAMPLES_PER_COLLECTION,
                "collections": stats,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    print("\n" + "=" * 60)
    print("Complete! Created %d collections" % len(source_files))
    print("Total records: %d" % total_records)
    print("Output: %s" % OUTPUT_DIR)
    print("=" * 60)


if __name__ == "__main__":
    main()
