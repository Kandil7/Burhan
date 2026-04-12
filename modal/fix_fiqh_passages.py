#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║       🕌  ATHAR – Fix Fiqh Passages Embedding                               ║
║                                                                              ║
║  Problem: fiqh_passages in Qdrant has corrupted UTF-8 data                   ║
║  Source:  fiqh_passages.jsonl on disk has CORRECT UTF-8 (7 GB, 2.4M docs)    ║
║  Solution: Re-embed with BGE-M3 on GPU, upload to Qdrant                    ║
║                                                                              ║
║  Run:  modal run modal/fix_fiqh_passages.py                                 ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import json
import time
import gzip
import modal

app = modal.App("athar-fix-fiqh")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "torch==2.2.2",
        "transformers>=4.39.0",
        "accelerate>=0.27.0",
        "qdrant-client>=1.9.0",
        "tqdm",
        "numpy",
        "sentencepiece",
    )
    .env({
        "TOKENIZERS_PARALLELISM": "false",
    })
)

SECRETS = [
    modal.Secret.from_name("qdrant-secret"),
    modal.Secret.from_name("hf-secret"),
]

COLLECTION_NAME = "fiqh_passages"
EMBED_MODEL_ID = "BAAI/bge-m3"
EMBED_DIM = 1024
MAX_LENGTH = 512
BATCH_SIZE = 256  # L4 safe, 512 for L40S
QDRANT_BATCH = 500

LOCAL_JSONL = "data/processed/lucene_pages/collections/fiqh_passages.jsonl"


@app.cls(
    gpu="L4",
    image=image,
    secrets=SECRETS,
    timeout=50400,  # 14 hours
    memory=32768,
    cpu=8,
)
class FiqhEmbedder:
    @modal.enter()
    def load_model(self):
        import torch
        from transformers import AutoTokenizer, AutoModel

        hf_token = os.environ.get("HF_TOKEN")
        print("🤖 Loading BAAI/bge-m3...")

        self.tokenizer = AutoTokenizer.from_pretrained(EMBED_MODEL_ID, token=hf_token)
        self.model = AutoModel.from_pretrained(EMBED_MODEL_ID, token=hf_token)

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = self.model.to(self.device).half().eval()

        vram = self.model.get_memory_footprint() / 1e9 if hasattr(self.model, "get_memory_footprint") else "~1.06"
        print(f"✅ BGE-M3 ready | device={self.device.upper()} | FP16 | VRAM≈{vram:.2f} GB")
        print(f"📐 Config: MAX_LENGTH={MAX_LENGTH}, BATCH_SIZE={BATCH_SIZE}")

    @modal.method()
    def embed_and_upload(self) -> dict:
        import torch
        import numpy as np
        from tqdm import tqdm
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, VectorParams, PointStruct

        # ── 1. Load passages from local JSONL ──
        print(f"\n📖 Loading fiqh_passages from {LOCAL_JSONL}...")
        t0 = time.time()
        passages = []
        with open(LOCAL_JSONL, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                try:
                    passages.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

        load_time = time.time() - t0
        print(f"✅ Loaded {len(passages):,} passages in {load_time:.1f}s")

        # Verify encoding
        sample = passages[0]["content"][:100]
        print(f"   Sample content: {sample}")

        # ── 2. Embed ──
        print(f"\n⚡ Embedding {len(passages):,} passages...")
        contents = [str(p.get("content", "")) for p in passages]
        all_embeddings = []
        t0 = time.time()

        for i in tqdm(range(0, len(contents), BATCH_SIZE), desc="Embedding", unit="batch"):
            batch = contents[i:i + BATCH_SIZE]
            encoded = self.tokenizer(
                batch, padding=True, truncation=True, max_length=MAX_LENGTH, return_tensors="pt"
            ).to(self.device)

            with torch.no_grad():
                outputs = self.model(**encoded)
                embs = outputs.last_hidden_state[:, 0, :]
                embs = torch.nn.functional.normalize(embs, p=2, dim=1)

            all_embeddings.append(embs.cpu().float().numpy())

            if (i // BATCH_SIZE) % 200 == 0 and i > 0:
                torch.cuda.empty_cache()

        elapsed = time.time() - t0
        emb_array = np.concatenate(all_embeddings, axis=0)
        speed = len(passages) / elapsed
        print(f"\n✅ Embedded {len(passages):,} vectors | shape={emb_array.shape} | {elapsed/60:.1f} min | {speed:.0f} passages/sec")

        # ── 3. Upload to Qdrant ──
        print(f"\n📤 Uploading to Qdrant...")
        qdrant_url = os.environ["QDRANT_URL"]
        qdrant_key = os.environ.get("QDRANT_API_KEY")
        client = QdrantClient(url=qdrant_url, api_key=qdrant_key, timeout=120)

        # Create collection
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=EMBED_DIM, distance=Distance.COSINE),
        )
        print(f"✅ Created collection: {COLLECTION_NAME}")

        # Upload
        t0 = time.time()
        for start in tqdm(range(0, len(passages), QDRANT_BATCH), desc="Uploading", unit="batch"):
            end = min(start + QDRANT_BATCH, len(passages))
            batch_emb = emb_array[start:end]
            batch_pas = passages[start:end]

            points = [
                PointStruct(
                    id=start + idx,
                    vector=batch_emb[idx].tolist(),
                    payload={
                        "content": p.get("content", ""),
                        "content_type": p.get("content_type"),
                        "book_id": p.get("book_id"),
                        "book_title": p.get("book_title", ""),
                        "category": p.get("category", ""),
                        "author": p.get("author", ""),
                        "author_death": p.get("author_death"),
                        "page_number": p.get("page_number"),
                        "chapter": p.get("chapter", ""),
                        "section": p.get("section", ""),
                        "collection": COLLECTION_NAME,
                        "hierarchy": p.get("hierarchy", []),
                        "section_title": p.get("section_title", ""),
                        "title": p.get("title", ""),
                        "page": p.get("page"),
                    },
                )
                for idx, p in enumerate(batch_pas)
            ]

            client.upsert(collection_name=COLLECTION_NAME, points=points)

        upload_time = time.time() - t0
        total_time = load_time + elapsed + upload_time

        print(f"\n{'='*70}")
        print(f"🎉 Fiqh Passages Embedding COMPLETE")
        print(f"{'='*70}")
        print(f"  Passages     : {len(passages):,}")
        print(f"  Vector shape  : {emb_array.shape}")
        print(f"  Load time     : {load_time:.1f}s")
        print(f"  Embed time    : {elapsed/60:.1f} min")
        print(f"  Upload time   : {upload_time/60:.1f} min")
        print(f"  Total time    : {total_time/60:.1f} min")
        print(f"  Speed         : {speed:.0f} passages/sec")
        gpu_price = {"L4": 0.80, "L40S": 1.95, "A100-40GB": 2.10}
        gpu_name = os.environ.get("MODAL_GPU_TYPE", "L4")
        print(f"  GPU cost      : ${total_time/3600 * gpu_price.get(gpu_name, 0.80):.2f} ({gpu_name})")
        print(f"{'='*70}")

        return {
            "passages": len(passages),
            "shape": list(emb_array.shape),
            "embed_minutes": elapsed / 60,
            "upload_minutes": upload_time / 60,
            "total_minutes": total_time / 60,
            "speed": speed,
        }


@app.local_entrypoint()
def main():
    print("\n" + "="*70)
    print("🕌  ATHAR – Fix Fiqh Passages Embedding")
    print("="*70)
    print(f"  Source: {LOCAL_JSONL}")
    print(f"  GPU: L4 ($0.80/hr)")
    print(f"  Est: ~2.4M docs × 0.5ms = ~20 min + upload\n")

    result = FiqhEmbedder().embed_and_upload.remote()

    print(f"\n{'='*70}")
    print(f"✅ DONE: {result['passages']:,} passages embedded and uploaded to Qdrant")
    print(f"{'='*70}")
