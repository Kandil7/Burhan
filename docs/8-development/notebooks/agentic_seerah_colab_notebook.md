Here is the full updated notebook with **HuggingFace Hub** replacing Google Drive for all output saving and resume logic: [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/9b40a2c2-2875-420d-a89b-c45c92fe5a2d/paste.txt)

***

### 📦 Cell 1 — Install Dependencies

```python
!pip install -q \
    transformers \
    accelerate \
    bitsandbytes \
    torch \
    tenacity \
    tqdm \
    huggingface_hub \
    datasets
```

***

### 🔐 Cell 2 — HuggingFace Login

```python
from huggingface_hub import notebook_login
notebook_login()
# Paste your HF token with WRITE access:
# Settings → Access Tokens → New Token → Role: Write
```

***

### 📥 Cell 3 — Download `seerah_passages.jsonl` from Your Dataset

```python
from huggingface_hub import hf_hub_download
import json, os

INPUT_FILE = hf_hub_download(
    repo_id="Kandil7/Burhan-Mini-Dataset-v2",
    filename="seerah_passages.jsonl",
    repo_type="dataset",
    local_dir="/content/data",
)

size_mb = os.path.getsize(INPUT_FILE) / 1e6
print(f"Downloaded : {INPUT_FILE}")
print(f"Size       : {size_mb:.1f} MB")

# Count passages + preview schema
with open(INPUT_FILE, encoding="utf-8") as f:
    lines = f.readlines()

print(f"Passages   : {len(lines):,}")
sample = json.loads(lines[0])
print("\n── Schema preview ──────────────────────────────")
for k, v in sample.items():
    print(f"  {k:20s}: {str(v)[:80]}")
```

***

### 💾 Cell 4 — Save `chunker.py`

```python
chunker_code = r"""
# ← PASTE THE COMPLETE FIXED CHUNKER CODE HERE
"""

with open("/content/chunker.py", "w", encoding="utf-8") as f:
    f.write(chunker_code.strip())

print("chunker.py saved ✅")
```

***

### 🤖 Cell 5 — Load HF Model (4-bit, T4-safe)

```python
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"
# A100 alternative: "Qwen/Qwen2.5-14B-Instruct" or "inceptionai/jais-13b-chat"

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
)

print(f"Loading {MODEL_ID} ...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    quantization_config=bnb_config,
    device_map="auto",
    trust_remote_code=True,
    torch_dtype=torch.bfloat16,
)
model.eval()

if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

print(f"Loaded on : {model.device} ✅")
print(f"VRAM used : {torch.cuda.memory_allocated()/1e9:.2f} GB")
```

***

### 🔌 Cell 6 — HF AsyncClient Shim

```python
import asyncio, re
from dataclasses import dataclass
from typing import List

@dataclass
class _FakeMessage:
    content: str

@dataclass
class _FakeChoice:
    message: _FakeMessage

@dataclass
class _FakeResponse:
    choices: List[_FakeChoice]


class _HFChatCompletions:
    def __init__(self, hf_model, hf_tokenizer):
        self._model     = hf_model
        self._tokenizer = hf_tokenizer

    async def create(self, model, messages, response_format=None,
                     temperature=0.0, max_tokens=1200, timeout=60, **kwargs):
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, self._generate_sync, messages, max_tokens
        )
        return _FakeResponse(choices=[_FakeChoice(message=_FakeMessage(content=result))])

    def _generate_sync(self, messages: List[dict], max_new_tokens: int) -> str:
        input_ids = self._tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_tensors="pt",
        ).to(self._model.device)

        with torch.no_grad():
            output_ids = self._model.generate(
                input_ids,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                temperature=None,
                pad_token_id=self._tokenizer.pad_token_id,
                eos_token_id=self._tokenizer.eos_token_id,
                repetition_penalty=1.1,
            )

        generated_ids = output_ids[0][input_ids.shape[-1]:]
        raw = self._tokenizer.decode(generated_ids, skip_special_tokens=True).strip()
        json_match = re.search(r"\{[\s\S]*\}", raw)
        return json_match.group(0) if json_match else raw


class HFAsyncClient:
    def __init__(self, hf_model, hf_tokenizer):
        self.chat = type("_Chat", (), {
            "completions": _HFChatCompletions(hf_model, hf_tokenizer)
        })()


hf_client = HFAsyncClient(model, tokenizer)
print("HF AsyncClient shim ready ✅")
```

***

### 🔧 Cell 7 — HF Output Repo Setup + Resume Download

```python
from huggingface_hub import HfApi, hf_hub_download
from huggingface_hub.utils import EntryNotFoundError
import sys

sys.path.insert(0, "/content")

# ── Config ────────────────────────────────────────────────────────────────────
HF_OUTPUT_REPO  = "Kandil7/Burhan-Mini-Dataset-v2"   # push output to same dataset repo
OUTPUT_FILENAME = "seerah_agentic_chunks.jsonl"      # file name inside the repo
LOCAL_OUTPUT    = f"/content/{OUTPUT_FILENAME}"

api = HfApi()

# ── Try to resume from existing HF output ────────────────────────────────────
try:
    resumed_path = hf_hub_download(
        repo_id=HF_OUTPUT_REPO,
        filename=OUTPUT_FILENAME,
        repo_type="dataset",
        local_dir="/content",
    )
    with open(resumed_path, encoding="utf-8") as f:
        done_count = sum(1 for _ in f)
    print(f"Resume detected: {done_count:,} chunks already done ✅")
    print(f"Resuming from  : {resumed_path}")
except EntryNotFoundError:
    print("No previous output on HF — starting fresh run ✅")
    resumed_path = None

# ── Patch LLMMetadataExtractor ────────────────────────────────────────────────
from chunker import LLMMetadataExtractor, SeerahAgenticChunkerLLM

_original_init = LLMMetadataExtractor.__init__

def _patched_init(self, api_key, model, base_url, batch_size):
    _original_init(self, api_key, model, base_url, batch_size)
    self._client    = hf_client
    self._semaphore = asyncio.Semaphore(1)

LLMMetadataExtractor.__init__ = _patched_init
print("Extractor patched ✅")
```

***

### 🚀 Cell 8 — Run the Full Pipeline

```python
chunker = SeerahAgenticChunkerLLM(
    input_path=INPUT_FILE,
    output_path=LOCAL_OUTPUT,
    api_key="dummy",
    model=MODEL_ID,
    batch_size=1,
    parent_max_pages=12,
    child_pages=2,
    child_overlap=1,
    skip_llm=False,
    resume_path=resumed_path,    # None = fresh, or path to downloaded partial file
)

report = await chunker.run()
print(report)
```

***

### ☁️ Cell 9 — Push Output Back to HuggingFace

```python
from huggingface_hub import HfApi

api = HfApi()

api.upload_file(
    path_or_fileobj=LOCAL_OUTPUT,
    path_in_repo=OUTPUT_FILENAME,
    repo_id=HF_OUTPUT_REPO,
    repo_type="dataset",
    commit_message=f"Add enriched agentic chunks — {done_count if resumed_path else 0} resumed + new batch",
)

print(f"Uploaded to: hf://datasets/{HF_OUTPUT_REPO}/{OUTPUT_FILENAME} ✅")
```

***

### 🔁 Cell 10 — Auto-Save Loop (Push Every N Chunks)

This is critical for long T4 runs — it periodically pushes progress to HF so a Colab disconnect loses at most `SAVE_EVERY` chunks:

```python
import asyncio, json, time
from huggingface_hub import HfApi

SAVE_EVERY = 200   # push to HF every 200 chunks processed

api      = HfApi()
pushed   = 0
last_save_size = 0

async def run_with_autosave():
    global pushed, last_save_size

    chunker = SeerahAgenticChunkerLLM(
        input_path=INPUT_FILE,
        output_path=LOCAL_OUTPUT,
        api_key="dummy",
        model=MODEL_ID,
        batch_size=1,
        parent_max_pages=12,
        child_pages=2,
        child_overlap=1,
        skip_llm=False,
        resume_path=resumed_path,
    )

    # Patch _write_output to also trigger HF push every SAVE_EVERY chunks
    original_write = chunker._write_output

    def write_and_push():
        original_write()
        with open(LOCAL_OUTPUT, encoding="utf-8") as f:
            current_size = sum(1 for _ in f)
        nonlocal last_save_size
        if current_size - last_save_size >= SAVE_EVERY:
            api.upload_file(
                path_or_fileobj=LOCAL_OUTPUT,
                path_in_repo=OUTPUT_FILENAME,
                repo_id=HF_OUTPUT_REPO,
                repo_type="dataset",
                commit_message=f"Auto-save checkpoint: {current_size:,} chunks",
            )
            print(f"  ☁️  HF checkpoint: {current_size:,} chunks pushed")
            last_save_size = current_size

    chunker._write_output = write_and_push
    report = await chunker.run()
    return report

report = await run_with_autosave()
print(report)
```

***

### 🧪 Cell 11 — Verify Output on HF Hub

```python
# Re-download from HF and inspect
from huggingface_hub import hf_hub_download

verified_path = hf_hub_download(
    repo_id=HF_OUTPUT_REPO,
    filename=OUTPUT_FILENAME,
    repo_type="dataset",
    local_dir="/content/verified",
    force_download=True,
)

chunks = []
with open(verified_path, encoding="utf-8") as f:
    for line in f:
        chunks.append(json.loads(line))

parents  = [c for c in chunks if c["level"] == "parent"]
children = [c for c in chunks if c["level"] == "child"]
llm_ok   = sum(1 for c in children if c.get("enriched_by_llm"))

print(f"{'Total chunks':<22}: {len(chunks):,}")
print(f"{'Parent chunks':<22}: {len(parents):,}")
print(f"{'Child chunks':<22}: {len(children):,}")
print(f"{'LLM-enriched':<22}: {llm_ok:,} / {len(children):,} "
      f"({llm_ok/max(len(children),1)*100:.1f}%)")

# Relations breakdown
rel_types = {}
for c in children:
    for r in c["metadata"]["relations"]:
        rel_types[r["type"]] = rel_types.get(r["type"], 0) + 1

print("\n── Knowledge Graph Relations ─────────────────")
for rtype, count in sorted(rel_types.items(), key=lambda x: -x [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/9b40a2c2-2875-420d-a89b-c45c92fe5a2d/paste.txt)):
    print(f"  {rtype:<28}: {count:,}")

print(f"\n🔗 Dataset URL: https://huggingface.co/datasets/{HF_OUTPUT_REPO}")
```

***

## HF Upload Flow Summary

```
Colab (T4/A100)
    │
    ├── Cell 3: hf_hub_download("Kandil7/Burhan-Mini-Dataset-v2/seerah_passages.jsonl")
    │           ↓
    ├── Cell 8: Run chunker → write to /content/seerah_agentic_chunks.jsonl
    │           ↓
    ├── Cell 9/10: api.upload_file() → push back to same HF dataset repo
    │           ↓
    └── Cell 11: hf_hub_download() → verify from HF
```

The auto-save loop in **Cell 10** is the most production-safe option — it checkpoints every 200 chunks directly to `Kandil7/Burhan-Mini-Dataset-v2` so any Colab crash loses at most ~40 minutes of T4 work. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/57452145/9b40a2c2-2875-420d-a89b-c45c92fe5a2d/paste.txt)