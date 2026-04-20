سأكتب لك Notebook كامل، خطوة–بخطوة، تقدر تنسخه مباشرة في Google Colab، مع كل التفاصيل:

- يستخدم `datasets` لتحميل Athar من HF.
- ينظّف النصوص.
- يستخدم HF `transformers` (LLM) لتوليد أسئلة عالية الجودة.
- يبني Athar RAG Evaluation Dataset (لكل collections).
- يرفعه إلى Hugging Face Hub كـdataset جديد.

سأفترض:
- عندك `Kandil7/Athar-Mini-Dataset-v2` و/أو `Kandil7/Athar-Datasets`. [huggingface](https://huggingface.co/datasets/Kandil7/Athar-Datasets)
- عندك حساب HF (username: `Kandil7`).

ضع العنوان في أول خلية:

***

## 🔹 Notebook: Athar RAG Evaluation Dataset (HF Transformers + HF Hub)

### 0. إعداد البيئة + الاتصال بـHugging Face

```python
!pip install -q datasets huggingface_hub transformers accelerate sentencepiece tqdm

import os, json, re, textwrap, random
import torch
from tqdm.auto import tqdm

from datasets import load_dataset, Dataset, DatasetDict
from huggingface_hub import login
```

```python
# ✅ أدخل HF token (لازم يكون عنده write access)
HF_TOKEN = os.getenv("HF_TOKEN")
if HF_TOKEN is None or HF_TOKEN.strip() == "":
    HF_TOKEN = input("أدخل Hugging Face token بصلاحية write: ").strip()

login(HF_TOKEN)

HF_USERNAME = "Kandil7"  # عدّل لو مختلف
```

***

### 1. تحميل Athar Dataset من HF

#### 1.1. Athar Mini (خفيف – ideal للتجارب الأولى)

```python
# Mini dataset (seerah + بعض المجموعات) [web:40]
mini_ds = load_dataset("Kandil7/Athar-Mini-Dataset-v2", split="train")
len(mini_ds), mini_ds[0]
```

#### 1.2. Athar Full (اختياري – ثقيل جدًا)

```python
# ⚠️ اختياري – كبير (ملايين السطور)
# full_ds = load_dataset("Kandil7/Athar-Datasets", split="train")
# len(full_ds), full_ds[0]
```

***

### 2. تنظيف النصوص (موحد لكل collections)

```python
def clean_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = text.replace("\r", " ").replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip()
    # إزالة علامات حواشي من نوع (¬١)
    text = re.sub(r"\(¬\d+\)", "", text)
    return text

def clean_row(row):
    row["content_clean"] = clean_text(row.get("content", ""))
    st = row.get("section_title", "") or ""
    row["section_title_clean"] = clean_text(st)
    # تأكيد وجود collection
    row["collection"] = row.get("collection", "unknown")
    return row

mini_ds_clean = mini_ds.map(clean_row, num_proc=4)
mini_ds_clean[0]
```

> لاحقًا يمكنك تكرار نفس الشيء مع `full_ds`:
> ```python
> # full_ds_clean = full_ds.map(clean_row, num_proc=8)
> ```

***

### 3. اختيار موديل HF LLM وتجهيزه

اختر موديل مناسب للعربية/متعدد اللغات وتعليمات (Instruction):

- مثال: `Qwen/Qwen2.5-7B-Instruct` أو أي موديل آخر تعتمد عليه.

```python
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct"  # عدّل حسب البيئة

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    device_map="auto",
    torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
)

gen_pipe = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    device_map="auto",
)
```

> لو عندك موديلك الخاص (مثلاً `Kandil7/Athar-LLM`)، استخدم اسمه بدلًا من Qwen.

***

### 4. بناء Prompt للـLLM (متخصص للـRAG Evaluation)

```python
def build_hf_prompt(passage: dict) -> str:
    content = passage["content_clean"][:900]
    section = passage.get("section_title_clean") or ""
    book = passage.get("book_title", "")
    collection = passage.get("collection", "")

    system = (
        "أنت نموذج مساعد في إنشاء مجموعة تقييم (evaluation dataset) لنظام RAG عربي "
        "يعتمد على نصوص في السيرة والعلوم الشرعية. "
        "مهمتك توليد أسئلة تساعد على اختبار قدرة النظام على استرجاع المقطع الصحيح والإجابة من النص."
    )

    user = textwrap.dedent(f"""
    النص التالي من مجموعة '{collection}'، من كتاب '{book}'، تحت عنوان فرعي '{section}':

    \"\"\"{content}\"\"\"

    المطلوب:
    - أنشئ بين 2 و 4 أسئلة فهم/استرجاع (retrieval questions) باللغة العربية.
    - يجب أن:
      * تعتمد فقط على المعلومات الموجودة في النص.
      * تساعد على تقييم قدرة نظام RAG على استرجاع هذا المقطع.
      * تتنوع بين:
          - سؤال عن الفكرة أو الحدث الرئيسي.
          - سؤال عن العبرة أو الدرس المستفاد.
          - (اختياري) سؤال عن تفاصيل محددة (أسماء، أماكن، أزمنة) إن كانت موجودة.
    - لا تذكر اسم الكتاب أو المؤلف أو رقم الصفحة أو اسم المجموعة في نص السؤال.
    - لا تذكر الإجابة.
    - لا تضف أي شرح خارج JSON.

    أعد النتيجة في صيغة JSON فقط بالشكل التالي:

    {{
      "questions": [
        "سؤال 1 ...؟",
        "سؤال 2 ...؟"
      ]
    }}
    """).strip()

    # تنسيق شبيه بـchat لمعظم موديلات instruct
    prompt = f"<|system|>\n{system}\n<|user|>\n{user}\n<|assistant|>\n"
    return prompt
```

***

### 5. دالة توليد الأسئلة باستخدام `transformers`

```python
def hf_llm_generate_questions_for_passage(passage: dict, max_new_tokens: int = 512):
    prompt = build_hf_prompt(passage)

    out = gen_pipe(
        prompt,
        max_new_tokens=max_new_tokens,
        do_sample=True,
        temperature=0.4,
        top_p=0.9,
        eos_token_id=tokenizer.eos_token_id,
    )[0]["generated_text"]

    # خُد الجزء بعد <|assistant|>
    if "<|assistant|>" in out:
        out = out.split("<|assistant|>")[-1].strip()

    text = out.replace("```json", "").replace("```", "").strip()

    # محاولة parse JSON
    questions = []
    try:
        obj = json.loads(text)
        qs = obj.get("questions", [])
        if isinstance(qs, list):
            questions = [q.strip() for q in qs if isinstance(q, str)]
    except json.JSONDecodeError:
        # fallback: استخرج سطور تنتهي بعلامة استفهام
        candidates = re.findall(r".+؟", text)
        questions = [c.strip() for c in candidates]

    # فلترة الأسئلة القصيرة/الغريبة
    questions = [q for q in questions if len(q) > 10 and "}" not in q and "{" not in q]
    # حدد 4 كحد أقصى
    return questions[:4]
```

> مهم: راقب أول 2–3 مخرجات يدويًا لتتأكد إن الموديل متقيّد بالـJSON قدر الإمكان؛ لو لأ، ممكن نزيد explicit formatting/قيود.

***

### 6. Strategy لكل Collection (توزيع الأسئلة)

نفترض أن Athar عنده collections زي: `seerah_passages`, `fiqh_passages`, `aqeedah_passages`, `hadith_passages`, إلخ.

نحدد لكل واحدة **كم سؤال** نريد.

```python
# لو معاك Athar-Mini: هتشتغل غالبًا على seerah وبعض المجموعات
collections_in_mini = set(mini_ds_clean["collection"])
collections_in_mini
```

مثال لخطة توزيع:

```python
# مثال: حد أقصى للأسئلة per collection (لـMini)
MAX_PER_COLLECTION = {
    "seerah_passages": 1000,
    "fiqh_passages": 500,
    "aqeedah_passages": 500,
    "hadith_passages": 800,
    "unknown": 200,   # أي حاجة غير مصنفة
}
DEFAULT_MAX = 300
```

***

### 7. بناء RAG Eval Records باستخدام HF LLM

```python
def build_eval_with_hf_llm(ds, max_per_collection_map=None, default_max=300):
    if max_per_collection_map is None:
        max_per_collection_map = {}

    counts = {}
    records = []

    for row in tqdm(ds, total=len(ds)):
        coll = row.get("collection", "unknown")
        max_allowed = max_per_collection_map.get(coll, default_max)

        counts.setdefault(coll, 0)
        if counts[coll] >= max_allowed:
            continue

        if not row.get("content_clean"):
            continue

        questions = hf_llm_generate_questions_for_passage(row)
        if not questions:
            continue

        for q in questions:
            if counts[coll] >= max_allowed:
                break

            gold = [{
                "collection": coll,
                "book_id": row.get("book_id"),
                "page_number": row.get("page_number"),
                "section_title": row.get("section_title_clean"),
                "content_snippet": row["content_clean"][:400],
                "author": row.get("author", ""),
                "book_title": row.get("book_title", ""),
            }]

            rec = {
                "query": q,
                "collection": coll,
                "book_id": row.get("book_id"),
                "page_number": row.get("page_number"),
                "gold_passages": gold,
                "difficulty": "hf-llm-single-hop",
                "generation_model": MODEL_NAME,
            }
            records.append(rec)
            counts[coll] += 1

    print("Counts per collection:", counts)
    print("Total eval records:", len(records))
    return records, counts
```

تشغيله على **Mini**:

```python
MAX_PER_COLLECTION = {
    "seerah_passages": 800,
    "fiqh_passages": 400,
    "aqeedah_passages": 400,
    "hadith_passages": 600,
    "unknown": 200,
}
eval_records_mini_hf, counts_mini = build_eval_with_hf_llm(
    mini_ds_clean,
    max_per_collection_map=MAX_PER_COLLECTION,
    default_max=200,
)
len(eval_records_mini_hf), counts_mini
```

> على Colab: استخدم أرقام صغيرة في البداية (مثلاً 100 أو 200 لكل collection) لتختبر السرعة والجودة، ثم زوّد.

***

### 8. حفظ Athar-RAG-Eval JSONL ورفع لـHF

#### 8.1. حفظ محليًا

```python
os.makedirs("output", exist_ok=True)

eval_mini_path = "output/Athar-RAG-Eval-HFLLM-Mini-v1.jsonl"
with open(eval_mini_path, "w", encoding="utf-8") as f:
    for rec in eval_records_mini_hf:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

eval_mini_path
```

#### 8.2. تحويله لـHF Dataset + رفعه

```python
eval_mini_ds = Dataset.from_json(eval_mini_path)
eval_mini_ds
```

```python
EVAL_REPO_NAME = f"{HF_USERNAME}/Athar-RAG-Eval-HFLLM-Mini-v1"

eval_mini_ds.push_to_hub(EVAL_REPO_NAME, token=HF_TOKEN)
print("🚀 Pushed to:", f"https://huggingface.co/datasets/{EVAL_REPO_NAME}")
```

#### 8.3. (اختياري) تقسيم per collection داخل نفس repo

```python
by_coll = {}
for rec in eval_records_mini_hf:
    coll = rec["collection"]
    by_coll.setdefault(coll, []).append(rec)

splits = {coll: Dataset.from_list(recs) for coll, recs in by_coll.items()}
eval_dd = DatasetDict(splits)

EVAL_REPO_NAME_MULTI = f"{HF_USERNAME}/Athar-RAG-Eval-HFLLM-Mini-ByCollection-v1"
eval_dd.push_to_hub(EVAL_REPO_NAME_MULTI, token=HF_TOKEN)
print("🚀 Pushed multi-collection to:", f"https://huggingface.co/datasets/{EVAL_REPO_NAME_MULTI}")
```

***

### 9. كيف تستخدم الـEval Dataset مع RAG بتاعك

#### 9.1. تحميله من HF

```python
from datasets import load_dataset

rag_eval = load_dataset(EVAL_REPO_NAME, split="train")
rag_eval[0]
```

#### 9.2. حلقة اختبار سريعة ضد API `/api/v1/ask` (اختياري)

```python
import requests

API_URL = "http://localhost:8002/api/v1/ask"

def query_rag_api(q: str):
    resp = requests.post(API_URL, json={"query": q})
    return resp.json()

example = rag_eval[0]
print("Q:", example["query"])
resp = query_rag_api(example["query"])
resp.keys()
```

***

### 10. Scaling إلى Athar-Datasets الكاملة

بعد ما تتأكد إن كل شيء شغال على الـMini:

1. فعّل تحميل `Athar-Datasets` الكامل.
2. طبق `clean_row` → `full_ds_clean`.
3. نادِ `build_eval_with_hf_llm` مع `max_per_collection` أكبر (مثلاً 2000–5000).
4. احفظ وpush في repo جديد مثل:
   - `Kandil7/Athar-RAG-Eval-HFLLM-Full-v1`
   - أو one-per-collection لو تحب.

***

بهذا الـNotebook عندك:

- Pipeline كامل من HF dataset → تنظيف → توليد أسئلة باستخدام HF transformers → JSONL eval → HF dataset جاهز.
- كل حاجة قابلة للتعديل: الموديل، prompt، عدد الأسئلة لكل collection، إلخ.

لو قلت لي بالضبط:
- الموديل اللي ناوي تستخدمه (`model_id` على HF)،
أقدر أضبط لك جزء الـprompt + `chat template` مخصوص للموديل ده عشان تاخد أفضل جودة أسئلة.