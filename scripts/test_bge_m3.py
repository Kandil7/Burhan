#!/usr/bin/env python3
"""
Test BAAI/bge-m3 embedding model with Arabic queries.

This script tests BGE-M3's ability to encode Arabic Islamic text
and compares similarity between related queries.

Usage:
    python scripts/test_bge_m3.py
    python scripts/test_bge_m3.py --model BAAI/bge-m3

Prerequisites:
    pip install FlagEmbedding
"""

import argparse
import sys
import time
from pathlib import Path

try:
    from FlagEmbedding import BGEM3FlagModel
    HAS_BGE = True
except ImportError:
    HAS_BGE = False
    print("❌ FlagEmbedding not installed. Run: pip install FlagEmbedding")
    print("   Continuing in dry-run mode to show what would be tested...")

# Test queries in Arabic
TEST_QUERIES = [
    # Islamic jurisprudence
    "ما حكم الصلاة؟",
    "هل الصلاة واجبة؟",
    "ما هي أحكام الصلاة؟",
    
    # Zakat
    "ما حكم زكاة المال؟",
    "كم نسبة الزكاة؟",
    "متى تجب الزكاة؟",
    
    # Quran
    "ما معنى آية الكرسي؟",
    "تفسير سورة الفاتحة",
    "فضل سورة البقرة",
    
    # Hadith
    "ما هو حديث جبريل؟",
    "شرح الأربعين النووية",
    "أفضل الأحاديث النبوية",
]

# Expected similar pairs
SIMILAR_PAIRS = [
    (0, 1, "Similar: prayer ruling questions"),
    (0, 2, "Related: prayer rulings"),
    (3, 4, "Related: zakat questions"),
    (6, 7, "Related: Quran tafsir"),
]

# Expected dissimilar pairs
DISSIMILAR_PAIRS = [
    (0, 5, "Different: prayer vs zakat"),
    (3, 8, "Different: zakat vs Quran"),
    (6, 9, "Different: Quran vs Hadith"),
]


def test_bge_m3(model_name: str = "BAAI/bge-m3", dry_run: bool = False):
    """Test BGE-M3 model with Arabic queries."""
    
    print("=" * 70)
    print("🕌 ATHAR - TEST BGE-M3 EMBEDDING MODEL")
    print("=" * 70)
    print(f"  Model:           {model_name}")
    print(f"  Test queries:    {len(TEST_QUERIES)}")
    print(f"  Similar pairs:   {len(SIMILAR_PAIRS)}")
    print(f"  Dissimilar pairs: {len(DISSIMILAR_PAIRS)}")
    print("=" * 70)
    
    if dry_run or not HAS_BGE:
        print("\n[DRY RUN] Showing what would be tested:")
        print("\nTest queries:")
        for i, query in enumerate(TEST_QUERIES):
            print(f"  {i+1}. {query}")
        
        print("\nExpected similar pairs:")
        for i, j, desc in SIMILAR_PAIRS:
            print(f"  ✓ {TEST_QUERIES[i][:40]}... ↔ {TEST_QUERIES[j][:40]}...")
            print(f"    ({desc})")
        
        print("\nExpected dissimilar pairs:")
        for i, j, desc in DISSIMILAR_PAIRS:
            print(f"  ✗ {TEST_QUERIES[i][:40]}... ↔ {TEST_QUERIES[j][:40]}...")
            print(f"    ({desc})")
        
        print("\n💡 Install FlagEmbedding to run actual test:")
        print("   pip install FlagEmbedding")
        return
    
    # Load model
    print("\n📦 Loading model...")
    start_time = time.time()
    
    try:
        model = BGEM3FlagModel(
            model_name,
            use_fp16=True,
        )
        load_time = time.time() - start_time
        print(f"  ✓ Model loaded in {load_time:.1f}s")
    except Exception as e:
        print(f"  ✗ Failed to load model: {e}")
        return
    
    # Encode queries
    print(f"\n🔢 Encoding {len(TEST_QUERIES)} queries...")
    start_time = time.time()
    
    try:
        result = model.encode(
            TEST_QUERIES,
            batch_size=4,
            max_length=8192,
        )
        
        embeddings = result['dense_vecs']
        encode_time = time.time() - start_time
        avg_time = encode_time / len(TEST_QUERIES) * 1000
        
        print(f"  ✓ Encoded in {encode_time:.1f}s ({avg_time:.0f}ms per query)")
        print(f"  ✓ Embedding shape: {embeddings.shape}")
        print(f"  ✓ Dimensions: {embeddings.shape[1]}")
        
    except Exception as e:
        print(f"  ✗ Failed to encode: {e}")
        return
    
    # Test similarity
    print("\n🔍 Testing similarity...")
    
    import numpy as np
    
    def cosine_sim(a, b):
        """Compute cosine similarity between two vectors."""
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    # Similar pairs (should have high similarity > 0.7)
    print("\n  Similar pairs (expected > 0.7):")
    similar_scores = []
    for i, j, desc in SIMILAR_PAIRS:
        sim = cosine_sim(embeddings[i], embeddings[j])
        similar_scores.append(sim)
        status = "✅" if sim > 0.7 else "⚠️"
        print(f"    {status} Query {i+1} ↔ Query {j+1}: {sim:.3f}")
        print(f"       ({desc})")
    
    # Dissimilar pairs (should have low similarity < 0.5)
    print("\n  Dissimilar pairs (expected < 0.5):")
    dissimilar_scores = []
    for i, j, desc in DISSIMILAR_PAIRS:
        sim = cosine_sim(embeddings[i], embeddings[j])
        dissimilar_scores.append(sim)
        status = "✅" if sim < 0.5 else "⚠️"
        print(f"    {status} Query {i+1} ↔ Query {j+1}: {sim:.3f}")
        print(f"       ({desc})")
    
    # Summary
    avg_similar = np.mean(similar_scores) if similar_scores else 0
    avg_dissimilar = np.mean(dissimilar_scores) if dissimilar_scores else 0
    separation = avg_similar - avg_dissimilar
    
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    print(f"  Avg similar similarity:    {avg_similar:.3f}")
    print(f"  Avg dissimilar similarity: {avg_dissimilar:.3f}")
    print(f"  Separation:                {separation:.3f}")
    print(f"  Encoding speed:            {avg_time:.0f}ms/query")
    print("=" * 70)
    
    if separation > 0.3:
        print("\n✅ BGE-M3 is suitable for Arabic Islamic text!")
        print("   Recommendation: Migrate from Qwen3-Embedding-0.6B")
    else:
        print("\n⚠️ BGE-M3 separation is low. Consider:")
        print("   - Using domain-specific fine-tuning")
        print("   - Keeping current model")


def main():
    parser = argparse.ArgumentParser(description="Test BGE-M3 model")
    parser.add_argument(
        "--model",
        type=str,
        default="BAAI/bge-m3",
        help="Model name (default: BAAI/bge-m3)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be tested without running",
    )
    args = parser.parse_args()
    
    test_bge_m3(args.model, args.dry_run)


if __name__ == "__main__":
    main()
