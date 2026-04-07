"""
Lucene extraction pipeline for Shamela system_book_datasets.

Modules:
    extract_lucene_pages  - Main extraction (A)
    decode_lucene_content - Encoding fix utility (B)
    merge_lucene_with_master - Merge with catalog (C)
    verify_lucene_extraction - Quality verification (D)

Usage:
    # Full pipeline
    python scripts/data/lucene/extract_lucene_pages.py
    python scripts/data/lucene/decode_lucene_content.py --input data/processed/lucene_pages/raw/ --output data/processed/lucene_pages/cleaned/
    python scripts/data/lucene/merge_lucene_with_master.py
    python scripts/data/lucene/verify_lucene_extraction.py

    # Or use the pipeline runner
    python scripts/data/lucene/run_pipeline.py
"""
