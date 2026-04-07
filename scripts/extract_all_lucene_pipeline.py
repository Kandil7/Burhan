#!/usr/bin/env python3
"""
Full Lucene extraction pipeline.

Extracts ALL Lucene indexes from Shamela system_book_datasets.

Usage:
    python scripts/extract_all_lucene_pipeline.py              # Full extraction (3-5 hours)
    python scripts/extract_all_lucene_pipeline.py --quick      # Quick test (15 minutes)
    python scripts/extract_all_lucene_pipeline.py --index page # Extract only page index
"""
import subprocess
import sys
import os
from pathlib import Path
from typing import List, Dict, Tuple
import time

# Configuration
BASE_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = BASE_DIR / "scripts"
STORE_DIR = BASE_DIR / "datasets" / "system_book_datasets" / "store"
OUTPUT_DIR = BASE_DIR / "data" / "processed"

LUCENE_CORE = BASE_DIR / "lib" / "lucene" / "lucene-core-9.12.0.jar"
LUCENE_CODECS = BASE_DIR / "lib" / "lucene" / "lucene-backward-codecs-9.12.0.jar"

CLASSPATH = f".;{LUCENE_CORE};{LUCENE_CODECS}"

# All available indexes with estimated doc counts
ALL_INDEXES = {
    "esnad": {"name": "Hadith Chains", "estimated_docs": 35_526, "time": "5 min"},
    "author": {"name": "Author Biographies", "estimated_docs": 3_000, "time": "5 min"},
    "book": {"name": "Book Index", "estimated_docs": 8_400, "time": "10 min"},
    "title": {"name": "Chapters/Sections", "estimated_docs": 3_914_618, "time": "30-60 min"},
    "page": {"name": "Full Arabic Text", "estimated_docs": 7_300_000, "time": "2-4 hours"},
    "aya": {"name": "Quran Verses", "estimated_docs": 6_236, "time": "5 min"},
    "s_author": {"name": "Search Author", "estimated_docs": 3_000, "time": "5 min"},
    "s_book": {"name": "Search Book", "estimated_docs": 8_400, "time": "10 min"},
}

def compile_extractor() -> bool:
    """Compile LuceneExtractor.java if needed."""
    java_file = SCRIPTS_DIR / "LuceneExtractor.java"
    class_file = SCRIPTS_DIR / "LuceneExtractor.class"
    
    # Check if compilation needed
    if class_file.exists():
        if java_file.exists():
            if class_file.stat().st_mtime > java_file.stat().st_mtime:
                print("  ✓ Already compiled")
                return True
    
    if not java_file.exists():
        print("  ✗ LuceneExtractor.java not found")
        return False
    
    print("  Compiling LuceneExtractor.java...")
    result = subprocess.run(
        ["javac", "-cp", CLASSPATH, "-encoding", "UTF-8", str(java_file)],
        capture_output=True,
        text=True,
        cwd=str(SCRIPTS_DIR)
    )
    
    if result.returncode != 0:
        print(f"  ✗ Compilation failed:")
        print(result.stderr)
        return False
    
    print("  ✓ Compilation successful")
    return True


def extract_index(index_name: str, max_docs: int = -1) -> Tuple[bool, int]:
    """
    Extract a single Lucene index.
    
    Returns:
        (success, doc_count)
    """
    index_path = STORE_DIR / index_name
    output_file = OUTPUT_DIR / f"lucene_{index_name}.json"
    
    if not index_path.exists():
        print(f"  ✗ Index not found: {index_path}")
        return False, 0
    
    print(f"\n{'='*70}")
    print(f"  📚 Extracting: {index_name} - {ALL_INDEXES.get(index_name, {}).get('name', 'Unknown')}")
    print(f"{'='*70}")
    print(f"  Index: {index_path}")
    print(f"  Output: {output_file}")
    print(f"  Max docs: {max_docs if max_docs > 0 else 'ALL'}")
    print(f"  Started: {time.strftime('%H:%M:%S')}")
    print()
    
    # Run Java extractor
    cmd = [
        "java", "-Xmx2g",
        "-cp", CLASSPATH,
        "LuceneExtractor",
        str(index_path),
        str(output_file),
        str(max_docs)
    ]
    
    start_time = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(SCRIPTS_DIR))
    elapsed = time.time() - start_time
    
    # Print stderr (progress messages)
    if result.stderr:
        for line in result.stderr.split('\n'):
            if 'Extracted' in line or 'Index:' in line or 'Total' in line or 'complete' in line:
                print(f"  {line}")
    
    if result.returncode != 0:
        print(f"  ✗ Extraction failed")
        return False, 0
    
    # Check output
    if not output_file.exists():
        print(f"  ✗ Output file not created")
        return False, 0
    
    # Get file size
    file_size = output_file.stat().st_size
    print(f"\n  ✓ Success!")
    print(f"  File size: {file_size / 1e6:.1f} MB")
    print(f"  Time: {elapsed:.0f}s ({elapsed/60:.1f} min)")
    print(f"  Finished: {time.strftime('%H:%M:%S')}")
    
    return True, file_size


def check_prerequisites() -> bool:
    """Check if all prerequisites are met."""
    print("Checking prerequisites...")
    
    # Check Java
    try:
        result = subprocess.run(["java", "-version"], capture_output=True, text=True)
        print(f"  ✓ Java installed")
    except:
        print("  ✗ Java not found! Please install Java 11+")
        return False
    
    # Check Lucene JARs
    if not LUCENE_CORE.exists():
        print(f"  ✗ Lucene core JAR not found: {LUCENE_CORE}")
        return False
    print(f"  ✓ Lucene core: {LUCENE_CORE.name}")
    
    if not LUCENE_CODECS.exists():
        print(f"  ✗ Lucene codecs JAR not found: {LUCENE_CODECS}")
        return False
    print(f"  ✓ Lucene codecs: {LUCENE_CODECS.name}")
    
    # Check store directory
    if not STORE_DIR.exists():
        print(f"  ✗ Store directory not found: {STORE_DIR}")
        return False
    print(f"  ✓ Store directory: {STORE_DIR}")
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"  ✓ Output directory: {OUTPUT_DIR}")
    
    return True


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract all Lucene indexes from Shamela")
    parser.add_argument("--quick", action="store_true", help="Quick test mode (extract 1000 docs per index)")
    parser.add_argument("--index", type=str, help="Extract specific index only")
    parser.add_argument("--max-docs", type=int, default=-1, help="Limit docs per index (-1 = all)")
    
    args = parser.parse_args()
    
    print("="*70)
    print("  🕌 ATHAR - FULL LUCENE EXTRACTION PIPELINE")
    print("="*70)
    print()
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n✗ Prerequisites check failed")
        sys.exit(1)
    
    # Compile extractor
    print("\nCompiling Java extractor...")
    if not compile_extractor():
        print("\n✗ Compilation failed")
        sys.exit(1)
    
    # Determine which indexes to extract
    if args.index:
        indexes_to_extract = [args.index]
    elif args.quick:
        # Quick mode: extract first 1000 docs from small indexes
        indexes_to_extract = ["esnad", "author", "book"]
        args.max_docs = 1000
        print("\n🚀 QUICK MODE: Extracting 1000 docs from small indexes")
    else:
        # Full mode: extract all indexes
        indexes_to_extract = list(ALL_INDEXES.keys())
        print("\n🚀 FULL MODE: Extracting ALL indexes")
        print(f"   Estimated time: 3-5 hours")
        print(f"   Estimated output: ~13 GB")
    
    # Extract indexes
    print(f"\n{'='*70}")
    print(f"  EXTRACTION START")
    print(f"{'='*70}")
    
    success_count = 0
    fail_count = 0
    total_size = 0
    
    for index_name in indexes_to_extract:
        success, size = extract_index(index_name, max_docs=args.max_docs)
        if success:
            success_count += 1
            total_size += size
        else:
            fail_count += 1
    
    # Summary
    print(f"\n{'='*70}")
    print(f"  ✅ EXTRACTION COMPLETE")
    print(f"{'='*70}")
    print(f"\n  Successful: {success_count}/{len(indexes_to_extract)}")
    if fail_count > 0:
        print(f"  Failed: {fail_count}")
    print(f"  Total output: {total_size / 1e9:.2f} GB")
    print(f"\n  Output files:")
    for f in sorted(OUTPUT_DIR.glob("lucene_*.json")):
        print(f"    {f.name:30s} {f.stat().st_size / 1e6:8.1f} MB")
    
    print(f"\n  Next steps:")
    print(f"    1. Merge with master catalog:")
    print(f"       python scripts/data/lucene/merge_lucene_with_master.py")
    print(f"    2. Build hierarchical chunks:")
    print(f"       python scripts/data/lucene/run_pipeline.py")
    print(f"    3. Upload to Hugging Face:")
    print(f"       python notebooks/04_upload_to_huggingface.ipynb")
    print()


if __name__ == "__main__":
    main()
