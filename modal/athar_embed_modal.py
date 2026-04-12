# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║       🕌  ATHAR  –  Embed Pipeline on Modal  (L4 ★ / L40S ✦ / A100)       ║
║                                                                              ║
║  Purpose : Embed 7M+ Islamic-text passages with BAAI/bge-m3 on Modal GPU   ║
║  Output  : 10 Qdrant collections  +  HuggingFace backup                    ║
╚══════════════════════════════════════════════════════════════════════════════╝

QUICK-START
───────────
1.  Install Modal and authenticate:
        pip install modal
        modal setup                   # opens browser, saves API token

2.  Create secrets in the Modal dashboard  (Settings → Secrets):
        qdrant-secret  →  QDRANT_URL, QDRANT_API_KEY
        hf-secret      →  HF_TOKEN

3.  Run:
        modal run athar_embed_modal.py               # full pipeline
        modal run athar_embed_modal.py::embed_only   # skip download (already on volume)
        modal run athar_embed_modal.py::upload_only  # re-upload pre-computed embeddings
        modal run athar_embed_modal.py::verify       # check Qdrant collections

GPU OPTIONS  (Modal official pricing)
──────────────────────────────────────
┌────────────┬──────────┬─────────────┬──────────────┬──────────┬──────────────┐
│ GPU        │ VRAM     │ FP16 TFLOPs │ Mem BW GB/s  │ $/hr     │ Safe batch   │
├────────────┼──────────┼─────────────┼──────────────┼──────────┼──────────────┤
│ T4         │ 16 GB    │  65         │  300         │ $0.59    │ 64           │
│ L4    ★   │ 24 GB    │ 242         │  300         │ $0.80    │ 256          │
│ A10G       │ 24 GB    │ 125         │  600         │ $1.10    │ 256          │
│ L40S  ✦   │ 48 GB    │ 362         │  864         │ $1.95    │ 512          │
│ A100-40GB  │ 40 GB    │ 312         │ 1555         │ $2.10    │ 512          │
│ A100-80GB  │ 80 GB    │ 624         │ 2039         │ $2.50    │ 1024         │
└────────────┴──────────┴─────────────┴──────────────┴──────────┴──────────────┘

  T4      :  30h × $0.59 = $18.53   ❌ slow + OOM risk
  A10G    :   9h × $1.10 = $10.01   ❌ dominated by L4
  L4   ★  :  10h × $0.80 =  $8.27   ✅ cheapest  → DEFAULT
  L40S ✦  :   4h × $1.95 =  $8.43   ✅ 2.4× faster, only $0.16 more than L4
  A100-40G:   4h × $2.10 =  $7.57   ✅ fastest value, but $0.70 more than L4
  A100-80G:   3h × $2.50 =  $6.15   ✅ absolute fastest, overkill for 7M passages

  RECOMMENDATION:
    • Budget  / first run  →  L4   ("L4",   BATCH_SIZE=256)  ~$8.27
    • Fast    / team use   →  L40S ("L40S", BATCH_SIZE=512)  ~$8.43  ← 2.4× faster
    • Fastest / production →  A100-40GB   ("A100-40GB", BATCH_SIZE=512)

COST BREAKDOWN
──────────────
  ★ L4  ($0.80/hr, batch=256)
      Embed 7M passages     : ~9 h → $7.20
      Download + upload     : ~1.5h → $1.20
      ──────────────────────────────────────
      TOTAL                 : ~10.5h → ~$8.27

  ✦ L40S ($1.95/hr, batch=512)  ← 2.4× faster, $0.16 more
      Embed 7M passages     : ~3h  → $5.85
      Download + upload     : ~1.5h → $2.93
      ──────────────────────────────────────
      TOTAL                 :  ~4.5h → ~$8.43

  Both well inside the $30 Starter free credit.

SAFE BATCH-SIZE TABLE  (L4 = 24 GB VRAM, BGE-M3 FP16 ≈ 1.06 GB)
───────────────────────────────────────────────────────────────────
  max_length=512    →  batch_size=256   ← DEFAULT  (best throughput)
  max_length=1024   →  batch_size=128
  max_length=2048   →  batch_size=64
  max_length=4096   →  batch_size=16   ← uncomment CONFIG B below
  max_length=8192   →  batch_size=4    (very slow; rarely needed)

  ⚠️  NEVER mix max_length=4096 + batch_size=128  → OOM guaranteed.
      Attention memory = O(batch × seq_len²).  Double seq_len = 4× RAM.

ARCHITECTURE NOTES
──────────────────
  • Embedder (@app.cls) loads BGE-M3 ONCE then processes all 10 collections
    sequentially → zero model-reload overhead (~2 min saved per collection).
  • modal.Volume persists .npy + .jsonl across all pipeline steps and reruns.
  • volume.commit() flushes writes; volume.reload() sees remote writes.
  • upload_to_qdrant and backup_to_hf run in parallel via .map().
  • Resumable: _already_embedded() skips collections that finished earlier.
"""

# ── Standard library ──────────────────────────────────────────────────────────
import os
import json
import gzip
import time
import shutil
from datetime import datetime, timezone

# ── Modal SDK ─────────────────────────────────────────────────────────────────
import modal

# ═══════════════════════════════════════════════════════════════════════════════
# 1.  APP  &  CONTAINER IMAGE
# ═══════════════════════════════════════════════════════════════════════════════

app = modal.App("athar-embed")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "torch==2.2.2",
        "transformers>=4.39.0",
        "accelerate>=0.27.0",                    # faster model loading on GPU
        "huggingface_hub[hf_transfer]>=0.22.0",  # hf_transfer = 10× download speed
        "qdrant-client>=1.9.0",
        "tqdm",
        "numpy",
        "sentencepiece",          # BGE-M3 tokenizer dependency
    )
    .env({
        "HF_HUB_ENABLE_HF_TRANSFER": "1",   # Rust-based downloader
        "TOKENIZERS_PARALLELISM": "false",   # suppress fork warnings in batch loops
    })
)

# ═══════════════════════════════════════════════════════════════════════════════
# 2.  PERSISTENT VOLUME
# ═══════════════════════════════════════════════════════════════════════════════

volume = modal.Volume.from_name("athar-embeddings-vol", create_if_missing=True)

VOLUME_PATH     = "/vol"
COLLECTIONS_DIR = f"{VOLUME_PATH}/athar-collections/collections"
EMBEDDINGS_DIR  = f"{VOLUME_PATH}/embeddings"
PROGRESS_FILE   = f"{VOLUME_PATH}/progress.jsonl"

# ═══════════════════════════════════════════════════════════════════════════════
# 3.  SECRETS
# ═══════════════════════════════════════════════════════════════════════════════
#   Modal dashboard → Settings → Secrets
#   qdrant-secret:  QDRANT_URL, QDRANT_API_KEY
#   hf-secret:      HF_TOKEN

SECRETS = [
    modal.Secret.from_name("qdrant-secret"),
    modal.Secret.from_name("hf-secret"),
]

# ═══════════════════════════════════════════════════════════════════════════════
# 4.  PIPELINE CONFIG
# ═══════════════════════════════════════════════════════════════════════════════

COLLECTIONS = [
    "seerah_passages",           # ~0.8 GB   ─┐
    "usul_fiqh",                 # ~0.9 GB    │ small
    "spirituality_passages",     # ~1.1 GB   ─┘
    "aqeedah_passages",          # ~1.8 GB   ─┐
    "arabic_language_passages",  # ~2.3 GB    │ medium
    "quran_tafsir",              # ~5.2 GB    │
    "islamic_history_passages",  # ~6.0 GB   ─┘
    "general_islamic",           # ~6.5 GB   ─┐
    "fiqh_passages",             # ~7.0 GB    │ large
    "hadith_passages",           # ~11.0 GB  ─┘
]


HF_DATASET_REPO = "Kandil7/Athar-Datasets"
HF_BACKUP_REPO  = "Kandil7/Athar-Embeddings"
EMBED_MODEL_ID  = "BAAI/bge-m3"

# ─────────────────────────────────────────────────────────────────────────────
# GPU → BATCH_SIZE mapping  (match this to your gpu= choice above)
#
#   gpu="L4"       → BATCH_SIZE = 256   (24 GB VRAM)
#   gpu="L40S"     → BATCH_SIZE = 512   (48 GB VRAM)  ← 2× throughput boost
#   gpu="A100-40GB"→ BATCH_SIZE = 512
#   gpu="A100-80GB"→ BATCH_SIZE = 1024
# ─────────────────────────────────────────────────────────────────────────────

# ✅  CONFIG A – L4 default (max_length=512, best for Arabic Islamic texts)
MAX_LENGTH  = 512    # 95%+ of passages fit in 512 tokens
BATCH_SIZE  = 256    # safe for L4 (24 GB); change to 512 for L40S/A100

# ─────────────────────────────────────────────────────────────────────────────
# ⬜  CONFIG A2 – L40S / A100 (same max_length, larger batch → 2× throughput)
#     Requires:  gpu="L40S" or gpu="A100-40GB"
# ─────────────────────────────────────────────────────────────────────────────
# MAX_LENGTH = 512
# BATCH_SIZE = 512

# ─────────────────────────────────────────────────────────────────────────────
# ⬜  CONFIG B – longer context (uncomment if passages exceed 512 tokens)
#     ⚠️  DO NOT mix max_length=4096 + batch_size>16  →  OOM guaranteed
# ─────────────────────────────────────────────────────────────────────────────
# MAX_LENGTH = 4096
# BATCH_SIZE = 16    # L4 / L40S safe at 4096 tokens

# ─────────────────────────────────────────────────────────────────────────────
# ⬜  CONFIG C – BGE-M3 native max (very slow; rarely needed)
# ─────────────────────────────────────────────────────────────────────────────
# MAX_LENGTH = 8192
# BATCH_SIZE = 4

EMBED_DIM           = 1024   # BGE-M3 dense output dimension
QDRANT_UPLOAD_BATCH = 256    # points per Qdrant upsert call


# ═══════════════════════════════════════════════════════════════════════════════
# 5.  HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _log_progress(
    collection: str, status: str, elapsed_sec: float, passage_count: int
) -> None:
    """Append one JSON line to the shared progress log on the volume."""
    os.makedirs(EMBEDDINGS_DIR, exist_ok=True)
    entry = {
        "collection":      collection,
        "status":          status,
        "passage_count":   passage_count,
        "elapsed_minutes": round(elapsed_sec / 60, 2),
        "timestamp":       datetime.now(timezone.utc).isoformat(),
    }
    with open(PROGRESS_FILE, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _already_embedded(collection_name: str) -> bool:
    """Return True if both output files already exist (resume guard)."""
    emb = f"{EMBEDDINGS_DIR}/{collection_name}_embeddings.npy"
    pas = f"{EMBEDDINGS_DIR}/{collection_name}_passages.jsonl"
    return os.path.exists(emb) and os.path.exists(pas)


# ═══════════════════════════════════════════════════════════════════════════════
# 6.  STEP 1 – DOWNLOAD DATASET  (CPU, no GPU needed)
# ═══════════════════════════════════════════════════════════════════════════════

@app.function(
    image=image,
    volumes={VOLUME_PATH: volume},
    secrets=SECRETS,
    timeout=7200,    # 2 h – large dataset
    memory=8192,
    cpu=4,
)
def download_dataset() -> None:
    """
    Pull Athar-Datasets from HuggingFace onto the shared volume.
    snapshot_download skips files already present → safe to re-run.
    """
    from huggingface_hub import snapshot_download

    os.makedirs(COLLECTIONS_DIR, exist_ok=True)
    os.makedirs(EMBEDDINGS_DIR, exist_ok=True)

    hf_token = os.environ.get("HF_TOKEN")

    print(f"📥  Downloading {HF_DATASET_REPO} …")
    print("    (hf_transfer enabled – expect 200-400 MB/s)\n")

    snapshot_download(
        repo_id=HF_DATASET_REPO,
        local_dir=f"{VOLUME_PATH}/athar-collections",
        repo_type="dataset",
        token=hf_token,
        ignore_patterns=["*.git*", "__pycache__"],
    )

    volume.commit()   # flush so subsequent functions see the files immediately

    found = (
        [f for f in os.listdir(COLLECTIONS_DIR) if f.endswith(".jsonl.gz")]
        if os.path.isdir(COLLECTIONS_DIR) else []
    )
    print(f"\n✅  Download complete. Found {len(found)} collection file(s):")
    for f in sorted(found):
        size_mb = os.path.getsize(f"{COLLECTIONS_DIR}/{f}") / 1e6
        print(f"    {f:<50}  {size_mb:>8.1f} MB")


# ═══════════════════════════════════════════════════════════════════════════════
# 7.  STEP 2 – EMBED ALL COLLECTIONS  (L4 GPU, model loaded ONCE)
# ═══════════════════════════════════════════════════════════════════════════════

@app.cls(
    # ── GPU choice ──────────────────────────────────────────────────────────
    # Pick ONE option below.  Comment out the others.
    #
    # ★ L4       → cheapest   (~$8.27,  ~10h)   batch=256  ← DEFAULT
    # ✦ L40S     → 2.4× faster, same cost (~$8.43, ~4h)   batch=512
    #   A100-40GB → fastest value (~$7.57,  ~4h)  batch=512
    #   A100-80GB → absolute fastest (~$6.15, ~3h) batch=1024
    #
    gpu="L4",          # ★ DEFAULT – best value
    # gpu="L40S",      # ✦ FASTER  – uncomment to switch (also set BATCH_SIZE=512 below)
    # gpu="A100-40GB", # FASTEST VALUE – uncomment to switch

    image=image,
    volumes={VOLUME_PATH: volume},
    secrets=SECRETS,

    # L4 full pipeline ≈ 11 h; 14 h gives comfortable margin for large collections
    timeout=50400,       # 14 hours  (Modal max = 24 h)

    memory=32768,        # 32 GB RAM – needed to load hadith_passages into Python
    cpu=8,
    retries=modal.Retries(
        max_retries=1,
        backoff_coefficient=2.0,
        initial_delay=10.0,
    ),
)
class Embedder:
    """
    GPU worker: loads BGE-M3 ONCE via @modal.enter(), then embeds all
    10 collections sequentially inside a single container invocation.

    Why one container?  Model load = ~2 min.  10 collections = 20 min saved.
    """

    # ── Model setup  (runs once when the container starts) ──────────────────
    @modal.enter()
    def load_model(self) -> None:
        import torch
        from transformers import AutoTokenizer, AutoModel

        hf_token = os.environ.get("HF_TOKEN")
        print("🤖  Loading BAAI/bge-m3 …")

        self.tokenizer = AutoTokenizer.from_pretrained(
            EMBED_MODEL_ID, token=hf_token
        )
        self.model = AutoModel.from_pretrained(
            EMBED_MODEL_ID, token=hf_token
        )

        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        # FP16: halves VRAM (1.06 GB vs 2.12 GB), no accuracy loss for retrieval
        self.model = self.model.to(self.device).half().eval()

        params = sum(p.numel() for p in self.model.parameters())
        vram   = self.model.get_memory_footprint() / 1e9 if hasattr(
            self.model, "get_memory_footprint") else "~1.06"

        print(
            f"✅  BGE-M3 ready  │  device={self.device.upper()}  "
            f"│  FP16  │  {params:,} params  │  VRAM≈{vram:.2f} GB"
        )
        print(
            f"📐  Config: MAX_LENGTH={MAX_LENGTH}, BATCH_SIZE={BATCH_SIZE}  "
            f"(L4 24 GB can handle this comfortably)"
        )

    # ── Internal: embed one collection ──────────────────────────────────────
    def _embed_one(self, collection_name: str) -> dict:
        import torch
        import numpy as np
        from tqdm import tqdm

        volume.reload()   # pick up files written by download_dataset()

        # ── Resume guard ─────────────────────────────────────────────────────
        if _already_embedded(collection_name):
            print(f"⏭️   {collection_name}: already embedded – skipping.")
            return {"status": "skipped", "collection": collection_name, "count": 0}

        filepath_gz = f"{COLLECTIONS_DIR}/{collection_name}.jsonl.gz"
        if not os.path.exists(filepath_gz):
            print(f"⚠️   {collection_name}: source file missing → {filepath_gz}")
            return {"status": "missing", "collection": collection_name, "count": 0}

        # ── Load passages ─────────────────────────────────────────────────────
        sep = "─" * 68
        print(f"\n{sep}\n📖  {collection_name}\n{sep}")
        print("    Loading passages …")

        passages = []
        with gzip.open(filepath_gz, "rt", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    passages.append(json.loads(line))
                except json.JSONDecodeError:
                    continue   # silently skip malformed lines

        print(f"    Loaded {len(passages):,} passages")

        if not passages:
            _log_progress(collection_name, "empty", 0, 0)
            return {"status": "empty", "collection": collection_name, "count": 0}

        _log_progress(collection_name, "started", 0, len(passages))
        contents = [str(p.get("content") or "") for p in passages]

        # ── Embed in batches ──────────────────────────────────────────────────
        all_embeddings = []
        t0 = time.time()

        for i in tqdm(
            range(0, len(contents), BATCH_SIZE),
            desc=f"    ⚡ {collection_name}",
            unit="batch",
            ncols=80,
        ):
            batch = contents[i : i + BATCH_SIZE]

            encoded = self.tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=MAX_LENGTH,
                return_tensors="pt",
            ).to(self.device)

            with torch.no_grad():
                outputs = self.model(**encoded)
                # CLS-token pooling: standard for BGE-M3 dense retrieval
                embs = outputs.last_hidden_state[:, 0, :]
                # L2-normalise: cosine similarity == dot product in Qdrant
                embs = torch.nn.functional.normalize(embs, p=2, dim=1)

            # Store as float32 (FP32) for lossless on-disk precision
            all_embeddings.append(embs.cpu().float().numpy())

            # Periodic GPU cache flush every 200 batches
            if (i // BATCH_SIZE) % 200 == 0 and i > 0:
                torch.cuda.empty_cache()

        elapsed   = time.time() - t0
        emb_array = np.concatenate(all_embeddings, axis=0)  # (N, 1024)

        speed = len(passages) / elapsed
        print(
            f"\n    ✅  {len(passages):,} vectors  │  shape={emb_array.shape}  │  "
            f"{elapsed/60:.1f} min  │  {speed:.0f} passages/sec"
        )

        # ── Save to volume ────────────────────────────────────────────────────
        os.makedirs(EMBEDDINGS_DIR, exist_ok=True)
        emb_path = f"{EMBEDDINGS_DIR}/{collection_name}_embeddings.npy"
        pas_path = f"{EMBEDDINGS_DIR}/{collection_name}_passages.jsonl"

        np.save(emb_path, emb_array)

        # JSONL: memory-safe for 7 M+ passages (no single giant JSON object)
        with open(pas_path, "w", encoding="utf-8") as fh:
            for p in passages:
                fh.write(json.dumps(p, ensure_ascii=False) + "\n")

        volume.commit()   # flush so upload step can read without a restart

        _log_progress(collection_name, "completed", elapsed, len(passages))
        torch.cuda.empty_cache()

        return {
            "status":     "completed",
            "collection": collection_name,
            "count":      len(passages),
            "elapsed":    elapsed,
            "shape":      list(emb_array.shape),
        }

    # ── Public method: embed everything in ONE container call ────────────────
    @modal.method()
    def embed_all(self, collections: list = COLLECTIONS) -> list:
        """
        Process every collection sequentially.
        BGE-M3 stays loaded the entire time → no reload overhead.
        """
        results     = []
        total_start = time.time()

        for coll in collections:
            result = self._embed_one(coll)
            results.append(result)
            icon = "✅" if result["status"] == "completed" else (
                   "⏭️" if result["status"] == "skipped"   else "❌"
            )
            print(f"\n{icon}  {coll:<38}  [{result['status']}]")

        total_elapsed = time.time() - total_start
        completed     = [r for r in results if r["status"] == "completed"]
        total_passages = sum(r["count"] for r in completed)

        sep = "═" * 68
        print(f"\n{sep}")
        print(f"🎉  EMBEDDING DONE")
        print(f"    Completed  : {len(completed)}/{len(collections)} collections")
        print(f"    Passages   : {total_passages:,}")
        print(f"    Wall time  : {total_elapsed/3600:.2f} h")
        gpu_prices = {"L4": 0.80, "L40S": 1.95, "A10G": 1.10,
                      "A100-40GB": 2.10, "A100-80GB": 2.50}
        gpu_name   = os.environ.get("MODAL_GPU_TYPE", "L4")
        gpu_price  = gpu_prices.get(gpu_name, 0.80)
        print(f"    GPU cost    : ${total_elapsed/3600 * gpu_price:.2f}  ({gpu_name} @ ${gpu_price}/h)")
        print(f"{sep}")

        return results


# ═══════════════════════════════════════════════════════════════════════════════
# 8.  STEP 3 – UPLOAD TO QDRANT  (CPU, runs in parallel via .map())
# ═══════════════════════════════════════════════════════════════════════════════

@app.function(
    image=image,
    volumes={VOLUME_PATH: volume},
    secrets=SECRETS,
    timeout=7200,    # 2 h per collection
    memory=16384,    # 16 GB – numpy for hadith_passages can exceed 5 GB
    cpu=4,
)
def upload_to_qdrant(collection_name: str) -> dict:
    """
    Upload one collection's embeddings + metadata to Qdrant.
    Uses upsert → idempotent / safe to re-run.
    """
    import numpy as np
    from tqdm import tqdm
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct

    volume.reload()

    qdrant_url = os.environ["QDRANT_URL"]
    qdrant_key = os.environ.get("QDRANT_API_KEY")

    emb_path = f"{EMBEDDINGS_DIR}/{collection_name}_embeddings.npy"
    pas_path = f"{EMBEDDINGS_DIR}/{collection_name}_passages.jsonl"

    if not os.path.exists(emb_path):
        print(f"⚠️   {collection_name}: embeddings not found – skipping.")
        return {"status": "missing", "collection": collection_name, "count": 0}

    # ── Load ──────────────────────────────────────────────────────────────────
    print(f"\n📤  Uploading: {collection_name}")
    embeddings = np.load(emb_path)   # (N, 1024) float32

    passages = []
    with open(pas_path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    passages.append(json.loads(line))
                except json.JSONDecodeError:
                    passages.append({})

    print(f"    Passages  : {len(passages):,}")
    print(f"    Embeddings: {embeddings.shape}")

    # ── Sanity checks ─────────────────────────────────────────────────────────
    if len(embeddings) != len(passages):
        raise ValueError(
            f"Shape mismatch for '{collection_name}': "
            f"{len(embeddings)} embeddings vs {len(passages)} passages. "
            "Re-embed this collection before uploading."
        )
    if embeddings.ndim != 2:
        raise ValueError(
            f"Expected 2-D array for '{collection_name}', got {embeddings.shape}"
        )

    vector_size = int(embeddings.shape[1])

    # ── Qdrant setup ──────────────────────────────────────────────────────────
    client = QdrantClient(url=qdrant_url, api_key=qdrant_key, timeout=120)

    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE,
            ),
        )
        print(f"    ✅  Created Qdrant collection (dim={vector_size})")
    else:
        print(f"    ℹ️   Collection exists – upserting into it")

    # ── Upload ────────────────────────────────────────────────────────────────
    t0 = time.time()

    for start in tqdm(
        range(0, len(passages), QDRANT_UPLOAD_BATCH),
        desc=f"    Uploading {collection_name}",
        unit="batch",
        ncols=80,
    ):
        end       = min(start + QDRANT_UPLOAD_BATCH, len(passages))
        batch_emb = embeddings[start:end]
        batch_pas = passages[start:end]

        points = [
            PointStruct(
                id=start + idx,
                vector=batch_emb[idx].tolist(),
                payload={
                    "content":      p.get("content", ""),
                    "book_id":      p.get("book_id"),
                    "title":        p.get("title", ""),
                    "author":       p.get("author", ""),
                    "author_death": p.get("author_death"),
                    "page":         p.get("page"),
                    "chapter":      p.get("chapter", ""),
                    "section":      p.get("section", ""),
                    "category":     p.get("category", ""),
                    "collection":   collection_name,
                },
            )
            for idx, p in enumerate(batch_pas)
        ]

        client.upsert(collection_name=collection_name, points=points)

    elapsed = time.time() - t0
    print(
        f"    ✅  {len(passages):,} vectors → Qdrant  "
        f"({elapsed/60:.1f} min, {len(passages)/elapsed:.0f} pts/sec)"
    )
    return {
        "status": "completed", "collection": collection_name,
        "count": len(passages), "elapsed": elapsed,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 9.  STEP 4 – BACKUP TO HUGGINGFACE  (CPU, runs in parallel via .map())
# ═══════════════════════════════════════════════════════════════════════════════

@app.function(
    image=image,
    volumes={VOLUME_PATH: volume},
    secrets=SECRETS,
    timeout=7200,
    memory=8192,
    cpu=4,
)
def backup_to_hf(collection_name: str) -> dict:
    """
    Gzip-compress and upload one collection's .npy + .jsonl to HF Hub.
    Saves ~60-70% storage.  Idempotent (upload_file overwrites).
    """
    from huggingface_hub import HfApi, login

    volume.reload()

    hf_token = os.environ["HF_TOKEN"]
    login(token=hf_token, add_to_git_credential=False)
    api = HfApi()

    try:
        api.create_repo(HF_BACKUP_REPO, repo_type="dataset", exist_ok=True)
    except Exception as exc:
        print(f"    ⚠️  Repo create warning (safe): {exc}")

    backed_up = 0
    for suffix in ("_embeddings.npy", "_passages.jsonl"):
        src = f"{EMBEDDINGS_DIR}/{collection_name}{suffix}"
        if not os.path.exists(src):
            print(f"    ⚠️  Not found: {src} – skipping.")
            continue

        gz_path       = f"/tmp/{collection_name}{suffix}.gz"
        original_mb   = os.path.getsize(src) / 1e6
        print(f"    📦  Compressing {collection_name}{suffix}  ({original_mb:.0f} MB) …")

        with (
            open(src, "rb") as fi,
            gzip.open(gz_path, "wb", compresslevel=6) as fo
        ):
            shutil.copyfileobj(fi, fo)

        compressed_mb = os.path.getsize(gz_path) / 1e6
        print(f"        {original_mb:.0f} MB → {compressed_mb:.0f} MB  "
              f"({compressed_mb/original_mb:.0%})")

        try:
            api.upload_file(
                path_or_fileobj=gz_path,
                path_in_repo=f"backup/{collection_name}{suffix}.gz",
                repo_id=HF_BACKUP_REPO,
                repo_type="dataset",
            )
            print(f"        ✅  Uploaded to HF")
            backed_up += 1
        except Exception as exc:
            print(f"        ❌  Upload failed: {exc}")

        os.remove(gz_path)

    return {
        "status":         "backed_up" if backed_up > 0 else "failed",
        "collection":     collection_name,
        "files_uploaded": backed_up,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 10.  STEP 5 – VERIFY QDRANT
# ═══════════════════════════════════════════════════════════════════════════════

@app.function(image=image, secrets=SECRETS, timeout=120)
def verify_qdrant() -> dict:
    """Quick sanity check: print vector counts for every collection."""
    from qdrant_client import QdrantClient

    client = QdrantClient(
        url=os.environ["QDRANT_URL"],
        api_key=os.environ.get("QDRANT_API_KEY"),
        timeout=30,
    )

    sep = "═" * 68
    print(f"\n{sep}\n📊  Qdrant Collections Status\n{sep}")

    total    = 0
    statuses = {}

    for name in COLLECTIONS:
        try:
            info = client.get_collection(name)
            cnt  = info.points_count or 0
            total += cnt
            statuses[name] = {"count": cnt, "status": str(info.status)}
            print(f"  ✅  {name:<38}  {cnt:>10,} vectors  │  {info.status}")
        except Exception as exc:
            statuses[name] = {"count": 0, "status": f"ERROR: {exc}"}
            print(f"  ❌  {name:<38}  {str(exc)[:40]}")

    print(f"{'─'*68}")
    print(f"      {'TOTAL':<37}  {total:>10,} vectors")
    print(f"{sep}\n")

    return {"total_vectors": total, "collections": statuses}


# ═══════════════════════════════════════════════════════════════════════════════
# 11.  TEST SEMANTIC SEARCH  (end-to-end sanity check)
# ═══════════════════════════════════════════════════════════════════════════════

@app.function(gpu="L4",  # change to "L40S" if that's your embed GPU
              image=image, secrets=SECRETS, timeout=120)
def test_search(
    query: str = "ما حكم صلاة الجماعة؟",
    collection: str = "fiqh_passages",
    top_k: int = 5,
) -> list:
    """
    Embed a query on L4 and search Qdrant.
    Usage:
        modal run athar_embed_modal.py::test_search \\
            --query "ما حكم صلاة الجماعة؟"
    """
    import torch
    from transformers import AutoTokenizer, AutoModel
    from qdrant_client import QdrantClient

    hf_token = os.environ.get("HF_TOKEN")
    tok = AutoTokenizer.from_pretrained(EMBED_MODEL_ID, token=hf_token)
    mdl = AutoModel.from_pretrained(EMBED_MODEL_ID, token=hf_token)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    mdl = mdl.to(device).half().eval()

    encoded = tok(
        [query], padding=True, truncation=True,
        max_length=MAX_LENGTH, return_tensors="pt",
    ).to(device)

    with torch.no_grad():
        out   = mdl(**encoded)
        q_vec = torch.nn.functional.normalize(
            out.last_hidden_state[:, 0, :], p=2, dim=1
        ).cpu().float().numpy()[0]

    client  = QdrantClient(
        url=os.environ["QDRANT_URL"],
        api_key=os.environ.get("QDRANT_API_KEY"),
    )
    results = client.search(
        collection_name=collection,
        query_vector=q_vec.tolist(),
        limit=top_k,
    )

    print(f"\n🔍  Query      : {query}")
    print(f"📚  Collection : {collection}")
    print("─" * 68)

    hits = []
    for i, r in enumerate(results, 1):
        pl = r.payload or {}
        print(f"\n[{i}]  score={r.score:.4f}")
        print(f"     Author  : {pl.get('author', '–')}")
        print(f"     Book    : {pl.get('title', '–')}")
        print(f"     Chapter : {pl.get('chapter', '–')}")
        print(f"     Content : {str(pl.get('content',''))[:200]}…")
        hits.append({"score": r.score, "payload": pl})

    return hits


# ═══════════════════════════════════════════════════════════════════════════════
# 12.  LOCAL ENTRYPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.local_entrypoint()
def main():
    """
    Full pipeline: download → embed → upload to Qdrant → backup to HF → verify
    Run:  modal run athar_embed_modal.py
    """
    print("\n" + "═"*68)
    print("🕌  ATHAR – Full Embedding Pipeline  │  GPU: L4 ($0.80/hr)")
    print("═"*68 + "\n")

    # Step 1: Download
    print("STEP 1/5 ─ Download dataset from HuggingFace\n")
    download_dataset.remote()

    # Step 2: Embed (all collections, model loaded once on L4)
    print("\nSTEP 2/5 ─ Embed with BAAI/bge-m3 on L4\n")
    embedder = Embedder()
    results  = embedder.embed_all.remote(COLLECTIONS)
    for r in results:
        icon = "✅" if r["status"] == "completed" else (
               "⏭️" if r["status"] == "skipped"   else "❌")
        print(f"  {icon}  {r['collection']:<38}  [{r['status']}]")

    # Step 3: Upload to Qdrant (parallel)
    print("\nSTEP 3/5 ─ Upload to Qdrant\n")
    for r in upload_to_qdrant.map(COLLECTIONS, order_outputs=True):
        icon = "✅" if r["status"] == "completed" else "❌"
        print(f"  {icon}  {r['collection']:<38}  [{r['status']}]")

    # Step 4: Backup to HF (parallel)
    print("\nSTEP 4/5 ─ Backup embeddings to HuggingFace\n")
    for r in backup_to_hf.map(COLLECTIONS, order_outputs=True):
        icon = "✅" if r["status"] == "backed_up" else "❌"
        print(f"  {icon}  {r['collection']:<38}  [{r['status']}]")

    # Step 5: Verify
    print("\nSTEP 5/5 ─ Verify Qdrant collections\n")
    verify_qdrant.remote()

    print("\n🎉  Pipeline complete!")
    print("    L4:   ~$8.27 / ~10h  (default)")
    print("    L40S: ~$8.43 /  ~4h  (if you used gpu=L40S)")


@app.local_entrypoint()
def embed_only():
    """
    Embed only (skip download if collections already on volume).
    Run:  modal run athar_embed_modal.py::embed_only
    """
    print("🚀  Embedding only (download skipped)\n")
    embedder = Embedder()
    results  = embedder.embed_all.remote(COLLECTIONS)
    for r in results:
        icon = "✅" if r["status"] == "completed" else (
               "⏭️" if r["status"] == "skipped"   else "❌")
        print(f"  {icon}  {r['collection']:<38}  [{r['status']}]")


@app.local_entrypoint()
def upload_only():
    """
    Re-upload pre-computed embeddings to Qdrant (skip embed step).
    Run:  modal run athar_embed_modal.py::upload_only
    """
    print("🚀  Upload only (embed step skipped)\n")
    for r in upload_to_qdrant.map(COLLECTIONS, order_outputs=True):
        icon = "✅" if r["status"] == "completed" else "❌"
        print(f"  {icon}  {r['collection']:<38}  [{r['status']}]")


@app.local_entrypoint()
def verify():
    """
    Verify Qdrant collection status.
    Run:  modal run athar_embed_modal.py::verify
    """
    verify_qdrant.remote()
