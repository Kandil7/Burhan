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

# ==========================================
# Category to Collection Mapping (All 40 Shamela categories)
# ==========================================
CATEGORY_COLLECTION_MAP = {
    # Hadith-related (5 categories → hadith_passages)
    "كتب السنة": "hadith_passages",
    "شروح الحديث": "hadith_passages",
    "علوم الحديث": "hadith_passages",
    "التخريج والأطراف": "hadith_passages",
    "العلل والسؤالات الحديثية": "hadith_passages",
    
    # Quran/Tafsir-related (3 categories → quran_tafsir)
    "التفسير": "quran_tafsir",
    "علوم القرآن وأصول التفسير": "quran_tafsir",
    "التجويد والقراءات": "quran_tafsir",
    
    # Fiqh-related (8 categories → fiqh_passages)
    "الفقه العام": "fiqh_passages",
    "مسائل فقهية": "fiqh_passages",
    "الفقه الحنفي": "fiqh_passages",
    "الفقه المالكي": "fiqh_passages",
    "الفقه الشافعي": "fiqh_passages",
    "الفقه الحنبلي": "fiqh_passages",
    "السياسة الشرعية والقضاء": "fiqh_passages",
    "الفرائض والوصايا": "fiqh_passages",
    "الفتاوى": "fiqh_passages",
    
    # Usul al-Fiqh (2 categories → usul_fiqh_passages)
    "أصول الفقه": "usul_fiqh_passages",
    "علوم الفقه والقواعد الفقهية": "usul_fiqh_passages",
    
    # Aqeedah (2 categories → aqeedah_passages)
    "العقيدة": "aqeedah_passages",
    "الفرق والردود": "aqeedah_passages",
    
    # Seerah/Biography (3 categories → seerah_passages)
    "السيرة النبوية": "seerah_passages",
    "التراجم والطبقات": "seerah_passages",
    "الأنساب": "seerah_passages",
    
    # History (2 categories → islamic_history_passages)
    "التاريخ": "islamic_history_passages",
    "البلدان والرحلات": "islamic_history_passages",
    
    # Arabic Language (6 categories → arabic_language_passages)
    "كتب اللغة": "arabic_language_passages",
    "النحو والصرف": "arabic_language_passages",
    "الغريب والمعاجم": "arabic_language_passages",
    "البلاغة": "arabic_language_passages",
    "الأدب": "arabic_language_passages",
    "الدواوين الشعرية": "arabic_language_passages",
    "العروض والقوافي": "arabic_language_passages",
    
    # General Islamic (8 categories → general_islamic_passages)
    "كتب عامة": "general_islamic_passages",
    "الرقائق والآداب والأذكار": "general_islamic_passages",
    "الجوامع": "general_islamic_passages",
    "فهارس الكتب والأدلة": "general_islamic_passages",
    "المنطق": "general_islamic_passages",
    "الطب": "general_islamic_passages",
    "علوم أخرى": "general_islamic_passages",
    "#": "general_islamic_passages",
}


def route_chunk_to_collection(chunk: dict) -> str:
    """
    Route a chunk to the appropriate collection based on metadata.
    
    Args:
        chunk: Document chunk with metadata
        
    Returns:
        Collection name string
    """
    metadata = chunk.get('metadata', {})
    chunk_type = metadata.get('type', '')
    category = metadata.get('category', '')
    
    # Hadith chunks
    if chunk_type == 'hadith':
        return 'hadith_passages'
    
    # Dua chunks
    if chunk_type == 'dua':
        return 'duas_adhkar'
    
    # Islamic book chunks - route by category
    if chunk_type == 'islamic_book':
        return CATEGORY_COLLECTION_MAP.get(category, 'general_islamic_passages')
    
    # Default to general
    return 'general_islamic_passages'


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
        # Load from processed islamic books (filter by type)
        all_chunks_file = PROCESSED_DIR / "all_chunks.json"
        if all_chunks_file.exists():
            logger.info("embeddings.loading_all_chunks", path=str(all_chunks_file))
            with open(all_chunks_file, 'r', encoding='utf-8') as f:
                all_chunks = json.load(f)
                # Filter for islamic_book type chunks
                documents = [c for c in all_chunks if c.get('metadata', {}).get('type') == 'islamic_book']
                logger.info("embeddings.filtered_chunks", total=len(all_chunks), fiqh=len(documents))

        # Also load hadith chunks if we don't have enough
        if len(documents) < 1000:
            hadith_file = PROCESSED_DIR / "hadith_chunks.json"
            if hadith_file.exists():
                with open(hadith_file, 'r', encoding='utf-8') as f:
                    hadith_chunks = json.load(f)
                    documents.extend(hadith_chunks)

        if limit and len(documents) > limit:
            documents = documents[:limit]

    elif collection == "hadith_passages":
        # FIXED: Correct path to hadith_chunks.json
        hadith_file = PROCESSED_DIR / "hadith_chunks.json"
        if hadith_file.exists():
            with open(hadith_file, 'r', encoding='utf-8') as f:
                documents = json.load(f)
                logger.info("embeddings.hadith_loaded", count=len(documents))
        else:
            logger.warning("embeddings.hadith_file_not_found", path=str(hadith_file))

        if limit and len(documents) > limit:
            documents = documents[:limit]

    elif collection in ("general_islamic", "general_islamic_passages"):
        # FIXED: Filter from all_chunks.json by category
        all_chunks_file = PROCESSED_DIR / "all_chunks.json"
        if all_chunks_file.exists():
            with open(all_chunks_file, 'r', encoding='utf-8') as f:
                all_chunks = json.load(f)
                # Filter for general Islamic categories (not fiqh-specific)
                general_categories = [
                    "كتب عامة", "الرقائق والآداب والأذكار", "الجوامع",
                    "فهارس الكتب والأدلة", "المنطق", "الطب", "علوم أخرى", "#"
                ]
                documents = [
                    c for c in all_chunks
                    if c.get('metadata', {}).get('type') == 'islamic_book'
                    and c.get('metadata', {}).get('category') in general_categories
                ]
                logger.info("embeddings.general_loaded", total=len(all_chunks), general=len(documents))

        if limit and len(documents) > limit:
            documents = documents[:limit]

    elif collection == "duas_adhkar":
        # Load duas from seed data
        duas_file = Path(__file__).parent.parent / "data" / "seed" / "duas.json"
        if duas_file.exists():
            with open(duas_file, 'r', encoding='utf-8') as f:
                duas = json.load(f)
                # Convert duas to chunk format
                documents = [
                    {
                        "chunk_index": i,
                        "content": f"الدعاء: {dua.get('arabic_text', '')}\n\nالترجمة: {dua.get('translation', '')}\n\nالمناسبة: {dua.get('occasion', '')}\n\nالمصدر: {dua.get('source', '')}",
                        "metadata": {
                            "type": "dua",
                            "category": dua.get('category', 'general'),
                            "occasion": dua.get('occasion', ''),
                            "source": dua.get('source', ''),
                            "id": dua.get('id', i)
                        }
                    }
                    for i, dua in enumerate(duas)
                ]
                logger.info("embeddings.duas_loaded", count=len(documents))

    elif collection == "all":
        # Load all collections sequentially
        for coll in ["fiqh_passages", "hadith_passages", "general_islamic_passages", "duas_adhkar", "arabic_language_passages"]:
            coll_docs = load_documents(coll, limit)
            documents.extend(coll_docs)
            if limit and len(documents) >= limit:
                documents = documents[:limit]
                break

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
        choices=[
            "fiqh_passages", "hadith_passages", "quran_tafsir",
            "aqeedah_passages", "seerah_passages", "islamic_history_passages",
            "usul_fiqh_passages", "arabic_language_passages",
            "general_islamic_passages", "duas_adhkar", "all"
        ],
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
