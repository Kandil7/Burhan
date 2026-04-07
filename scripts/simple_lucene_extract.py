#!/usr/bin/env python3
"""
Simple Lucene extraction using existing working Java extractor.

Extracts Lucene indexes and organizes output by book_id.
"""
import subprocess
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
STORE_DIR = BASE_DIR / "datasets" / "system_book_datasets" / "store"
LUCENE_JARS = list((BASE_DIR / "lib" / "lucene").glob("*.jar"))
CLASSPATH = ";".join(str(j) for j in LUCENE_JARS)
OUTPUT_DIR = BASE_DIR / "data" / "processed" / "lucene_simple"

def extract_index(index_name, max_docs=1000):
    """Extract a Lucene index using Java."""
    print(f"\n📚 Extracting {index_name} (max {max_docs} docs)...")
    
    index_path = STORE_DIR / index_name
    if not index_path.exists():
        print(f"  ✗ Not found: {index_path}")
        return
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / f"{index_name}.json"
    
    cmd = [
        "java",
        "-cp", f".;{CLASSPATH}",
        "-Xmx2g",
        "LuceneExtractor",
        str(index_path),
        str(output_file),
        str(max_docs)
    ]
    
    print(f"  Running: java -cp ... LuceneExtractor ...")
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(BASE_DIR / "scripts")
    )
    
    # Print stderr (progress messages)
    if result.stderr:
        for line in result.stderr.split('\n'):
            if line.strip():
                print(f"  {line}")
    
    if output_file.exists():
        size = output_file.stat().st_size
        print(f"  ✓ Output: {output_file.name} ({size/1e6:.1f} MB)")
        
        # Count docs
        with open(output_file) as f:
            content = f.read()
            # Count JSON objects (simplified)
            doc_count = content.count('"id":')
            print(f"  ✓ Docs extracted: ~{doc_count}")
        
        return output_file
    
    print(f"  ✗ Extraction failed")
    return None

def main():
    print("="*70)
    print("🕌 ATHAR - SIMPLE LUCENE EXTRACTION")
    print("="*70)
    
    # Test with small indexes
    indexes = {
        "esnad": 1000,      # Hadith chains
        "author": 100,      # Author bios
        "book": 100,        # Book index
        "title": 1000,      # Titles
    }
    
    for index_name, max_docs in indexes.items():
        extract_index(index_name, max_docs)
    
    print(f"\n{'='*70}")
    print(f"✅ EXTRACTION COMPLETE")
    print(f"{'='*70}")
    print(f"\n📁 Output: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
