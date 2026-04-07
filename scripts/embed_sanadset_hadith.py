#!/usr/bin/env python3
"""
Sanadset Hadith Embedding Pipeline.

Processes all 650K+ hadith from Sanadset CSV and embeds them to Qdrant.

Usage:
    # Embed all hadith
    python scripts/embed_sanadset_hadith.py
    
    # Embed first N hadith (for testing)
    python scripts/embed_sanadset_hadith.py --limit 1000
    
    # Embed with custom batch size
    python scripts/embed_sanadset_hadith.py --batch-size 64
"""
import argparse
import asyncio
import sys
from pathlib import Path

import numpy as np
from tqdm import tqdm

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.sanadset_hadith_agent import parse_sanadset_csv
from src.knowledge.embedding_model import EmbeddingModel
from src.knowledge.vector_store import VectorStore
from src.config.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger()

CHECKPOINT_FILE = Path(__file__).parent.parent / "data" / "embeddings" / "sanadset_checkpoint.json"


def save_checkpoint(processed: int):
    """Save processing checkpoint."""
    CHECKPOINT_FILE.parent.mkdir(parents=True, exist_ok=True)
    import json
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump({"processed": processed}, f)
    logger.info("sanadset.checkpoint_saved", processed=processed)


def load_checkpoint() -> int:
    """Load last processed count."""
    import json
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE, 'r') as f:
            data = json.load(f)
        return data.get("processed", 0)
    return 0


async def embed_sanadset(limit: int = None, batch_size: int = 32, resume: bool = True):
    """
    Embed Sanadset hadith to Qdrant.
    
    Args:
        limit: Max hadith to process (None = all)
        batch_size: Batch size for embedding
        resume: Resume from checkpoint
    """
    logger.info("sanadset.embedding_start", limit=limit, batch_size=batch_size)
    
    # Initialize components
    logger.info("sanadset.loading_embedding_model")
    embedding_model = EmbeddingModel()
    await embedding_model.load_model()
    
    logger.info("sanadset.loading_vector_store")
    vector_store = VectorStore()
    await vector_store.initialize()
    
    # Collection already exists (has 32 vectors)
    
    # Parse CSV
    csv_path = Path(__file__).parent.parent / "datasets" / "Sanadset 368K Data on Hadith Narrators" / "Sanadset 368K Data on Hadith Narrators" / "sanadset.csv"
    
    if not csv_path.exists():
        logger.error("sanadset.csv_not_found", path=str(csv_path))
        return
    
    logger.info("sanadset.parsing_csv", path=str(csv_path))
    
    # Count total lines first
    total_lines = sum(1 for _ in open(csv_path, 'r', encoding='utf-8')) - 1  # minus header
    actual_limit = min(limit, total_lines) if limit else total_lines
    
    start_from = 0
    if resume:
        start_from = load_checkpoint()
        if start_from > 0:
            logger.info("sanadset.resuming", from_row=start_from, total=actual_limit)
    
    # Process in batches
    processed = start_from
    errors = 0
    
    # Re-parse CSV from start_from position
    documents = []
    import csv
    import re
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        # Skip already processed rows
        for _ in range(start_from):
            next(reader)
        
        pbar = tqdm(total=actual_limit - start_from, desc="Embedding hadith", unit="hadith")
        
        batch_docs = []
        batch_texts = []
        
        for i, row in enumerate(reader):
            if processed >= actual_limit:
                break
            
            try:
                # Clean sanad
                sanad_raw = row.get('Sanad', '')
                sanad_clean = re.sub(r'<[^>]+>', '', sanad_raw).strip()
                
                # Extract matn
                matn = row.get('Matn', '').strip()
                
                # Build content
                content_parts = []
                if matn:
                    content_parts.append(matn)
                if sanad_clean and sanad_clean != "No SANAD":
                    content_parts.append(sanad_clean)
                book = row.get('Book', '')
                if book:
                    content_parts.append(book)
                
                content = " | ".join(content_parts)
                
                doc = {
                    "chunk_index": processed,
                    "content": content[:5000],  # Truncate very long content
                    "metadata": {
                        "type": "hadith",
                        "book": book,
                        "num_hadith": row.get('Num_hadith', ''),
                        "matn": matn[:2000],
                        "sanad": sanad_clean[:1000],
                        "sanad_length": row.get('Sanad_Length', ''),
                        "dataset": "sanadset_368k",
                        "language": "ar",
                    }
                }
                batch_docs.append(doc)
                batch_texts.append(content[:2000])  # Limit for embedding model
                
                # Process batch
                if len(batch_docs) >= batch_size:
                    # Embed batch
                    embeddings = await embedding_model.encode(batch_texts)
                    
                    # Upsert to Qdrant
                    count = await vector_store.upsert("hadith_passages", batch_docs, embeddings)
                    processed += count
                    pbar.update(count)
                    
                    # Save checkpoint every 1000
                    if processed % 1000 == 0:
                        save_checkpoint(processed)
                    
                    batch_docs = []
                    batch_texts = []
            
            except Exception as e:
                errors += 1
                if errors % 100 == 0:
                    logger.warning("sanadset.errors", count=errors, last_error=str(e))
        
        # Process remaining batch
        if batch_docs:
            embeddings = await embedding_model.encode(batch_texts)
            count = await vector_store.upsert("hadith_passages", batch_docs, embeddings)
            processed += count
            pbar.update(count)
        
        pbar.close()
    
    # Final stats
    final_count = await vector_store.get_collection_stats("hadith_passages")
    logger.info(
        "sanadset.embedding_complete",
        processed=processed,
        errors=errors,
        total_in_collection=final_count.get("vectors_count", "unknown")
    )
    
    print(f"\n✅ Sanadset Embedding Complete")
    print(f"   Processed: {processed:,} hadith")
    print(f"   Errors: {errors}")
    print(f"   Total in collection: {final_count.get('vectors_count', 'unknown')}")


def main():
    parser = argparse.ArgumentParser(description="Embed Sanadset Hadith")
    parser.add_argument("--limit", type=int, default=None, help="Max hadith to process")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size")
    parser.add_argument("--no-resume", action="store_true", help="Don't resume from checkpoint")
    args = parser.parse_args()
    
    asyncio.run(embed_sanadset(
        limit=args.limit,
        batch_size=args.batch_size,
        resume=not args.no_resume
    ))


if __name__ == "__main__":
    main()
