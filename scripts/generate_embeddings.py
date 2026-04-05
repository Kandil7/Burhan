#!/usr/bin/env python3
"""
Batch Embedding Generation Script for Athar Islamic QA system.

Generates embeddings for:
- Processed Islamic books (10,000+ books)
- Hadith collections
- Quran tafsir passages
- General Islamic knowledge documents

Usage:
    python scripts/generate_embeddings.py --collection fiqh_passages
    python scripts/generate_embeddings.py --collection hadith_passages
    python scripts/generate_embeddings.py --collection all
    
    python scripts/generate_embeddings.py --limit 1000 (process first 1000 docs)
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Optional

import numpy as np
from tqdm import tqdm

from src.knowledge.embedding_model import EmbeddingModel
from src.knowledge.vector_store import VectorStore
from src.config.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger()

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"


def load_documents(collection: str, limit: Optional[int] = None) -> list[dict]:
    """
    Load documents for a specific collection.
    
    Args:
        collection: Collection name (fiqh_passages, hadith_passages, etc.)
        limit: Maximum number of documents
        
    Returns:
        List of document dicts
    """
    documents = []
    
    if collection == "fiqh_passages":
        # Load from processed extracted books
        chunk_files = list(PROCESSED_DIR.glob("*_chunks.json"))
        
        for chunk_file in chunk_files:
            with open(chunk_file, 'r', encoding='utf-8') as f:
                chunks = json.load(f)
                documents.extend(chunks)
                
                if limit and len(documents) >= limit:
                    documents = documents[:limit]
                    break
    
    elif collection == "hadith_passages":
        # Load hadith data (would be processed separately)
        hadith_file = PROCESSED_DIR / "hadith" / "hadith_chunks.json"
        if hadith_file.exists():
            with open(hadith_file, 'r', encoding='utf-8') as f:
                documents = json.load(f)
    
    elif collection == "general_islamic":
        # Load general Islamic knowledge documents
        general_files = list((PROCESSED_DIR / "general").glob("*.json"))
        
        for general_file in general_files:
            with open(general_file, 'r', encoding='utf-8') as f:
                docs = json.load(f)
                documents.extend(docs)
    
    elif collection == "all":
        # Load all collections
        for coll in ["fiqh_passages", "hadith_passages", "general_islamic"]:
            documents.extend(load_documents(coll, limit))
    
    logger.info(
        "embeddings.documents_loaded",
        collection=collection,
        count=len(documents)
    )
    
    return documents


async def generate_embeddings(
    collection: str,
    limit: Optional[int] = None,
    batch_size: int = 32
):
    """
    Generate embeddings for a collection and upsert to Qdrant.
    
    Args:
        collection: Collection name
        limit: Maximum documents to process
        batch_size: Batch size for embedding generation
    """
    logger.info("embeddings.generating", collection=collection)
    
    # Load documents
    documents = load_documents(collection, limit)
    
    if not documents:
        logger.warning("embeddings.no_documents", collection=collection)
        return
    
    # Initialize model and vector store
    model = EmbeddingModel()
    await model.load_model()
    
    vector_store = VectorStore()
    await vector_store.initialize()
    
    # Process in batches
    total_embedded = 0
    errors = 0
    
    for i in tqdm(range(0, len(documents), batch_size), desc=f"Embedding {collection}"):
        batch = documents[i:i + batch_size]
        
        try:
            # Extract texts
            texts = [doc.get("content", "") for doc in batch]
            
            # Generate embeddings
            embeddings = await model.encode(texts, batch_size=len(texts))
            
            # Upsert to Qdrant
            await vector_store.upsert(
                collection=collection,
                documents=batch,
                embeddings=embeddings
            )
            
            total_embedded += len(batch)
            
        except Exception as e:
            logger.error(
                "embeddings.batch_error",
                batch=i // batch_size,
                error=str(e)
            )
            errors += len(batch)
    
    logger.info(
        "embeddings.complete",
        collection=collection,
        total=total_embedded,
        errors=errors
    )
    
    # Print summary
    print(f"\n✅ Embedding Generation Complete")
    print(f"   Collection: {collection}")
    print(f"   Documents: {total_embedded}")
    print(f"   Errors: {errors}")
    print(f"   Model: {model.MODEL_NAME}")
    print(f"   Device: {model.device}")
    print(f"\n📊 Cache Stats: {model.get_stats()}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate Embeddings")
    parser.add_argument(
        "--collection",
        choices=["fiqh_passages", "hadith_passages", "general_islamic", "all"],
        default="all",
        help="Collection to embed"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of documents to process"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Batch size for embedding generation"
    )
    
    args = parser.parse_args()
    
    import asyncio
    asyncio.run(generate_embeddings(args.collection, args.limit, args.batch_size))


if __name__ == "__main__":
    main()
