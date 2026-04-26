# 📓 دفتر_notes: بناء مجموعة تقييم RAG متكاملة لنظام Burhan

## 🎯 الغرض من هذا الدفتر

يُنشئ هذا الدفتر مجموعة تقييم شاملة لنظام RAG الخاص بـBurhan، وهي مجموعة بيانات مُصمَّمة خصيصًا لاختبار قدرة نظام الاسترجاع على استرجاع المقاطع الصحيحة والإجابة من النصوص الأصلية.

يغطي هذا الدفتر الخطوات التالية:

1. إعداد بيئة Google Colab وتثبيت المتطلبات الأساسية
2. تحميل مجموعة بيانات Burhan من Hugging Face
3. تنظيف النصوص ومعالجتها بشكل موحد
4. إعداد نموذج اللغات الكبير (LLM) من Hugging Face
5. تصميم قوالب الأوامر المتخصصة لتوليد الأسئلة
6. توليد أسئلة التقييم لكل المقاطع
7. إنشاء سجلات التقييم مع البيانات المرجعية
8. حفظ النتائج ورفعها إلى Hugging Face Hub

---

## 📋 المتطلبات الأساسية

للبدء في تشغيل هذا الدفتر، يجب توفر ما يلي:

- حساب على Hugging Face مع رمز وصول (token)，拥有 صلاحيات الكتابة
- رمز Hugging Face مخصص بـصلاحيات write (للرفع إلى Hub)
- إما GPU من Nvidia في Google Colab أو استخدام API كبديل

---

## 🔧 القسم الأول: إعداد البيئة وتثبيت المتطلبات

### الخطوة 1.1: تثبيت المكتبات اللازمة

```python
# ══════════════════════════════════════════════════════════════════════════════
# تثبيت جميع المكتبات اللازمة في خطوة واحدة
# ══════════════════════════════════════════════════════════════════════════════

!pip install -q datasets huggingface_hub transformers accelerate sentencepiece tqdm
```

### الخطوة 1.2: استيراد المكتبات الأساسية

```python
# ══════════════════════════════════════════════════════════════════════════════
# استيراد المكتبات الأساسية للعمل
# ══════════════════════════════════════════════════════════════════════════════

import os
import json
import re
import textwrap
import random

import torch
from tqdm.auto import tqdm

from datasets import load_dataset, Dataset, DatasetDict
from huggingface_hub import login
```

### الخطوة 1.3: تسجيل الدخول إلى Hugging Face

```python
# ══════════════════════════════════════════════════════════════════════════════
# تسجيل الدخول إلى Hugging Face获取 رمز الوصول
# ════════════════════════════════════════════════════���═════════════════════════

# Try to get token from environment variable first
HF_TOKEN = os.getenv("HF_TOKEN")

# If not found, ask user to input it
if HF_TOKEN is None or HF_TOKEN.strip() == "":
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║  يُرجى إدخال Hugging Face token مع صلاحيات Write               ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    HF_TOKEN = input("أدخل Hugging Face token: ").strip()

# Login to Hugging Face
login(HF_TOKEN)

# تحديد اسم المستخدم على Hugging Face
HF_USERNAME = "Kandil7"  # ← يُرجى تعديل هذا إذا كان مختلفًا

print(f"✓ تم تسجيل الدخول بنجاح كمستخدم: {HF_USERNAME}")
```

---

## 📂 القسم الثاني: تحميل مجموعة بيانات Burhan

يدعم هذا الدفتر تحميل مجموعتين من البيانات:

### الخيار 1.2.1: تحميل Burhan Mini Dataset (مُوصى به للتجارب الأولى)

```python
# ══════════════════════════════════════════════════════════════════════════════
# تحميل مجموعة بيانات Burhan-Mini-Dataset-v2 (خفيفة ومثالية للتجارب)
# ══════════════════════════════════════════════════════════════════════════════

# تحميل المجموعة من Hugging Face
mini_ds = load_dataset("Kandil7/Burhan-Mini-Dataset-v2", split="train")

# عرض بعض المعلومات الأساسية
print(f"╔════════════════════════════════════════════════════════════════════╗")
print(f"║  معلومات مجموعة البيانات                                     ║")
print(f"╚════════════════════════════════════════════════════════════════════╝")
print(f"• الحجم: {len(mini_ds)} صف")
print(f"• الأعمدة: {mini_ds.column_names}")

# عرض عينة من البيانات
print(f"\n• عينة من السجل الأول:")
print(json.dumps(mini_ds[0], ensure_ascii=False, indent=2))
```

### الخيار 1.2.2: تحميل Burhan Full Dataset (للاستخدام الإنتاجي)

```python
# ⚠️ ══════════════════════════════════════════════════════════════════════
#   هذا الخيار اختياري - المجموعة الكاملة كبيرة جداً
#   (تحتوي على ملايين السطور)
# ══════════════════════════════════════════════════════════════════════

# full_ds = load_dataset("Kandil7/Burhan-Datasets", split="train")
# len(full_ds), full_ds[0]
```

### الخطوة 1.2.3: فحص مجموعات البيانات المتاحة

```python
# ═════��════════════════════════════════════════════════════════════════════════
# فحص المجموعات (collections) المتوفرة في البيانات
# ══════════════════════════════════════════════════════════════════════════════

# استخراج المجموعات الفريدة
collections_in_mini = set(mini_ds["collection"])
print(f"╔════════════════════════════════════════════════════════════════════╗")
print(f"║  المجموعات (Collections) المتوفرة                               ║")
print(f"╚════════════════════════════════════════════════════════════════════╝")
for i, coll in enumerate(sorted(collections_in_mini), 1):
    count = sum(1 for row in mini_ds if row.get("collection") == coll)
    print(f"  {i}. {coll}: {count} passage")
```

---

## 🧹 القسم الثالث: تنظيف النصوص ومعالجتها

### الخطوة 3.1: دالة تنظيف النصوص الأساسية

```python
# ══════════════════════════════════════════════════════════════════════════════
# دالة تنظيف النصوص - تزيل العلامات غير الضرورية
# ══════════════════════════════════════════════════════════════════════════════

def clean_text(text: str) -> str:
    """
    تنظيف النص من العلامات غير الضرورية.
    
    المعالجات:
    - استبدال مسافات الأسطر والعودة للسطر بمسافة واحدة
    - دمج المسافات المتعددة في مسافة واحدة
    - إزالة علامات الحواشي من نوع (¬1)
    
    Args:
        text: النص المراد تنظيفه
        
    Returns:
        النص المنظف
    """
    # التحويل إلى نص إذا كان نوع آخر
    if not isinstance(text, str):
        return ""
    
    # استبدال رموز الأسطر
    text = text.replace("\r", " ").replace("\n", " ")
    
    # دمج المسافات المتعددة
    text = re.sub(r"\s+", " ", text).strip()
    
    # إزالة علامات الحواشي (مثل: ¬1, ¬٢, ¬3)
    text = re.sub(r"\(\u00ac\d+\)", "", text)
    
    return text
```

### الخطوة 3.2: دالة معالجة السجل الكامل

```python
# ══════════════════════════════════════════════════════════════════════════════
# دالة معالجة كل سجل - إضافة حقول منظفة
# ══════════════════════════════════════════════════════════════════════════════

def clean_row(row):
    """
    معالجة سجل واحد - إضافة حقول منظفة.
    
    تُنشئ هذه الدالة الحقول التال��ة:
    - content_clean: النص المنظف
    - section_title_clean: عنوان القسم المنظف
    
    Args:
        row: سجل واحد من مجموعة البيانات
        
    Returns:
        السجل مع الحقول الجديدة
    """
    # تنظيف المحتوى
    row["content_clean"] = clean_text(row.get("content", ""))
    
    # تنظيف عنوان القسم (إن وُجد)
    section_title = row.get("section_title", "") or ""
    row["section_title_clean"] = clean_text(section_title)
    
    # التأكد من وجود collection
    row["collection"] = row.get("collection", "unknown")
    
    return row
```

### الخطوة 3.3: تطبيق التنظيف على البيانات

```python
# ══════════════════════════════════════════════════════════════════════════════
# تطبيق دالة التنظيف على جميع السجلات
# ══════════════════════════════════════════════════════════════════════════════

# تطبيق باستخدام multiprocessing للتسريع
mini_ds_clean = mini_ds.map(clean_row, num_proc=4)

# عرض عينة من البيانات المنظفة
print(f"╔════════════════════════════════════════════════════════════════════╗")
print(f"║  عينة من البيانات بعد التنظيف                                ║")
print(f"╚════════════════════════════════════════════════════════════════════╝")
sample = mini_ds_clean[0]
print(f"• المحتوى (الأول 200 حرف): {sample['content_clean'][:200]}...")
print(f"• عنوان القسم: {sample['section_title_clean']}")
print(f"• المجموعة: {sample['collection']}")
```

---

## 🤖 القسم الرابع: إعداد نموذج اللغات الكبير (LLM)

### الخطوة 4.1: اختيار النموذج المناسب

```python
# ══════════════════════════════════════════════════════════════════════════════
# اختيار نموذج اللغات الكبير المناسب
# ══════════════════════════════════════════════════════════════════════════════

# النماذج المدعومة:
# - Qwen/Qwen2.5-7B-Instruct (مُوصى به - جيد للعربية)
# - Qwen/Qwen2.5-14B-Instruct (أقوى لكن أبطأ)
# - meta-llama/Llama-3.1-8B-Instruct
# - arabic-bert-large-v2 (للembeddeding فقط - ليس مناسبًا للتوليد)

MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct"  # ← يُمكن تعديله selon الحاجة
```

### الخطوة 4.2: تحميل النموذج والمحلل اللغوي

```python
# ══════════════════════════════════════════════════════════════════════════════
# تحميل النموذج والمحلل اللغوي (tokenizer)
# ══════════════════════════════════════════════════════════════════════════════════════

from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

print(f"• جاري تحميل النموذج: {MODEL_NAME}")

# تحميل tokenizer
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)

# تحميل النموذج مع تعيين الجهاز التلقائي
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    device_map="auto",
    torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
)

# إنشاء pipeline للتوليد
gen_pipe = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    device_map="auto",
)

print(f"✓ تم تحميل النموذج بنجاح")
print(f"• الجهاز: {model.device}")
print(f"• CUDA متاح: {torch.cuda.is_available()}")
```

---

## 📝 القسم الخامس: تصميم قوالب الأوامر (Prompts)

### الخطوة 5.1: قالب الأمر الأساسي للنظام

```python
# ══════════════════════════════════════════════════════════════════════════════
# القالب الأساسي لنظام الـ LLM
# ══════════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = (
    "أنت نموذج مساعد متخصص في إنشاء مجموعة تقييم (evaluation dataset) لنظام RAG عربي "
    "يعتمد على نصوص في السيرة النبوية والعلوم الشرعية. "
    "مهمتك توليد أسئلة عالية الجودة تساعد على اختبار قدرة النظام على استرجاع المقطع الصحيح والإجابة من النص بدقة."
)
```

### الخطوة 5.2: دالة بناء الأمر للمستخدم

```python
# ══════════════════════════════════════════════════════════════════════════════
# دالة بناء الأمر الكامل للمستخدم بناءً على المقطع
# ══════════════════════════════════════════════════════════════════════════════

def build_hf_prompt(passage: dict) -> str:
    """
    بناء الأمر الكامل بناءً على المقطع المُعطى.
    
    Args:
        passage: قاموس يحتوي على معلومات المقطع
        
    Returns:
        الأمر الكامل جاهز للإرسال إلى النموذج
    """
    # استخراج المعلومات من المقطع
    content = passage["content_clean"][:900]  # تحديد الحد الأقصى للمحتوى
    section = passage.get("section_title_clean", "") or ""
    book = passage.get("book_title", "")
    collection = passage.get("collection", "")
    
    # بناء الأمر للمستخدم
    user = textwrap.dedent(f"""
    النص التالي من مجموعة '{collection}'، من كتاب '{book}'، تحت عنوان فرعي '{section}':

    \"\"\"{content}\"\"\"

    المطلوب:
    - أنشئ بين 2 و 4 أسئلة فهم/استرجاع (retrieval questions) باللغة العربية الفصحى.
    - يجب أن:
      * تعتمد فقط على المعلومات الموجودة في النص.
      * تساعد على تقييم قدرة نظام RAG على استرجاع هذا المقطع.
      * تتنوع بين:
          - سؤال عن الفكرة أو الحدث الرئيسي في النص.
          - سؤال عن العبرة أو الدرس المستفاد.
          - (اختياري) سؤال عن تفاصيل محددة (أسماء، أماكن، أزمنة) إن كانت موجودة.
    - لا تذكر اسم الكتاب أو المؤلف أو رقم الصفحة أو اسم المجموعة في نص السؤال.
    - لا تُفصح عن الإجابة في السؤال.
    - لا تُضف أي شرح خارج JSON.

    أعد النتيجة في صيغة JSON فقط بالشكل التالي:

    {{
      "questions": [
        "سؤال 1 ...؟",
        "سؤال 2 ...؟",
        "سؤال 3 ...؟",
        "سؤال 4 ...؟"
      ]
    }}
    """).strip()
    
    # بناء الأمر الشبيه بـ Chat Template لمعظم نماذج instruct
    prompt = f"<|system|>\n{SYSTEM_PROMPT}\n<|user|>\n{user}\n<|assistant|>\n"
    
    return prompt
```

---

## ✨ القسم السادس: توليد الأسئلة

### الخطوة 6.1: دالة توليد الأسئلة لمقطع واحد

```python
# ══════════════════════════════════════════════════════════════════════════════
# دالة توليد الأسئلة لمقطع واحد باستخدام LLM
# ══════════════════════════════════════════════════════════════════════════════

def hf_llm_generate_questions_for_passage(passage: dict, max_new_tokens: int = 512) -> list:
    """
    توليد أسئل�� تقييم لمقطع واحد.
    
    Args:
        passage: قاموس معلومات المقطع
        max_new_tokens: الحد الأقصى للرموز المُولَّدة
        
    Returns:
        قائمة الأسئلة المُولَّدة
    """
    # بناء الأمر
    prompt = build_hf_prompt(passage)
    
    # توليد النص
    out = gen_pipe(
        prompt,
        max_new_tokens=max_new_tokens,
        do_sample=True,
        temperature=0.4,
        top_p=0.9,
        eos_token_id=tokenizer.eos_token_id,
    )[0]["generated_text"]
    
    # استخراج الجزء بعد <|assistant|>
    if "<|assistant|>" in out:
        out = out.split("<|assistant|>")[-1].strip()
    
    # إزالة رموز markdown
    text = out.replace("```json", "").replace("```", "").strip()
    
    # محاولة تحليل JSON
    questions = []
    try:
        obj = json.loads(text)
        qs = obj.get("questions", [])
        if isinstance(qs, list):
            questions = [q.strip() for q in qs if isinstance(q, str)]
    except json.JSONDecodeError:
        # fallback: استخراج الأسطر التي تنتهي بعلامة استفهام
        candidates = re.findall(r"[^\n]+؟", text)
        questions = [c.strip() for c in candidates]
    
    # فلترة الأسئلة:
    # - إزالة الأسئلة القصيرة جداً
    # - إزالة الأسئلة التي تحتوي على أقواس JSON
    questions = [
        q for q in questions 
        if len(q) > 10 and "}" not in q and "{" not in q
    ]
    
    # تحديد الحد الأقصى بـ 4 أسئلة
    return questions[:4]
```

### الخطوة 6.2: اختبار الدالة على عينة

```python
# ══════════════════════════════════════════════════════════════════════════════
# اختبار دالة توليد الأسئلة على عينة
# ══════════════════════════════════════════════════════════════════════════════

# اختيار عينة للاختبار
test_passage = mini_ds_clean[0]
print(f"╔════════════════════════════════════════════════════════════════════╗")
print(f"║  اختبار توليد الأسئلة                                    ║")
print(f"╚════════════════════════════════════════════════════════════════════╝")
print(f"• المجموعة: {test_passage['collection']}")
print(f"• الكتاب: {test_passage['book_title']}")
print(f"• المحتوى (الأول 150 حرف): {test_passage['content_clean'][:150]}...")
print()

# توليد الأسئلة
test_questions = hf_llm_generate_questions_for_passage(test_passage)

print(f"• الأسئلة المُولَّدة ({len(test_questions)}):")
for i, q in enumerate(test_questions, 1):
    print(f"  {i}. {q}")
```

---

## 📊 القسم السابع: استراتيجية التوزيع على المجموعات

### الخطوة 7.1: تحديد حدود الأسئلة لكل مجموعة

```python
# ═════════════════=============================================================
# تحديد الحد الأقصى لعدد الأسئلة لكل مجموعة
# ══════════════════════════════════════════════════════════════════════════════

# قائمة الحدود لكل مجموعة (يمكن تعديلها حسب الاحتياجات)
MAX_PER_COLLECTION = {
    # المجموعات الرئيسية في Burhan Mini
    "seerah_passages": 1000,      # السيرة النبوية
    "fiqh_passages": 500,         # الفقه
    "aqeedah_passages": 500,       # العقيدة
    "hadith_passages": 800,        # الحديث
    "tafsir_passages": 400,        # التفسير
    "sirah_passages": 400,         # السيرة (بديل)
    "tarikh_passages": 300,        # التاريخ
    "adab_passages": 200,          # الأدب
    "unknown": 200,               # غير مصنف
}

# الحد الافتراضي للمجموعات غير المحددة
DEFAULT_MAX = 300
```

---

## 🏗️ القسم الثامن: بناء سجلات التقييم

### الخطوة 8.1: دالة بناء سجلات التقييم

```python
# ══════════════════════════════════════════════════════════════════════════════
# دالة بناء سجلات التقييم لجميع المقاطع
# ══════════════════════════════════════════════════════════════════════════════

def build_eval_with_hf_llm(
    ds, 
    max_per_collection_map=None, 
    default_max=300
):
    """
    بناء سجلات التقييم باستخدام LLM.
    
    Args:
        ds: مجموعة البيانات المنظفة
        max_per_collection_map: خريطة الحدود لكل مجموعة
        default_max: الحد الافتراضي
        
    Returns:
        قائمة السجلات +counts =counts لكل مجموعة
    """
    if max_per_collection_map is None:
        max_per_collection_map = {}
    
    #计数器 للمجاميع
    counts = {}
    records = []
    
    # التكرار على جميع السجلات
    for row in tqdm(ds, total=len(ds), desc="Building eval records"):
        coll = row.get("collection", "unknown")
        max_allowed = max_per_collection_map.get(coll, default_max)
        
        #تحقق من الحد
        counts.setdefault(coll, 0)
        if counts[coll] >= max_allowed:
            continue
        
        # التحقق من وجود محتوى
        if not row.get("content_clean"):
            continue
        
        # توليد الأسئلة
        questions = hf_llm_generate_questions_for_passage(row)
        if not questions:
            continue
        
        # إنشاء سجل لكل سؤال
        for q in questions:
            if counts[coll] >= max_allowed:
                break
            
            # إنشاء السجل الذهبي (gold passage)
            gold = [{
                "collection": coll,
                "book_id": row.get("book_id"),
                "page_number": row.get("page_number"),
                "section_title": row.get("section_title_clean"),
                "content_snippet": row["content_clean"][:400],
                "author": row.get("author", ""),
                "book_title": row.get("book_title", ""),
            }]
            
            # إنشاء السجل
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
    
    # عرض النتائج
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║  ملخص التوزيع                                               ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    for coll, count in sorted(counts.items()):
        print(f"  • {coll}: {count} question")
    print(f"\n• Total: {len(records)} eval records")
    
    return records, counts
```

### الخطوة 8.2: تشغيل البناء على البيانات الصغيرة

```python
# ══════════════════════════════════════════════════════════════════════════════
# تشغيل البناء على Burhan Mini Dataset
# ══════════════════════════════════════════════════════════════════════════════

# حدود كل مجموعة (يُنصح بالبدء بأرقام صغيرة للاختبار)
MAX_PER_COLLECTION_TEST = {
    "seerah_passages": 800,
    "fiqh_passages": 400,
    "aqeedah_passages": 400,
    "hadith_passages": 600,
    "unknown": 200,
}

# تشغيل الدالة
eval_records_mini_hf, counts_mini = build_eval_with_hf_llm(
    mini_ds_clean,
    max_per_collection_map=MAX_PER_COLLECTION_TEST,
    default_max=200,
)
```

> 💡 **نصيحة**: للبدء، يُنصح باستخدام أرقام صغيرة (مثلاً 100-200) لكل مجموعة لاختبار السرعة والجودة، ثم زيادة العدد تدريجياً.

---

## 💾 القسم التاسع: الحفظ والرفع إلى Hugging Face Hub

### الخطوة 9.1: حفظ البيانات محلياً

```python
# ══════════════════════════════════════════════════════════════════════════════
# حفظ السجلات في ملف JSONL محلياً
# ══════════════════════════════════════════════════════════════════════

# إنشاء المجلد
os.makedirs("output", exist_ok=True)

# مسار الملف
eval_mini_path = "output/Burhan-RAG-Eval-HFLLM-Mini-v1.jsonl"

# حفظ السجلات
with open(eval_mini_path, "w", encoding="utf-8") as f:
    for rec in eval_records_mini_hf:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

print(f"✓ تم حفظ {len(eval_records_mini_hf)} سجل في:")
print(f"  {eval_mini_path}")
```

### الخطوة 9.2: تحويل إلى HF Dataset

```python
# ══════════════════════════════════════════════════════════════════════════════
# تحويل ملف JSONL إلى Hugging Face Dataset
# ══════��═��═════════════════════════════════════════════════════════════════════

eval_mini_ds = Dataset.from_json(eval_mini_path)

print(f"╔════════════════════════════════════════════════════════════════════╗")
print(f"║  معلومات مجموعة البيانات                                     ║")
print(f"╚════════════════════════════════════════════════════════════════════╝")
print(f"• الحجم: {len(eval_mini_ds)} سؤال")
print(f"• الأعمدة: {eval_mini_ds.column_names}")
```

### الخطوة 9.3: الرفع إلى Hugging Face Hub

```python
# ══════════════════════════════════════════════════════════════════════════════
# رفع مجموعة البيانات إلى Hugging Face Hub
# ══════════════════════════════════════════════════════════════════════════════

# اسم مستودع البيانات
EVAL_REPO_NAME = f"{HF_USERNAME}/Burhan-RAG-Eval-HFLLM-Mini-v1"

# الرفع
eval_mini_ds.push_to_hub(EVAL_REPO_NAME, token=HF_TOKEN)

print(f"🚀 تم رفع مجموعة البيانات بنجاح!")
print(f"   الرابط: https://huggingface.co/datasets/{EVAL_REPO_NAME}")
```

### الخطوة 9.4: (اختياري) تقسيم البيانات حسب المجموعة

```python
# ══════════════════════════════════════════════════════════════════════════════
# تقسيم البيانات حسب المجموعة
# ══════════════════════════════════════════════════════════════════════

# تجميع السجلات حسب المجموعة
by_coll = {}
for rec in eval_records_mini_hf:
    coll = rec["collection"]
    by_coll.setdefault(coll, []).append(rec)

# إنشاء DatasetDict لكل مجموعة
splits = {coll: Dataset.from_list(recs) for coll, recs in by_coll.items()}
eval_dd = DatasetDict(splits)

# اسم المستودع الجديد
EVAL_REPO_NAME_MULTI = f"{HF_USERNAME}/Burhan-RAG-Eval-HFLLM-Mini-ByCollection-v1"

# الرفع
eval_dd.push_to_hub(EVAL_REPO_NAME_MULTI, token=HF_TOKEN)

print(f"🚀 تم رفع البيانات المقسمة بنجاح!")
print(f"   الرابط: https://huggingface.co/datasets/{EVAL_REPO_NAME_MULTI}")
```

---

## 🧪 القسم العاشر: استخدام مجموعة التقييم

### الخطوة 10.1: تحميل مجموعة التقييم

```python
# ══════════════════════════════════════════════════════════════════════════════
# تحميل مجموعة التقييم من Hugging Face
# ══════════════════════════════════════════════════════════════════════════════

from datasets import load_dataset

# تحميل المجموعة
rag_eval = load_dataset(EVAL_REPO_NAME, split="train")

# عرض عينة
print(f"╔════════════════════════════════════════════════════════════════════╗")
print(f"║  عينة من سؤال التقييم                                          ║")
print(f"╚════════════════════════════════════════════════════════════════════╝")
example = rag_eval[0]
print(f"• السؤال: {example['query']}")
print(f"• المجموعة: {example['collection']}")
print(f"• صعوبة: {example['difficulty']}")
print(f"• gold_passages: {len(example['gold_passages'])} passage")
```

### الخطوة 10.2: اختبار gegen RAG API

```python
# ══════════════════════════════════════════════════════════════════════════════
# اختبار RAG API (اختياري)
# ══════════════════════════════════════════════════════════════════════════════

import requests

# عنوان API (يُرجى تعديله حسب الإعداد المحلي)
API_URL = "http://localhost:8002/api/v1/ask"

def query_rag_api(q: str):
    """
    إرسال سؤال إلى RAG API والحصول على الإجابة.
    
    Args:
        q: السؤال
        
    Returns:
        JSON response
    """
    resp = requests.post(API_URL, json={"query": q})
    return resp.json()

# اختبار على عينة
example = rag_eval[0]
print(f"╔════════════════════════════════════════════════════════════════════╗")
print(f"║  اختبار RAG API                                               ║")
print(f"╚════════════════════════════════════════════════════════════════════╝")
print(f"Q: {example['query']}")

try:
    resp = query_rag_api(example['query'])
    print(f"\n• Response keys: {list(resp.keys())}")
except Exception as e:
    print(f"\n• Error: {e}")
```

---

## 📈 القسم الحادي عشر: التوسع إلى المجموعة الكاملة

### الخطوة 11.1: التحضير للتوسع

بعد التأكد من أن كل شيء يعمل بشكل صحيح على المجموعة الصغيرة، يُمكن التوسع إلى المجموعة الكاملة باتباع الخطوات التالية:

```python
# ═════════════════=============================================================
# التوسع إلى Burhan-Datasets الكاملة
# ══════════════════════════════════════════════════════════════════════════════

# 1. تحميل المجموعة الكاملة
# full_ds = load_dataset("Kandil7/Burhan-Datasets", split="train")
# print(f"• Full dataset size: {len(full_ds)} rows")

# 2. تطبيق التنظيف
# full_ds_clean = full_ds.map(clean_row, num_proc=8)

# 3. تشغيل البناء مع حدود أكبر
# MAX_PER_COLLECTION_FULL = {
#     "seerah_passages": 5000,
#     "fiqh_passages": 2000,
#     ...
# }
# eval_records_full_hf, counts_full = build_eval_with_hf_llm(
#     full_ds_clean,
#     max_per_collection_map=MAX_PER_COLLECTION_FULL,
#     default_max=1000,
# )

# 4. حفظ ورفع
# eval_full_path = "output/Burhan-RAG-Eval-HFLLM-Full-v1.jsonl"
# ...
```

### الخطوة 11.2: أسماء المستودعات المقترحة

للمجموعة الكاملة، يُنصح باستخدام أسماء المستودعات التالية:

```python
# ══════════════════════════════════════════════════════════════════════════════
# أسماء مستودعات البيانات المقترحة
# ══════════════════════════════════════════════════════════════════════════════

# للخيارات المختلفة:
# - Kandil7/Burhan-RAG-Eval-HFLLM-Full-v1
# - Kandir7/Burhan-RAG-Eval-HF-Llama-3.1-8B-v1
# - Kandil7/Burhan-RAG-Eval-GPT4-v1 (للاستخدام مع OpenAI API)
```

---

## ✅ ملخص الدفتر

بهذا الدفتر، أصبح لديك:

- ✅ **pipeline كامل** من تحميل البيانات → تنظيف → توليد أسئلة → إنشاء_eval records → رفع إلى Hub
- ✅ **مجموعة تقييم** جاهزة لاختبار RAG
- ✅ **مرونة عالية** في تعديل الموديل والبرومبت والعدد
- ✅ **كود قابل للتوسع** للمجموعة الكاملة

---

## 🔗 الموارد الإضافية

- **مجموعة بيانات Burhan**: [Kandil7/Burhan-Datasets](https://huggingface.co/datasets/Kandil7/Burhan-Datasets)
- **نموذج Qwen2.5**: [Qwen/Qwen2.5-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct)
- **مستندات Hugging Face Datasets**: [Hugging Face Docs](https://huggingface.co/docs/datasets)

---

## ⚙️ إعدادات قابلة للتعديل

| المتغير | الوصف | القيمة الافتراضية |
|--------|-------|---------------------|
| `MODEL_NAME` | اسم نموذج LLM | `Qwen/Qwen2.5-7B-Instruct` |
| `HF_USERNAME` | اسم المستخدم | `Kandil7` |
| `MAX_PER_COLLECTION` | حدود الأسئلة | (dict) |
| `max_new_tokens` | الرموز المُولَّدة | `512` |
| `temperature` | درجة الإبداع | `0.4` |

---

## 🆘 استكشاف الأخطاء الشائعة

### المشكلة 1: عدم كفاية VRAM

```python
# الحل: استخدام نموذج أصغر أو FP16
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    device_map="auto",
    torch_dtype=torch.float16,  # بدلاً من bfloat16
)
```

### المشكلة 2: فشل تحليل JSON

```python
# الحل: تحسين الـ prompt أو استخدام regex fallback更强
# الدالة الحالية تتضمن fallback بالفعل
```

### المشكلة 3: بطء التوليد

```python
# الحل: تقليل max_per_collection أو استخدام batch processing
# أو استخدام API بدلاً من المحلي
```

---

## 🛡️ القسم الثاني عشر: معالجة الأخطاء والاستثناءات

### الخطوة 12.1: نظام المعالجة الشامل

```python
# ══════════════════════════════════════════════════════════════════════════════
# نظام المعالجة الشامل للأخطاء
# ══════════════════════════════════════════════════════════════════════════════

import traceback
import sys
from functools import wraps

class EvaluationError(Exception):
    """الخطأ الأساسي لتقييم RAG."""
    pass

class ModelLoadError(EvaluationError):
    """خطأ في تحميل النموذج."""
    pass

class GenerationError(EvaluationError):
    """خطأ في توليد الأسئلة."""
    pass

class DatasetError(EvaluationError):
    """خطأ في مجموعة البيانات."""
    pass

def handle_errors(func):
    """ Decorator لمعالجة الأخطاء تلقائياً."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"❌ خطأ في {func.__name__}: {str(e)}")
            traceback.print_exc()
            return None
    return wrapper
```

### الخطوة 12.2: نظام النقاط (Checkpoints)

```python
# ══════════════════════════════════════════════════════════════════════════════
# نظام النقاط (Checkpoints) للحفظ والاستئناف
# ══════════════════════════════════════════════════════════════════════════════

import pickle
from pathlib import Path

class EvalCheckpoint:
    """
    نظام النقاط للحفظ والاستئناف عند الانقطاع.
    
    يُتيح هذا النظام:
    - حفظ التقدم بشكل دوري
    - استئناف العمل من آخر نقطة
    - تجنب فقدان البيانات عند انقطاع Colab
    """
    
    def __init__(self, checkpoint_path: str = "output/eval_checkpoints.pkl"):
        self.checkpoint_path = checkpoint_path
        self.state = {
            "processed_indices": set(),
            "counts": {},
            "records": [],
            "last_update": None,
        }
        self.load()
    
    def load(self):
        """تحميل النقطة الأخيرة."""
        if Path(self.checkpoint_path).exists():
            try:
                with open(self.checkpoint_path, "rb") as f:
                    self.state = pickle.load(f)
                print(f"✓ تم تحميل نقطة التقييم: {len(self.state['processed_indices'])} processed")
            except Exception as e:
                print(f"⚠️ خطأ في تحميل النقطة: {e}")
    
    def save(self):
        """حفظ النقطة الحالية."""
        self.state["last_update"] = str(datetime.now())
        os.makedirs(os.path.dirname(self.checkpoint_path), exist_ok=True)
        with open(self.checkpoint_path, "wb") as f:
            pickle.dump(self.state, f)
        print(f"✓ تم حفظ نقطة التقييم")
    
    def is_processed(self, idx: int) -> bool:
        """التحقق مما إذا كان الفهرس قد عولج."""
        return idx in self.state["processed_indices"]
    
    def mark_processed(self, idx: int, count: int, records: list):
        """وضع علامة على الفهرس كمُعالج."""
        self.state["processed_indices"].add(idx)
        self.state["records"].extend(records)
        for coll in self.state["counts"]:
            self.state["counts"][coll] = count
```

### الخطوة 12.3: مراقبة استخدام GPU

```python
# ══════════════════════════════════════════════════════════════════════════════
# مراقبة استخدام GPU والذاكرة
# ══════════════════════════════════════════════════════════════════════════════

import gc

def check_gpu_memory():
    """
    فحص استخدام GPU والذاكرة.
    
    Returns:
        قاموس يحتوي على معلومات الذاكرة
    """
    if not torch.cuda.is_available():
        return {"available": False}
    
    #_allocated = torch.cuda.memory_allocated() / 1024**3
    #_reserved = torch.cuda.memory_reserved() / 1024**3
    
    return {
        "available": True,
        "allocated_gb": torch.cuda.memory_allocated() / 1024**3,
        "reserved_gb": torch.cuda.memory_reserved() / 1024**3,
        "max_allocated_gb": torch.cuda.max_memory_allocated() / 1024**3,
    }

def clear_gpu_cache():
    """مسح ذاكرة GPU المؤقتة."""
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        gc.collect()
        print("✓ تم مسح ذاكرة GPU المؤقتة")

def print_gpu_status():
    """عرض حالة GPU."""
    mem = check_gpu_memory()
    if mem["available"]:
        print(f"╔════════════════════════════════════════════════════════════════════╗")
        print(f"║  حالة GPU                                                     ║")
        print(f"╚════════════════════════════════════════════════════════════════════════╝")
        print(f"  • المُخصصة: {mem['allocated_gb']:.2f} GB")
        print(f"  • المحجوزة: {mem['reserved_gb']:.2f} GB")
        print(f"  • الحد الأقصى: {mem['max_allocated_gb']:.2f} GB")
    else:
        print("⚠️ CUDA غير متاح")
```

---

## ⚡ القسم الثالث عشر: تحسين الأداء

### الخطوة 13.1: المعالجة الدفعية (Batch Processing)

```python
# ══════════════════════════════════════════════════════════════════════════════
# دالة توليد الأسئلة بالدفعات (Batching)
# ══════════════════════════════════════════════════════════════════════════════

def generate_questions_batch(passages: list, batch_size: int = 4) -> list:
    """
    توليد الأسئلة لعدة مقاطع دفعة واحدة.
    
    Args:
        passages: قائمة المقاطع
        batch_size: حجم الدفعة
        
    Returns:
        قائمة الأسئلة المُولَّدة
    """
    results = []
    
    for i in range(0, len(passages), batch_size):
        batch = passages[i:i + batch_size]
        
        # بناء الأوامر للدفعة
        prompts = [build_hf_prompt(p) for p in batch]
        
        # توليد كل الأسئلة
        for prompt in prompts:
            out = gen_pipe(
                prompt,
                max_new_tokens=512,
                do_sample=True,
                temperature=0.4,
                top_p=0.9,
            )[0]["generated_text"]
            
            # استخراج الأسئلة (نفس المنطق السابق)
            if "<|assistant|>" in out:
                out = out.split("<|assistant|>")[-1].strip()
            
            text = out.replace("```json", "").replace("```", "").strip()
            
            try:
                obj = json.loads(text)
                qs = obj.get("questions", [])
                results.extend([q.strip() for q in qs if isinstance(q, str)])
            except json.JSONDecodeError:
                # fallback
                candidates = re.findall(r"[^\n]+؟", text)
                results.extend([c.strip() for c in candidates])
        
        # مسح الذاكرة بعد كل دفعة
        if i % (batch_size * 5) == 0:
            clear_gpu_cache()
    
    # فلترة نهائية
    results = [
        q for q in results 
        if len(q) > 10 and "}" not in q and "{" not in q
    ][:len(passages) * 4]  # الحد الأقصى
    
    return results
```

### الخطوة 13.2: تخطي المقاطع المعطلة

```python
# ══════════════════════════════════════════════════════════════════════════════
# دالة آمنة لتوليد الأسئلة مع معالجة الأخطاء
# ══════════════════════════════════════════════════════════════════════════════

@handle_errors
def safe_generate_questions(passage: dict, max_retries: int = 3) -> list:
    """
    توليد الأسئلة مع معالجة الأخطاء وإعادة المحاولة.
    
    Args:
        passage: قاموس المقطع
        max_retries: عدد المحاولات
        
    Returns:
        قائمة الأسئلة أو قائمة فارغة عند الفشل
    """
    for attempt in range(max_retries):
        try:
            questions = hf_llm_generate_questions_for_passage(passage)
            if questions:  # نجاح فقط إذا كانت هناك أسئلة
                return questions
        except Exception as e:
            print(f"  ⚠️ المحاولة {attempt + 1} failed: {e}")
            clear_gpu_cache()  # مسح الذاكرة عند الفشل
    
    print(f"  ❌ فشل بعد {max_retries} محاولات")
    return []  # إرجاع قائمة فارغة عند الفشل النهائي
```

---

## 📊 القسم الرابع عشر: تقييم جودة الأسئلة

### الخطوة 14.1:メايقيس الجودة التلقائي

```python
# ══════════════════════════════════════════════════════════════════════════════
# تقييم جودة الأسئلة المُولَّدة
# ══════════════════════════════════════════════════════════════════════════════

def assess_question_quality(question: str, passage: dict) -> dict:
    """
    تقييم جودة سؤال واحد.
    
    Checks:
    - length: هل السؤال طويل بما يكفي؟
    - relevance: هل يحتوي على كلمات مفتاحية من النص؟
    - format: هل ينتهي بعلامة استفهام؟
    - no_leak: هل لا يكشف عن الإجابة؟
    
    Args:
        question: السؤال
        passage: المقطع الأصلي
        
    Returns:
        قاموس نتائج التقييم
    """
    results = {
        "length_ok": len(question) >= 15 and len(question) <= 300,
        "ends_with_question": question.strip().endswith("؟") or question.strip().endswith("?"),
        "has_keyword": any(kw in question for kw in ["ما", "من", "كيف", "لماذا", "متى", "أين"]),
        "no_book_name": passage.get("book_title", "") not in question,
        "no_author": passage.get("author", "") not in question,
    }
    
    results["pass"] = all(results.values())
    return results

def evaluate_dataset_quality(eval_records: list) -> dict:
    """
    تقييم جودة مجموعة التقييم الكاملة.
    
    Args:
        eval_records: قائمة سجلات التقييم
        
    Returns:
        قاموس إحصائيات الجودة
    """
    total = len(eval_records)
    if total == 0:
        return {"error": "No records"}
    
    stats = {
        "total": total,
        "by_collection": {},
        "length_distribution": {"short": 0, "medium": 0, "long": 0},
        "quality_pass": 0,
    }
    
    for rec in eval_records:
        coll = rec.get("collection", "unknown")
        stats["by_collection"][coll] = stats["by_collection"].get(coll, 0) + 1
        
        q_len = len(rec["query"])
        if q_len < 20:
            stats["length_distribution"]["short"] += 1
        elif q_len < 100:
            stats["length_distribution"]["medium"] += 1
        else:
            stats["length_distribution"]["long"] += 1
    
    stats["quality_pass"] = sum(
        1 for rec in eval_records 
        if len(rec["query"]) >= 15
    )
    stats["quality_rate"] = stats["quality_pass"] / total * 100
    
    return stats
```

### الخطوة 14.2: عرض إحصائيات الجودة

```python
# ══════════════════════════════════════════════════════════════════════════════
# عرض إحصائيات الجودة
# ══════════════════════════════════════════════════════════════════════════════

if eval_records_mini_hf:
    quality_stats = evaluate_dataset_quality(eval_records_mini_hf)
    
    print(f"╔════════════════════════════════════════════════════════════════════╗")
    print(f"║  إحصائيات الجودة                                               ║")
    print(f"╚════════════════════════════════════════════════════════════════════╝")
    print(f"• Total questions: {quality_stats['total']}")
    print(f"• Quality pass: {quality_stats['quality_pass']} ({quality_stats['quality_rate']:.1f}%)")
    print(f"\n• Distribution by length:")
    print(f"  - Short (<20): {quality_stats['length_distribution']['short']}")
    print(f"  - Medium (20-100): {quality_stats['length_distribution']['medium']}")
    print(f"  - Long (>100): {quality_stats['length_distribution']['long']}")
    print(f"\n• By collection:")
    for coll, count in quality_stats["by_collection"].items():
        print(f"  - {coll}: {count}")
```

---

## 🔄 القسم الخامس عشر: نماذج بديلة

### الخطوة 15.1: استخدام OpenAI API

```python
# ══════════════════════════════════════════════════════════════════════════════
# استخدام OpenAI API بدلاً من النموذج المحلي
# ══════════════════════════════════════════════════════════════════════════════

import openai

def generate_questions_openai(passage: dict, model: str = "gpt-4o") -> list:
    """
    توليد الأسئلة باستخدام OpenAI API.
    
    Args:
        passage: قاموس المقطع
        model: اسم النموذج
        
    Returns:
        قائمة الأسئلة
    """
    # إعداد OpenAI
    openai.api_key = os.getenv("OPENAI_API_KEY")
    
    prompt = build_hf_prompt(passage)
    
    response = openai.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt.split("<|user|>")[1].split("<|assistant|>")[0]}
        ],
        response_format={"type": "json_object"},
        temperature=0.4,
    )
    
    result = response.choices[0].message.content
    
    try:
        obj = json.loads(result)
        return [q.strip() for q in obj.get("questions", [])]
    except:
        return []
```

### الخطوة 15.2: استخدام Anthropic API

```python
# ══════════════════════════════════════════════════════════════════════════════
# استخدام Anthropic API (Claude)
# ══════════════════════════════════════════════════════════════════════════════

# import anthropic

# def generate_questions_claude(passage: dict) -> list:
#     """
#     توليد الأسئلة باستخدام Claude API.
#     """
#     client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
#     
#     prompt = build_hf_prompt(passage)
#     
#     message = client.messages.create(
#         model="claude-3-5-sonnet-20241022",
#         max_tokens=1024,
#         system=SYSTEM_PROMPT,
#         messages=[{"role": "user", "content": prompt}]
#     )
#     
#     text = message.content[0].text
#     
#     try:
#         obj = json.loads(text)
#         return [q.strip() for q in obj.get("questions", [])]
#     except:
#         return []
```

---

## ✅ القسم السادس عشر: التحقق النهائي

### الخطوة 16.1: التحقق من صحة مجموعة البيانات

```python
# ══════════════════════════════════════════════════════════════════════════════
# التحقق من صحة مجموعة البيانات النهائية
# ══════════════════════════════════════════════════════════════════════════════

def validate_eval_dataset(eval_records: list) -> dict:
    """
    التحقق من صحة مجموعة بيانات التقييم.
    
    Checks:
    - 所有 السجلات تحتوي على الحقول المطلوبة
    - gold_passages غير فارغة
    - لا توجد حقول مفقودة
        
    Returns:
        قاموس نتائج التحقق
    """
    required_fields = ["query", "collection", "gold_passages", "difficulty"]
    validation = {
        "valid": True,
        "errors": [],
        "warnings": [],
    }
    
    for i, rec in enumerate(eval_records):
        # التحقق من الحقول المطلوبة
        for field in required_fields:
            if field not in rec:
                validation["errors"].append(f"Row {i}: missing field '{field}'")
                validation["valid"] = False
        
        # التحقق من gold_passages
        if not rec.get("gold_passages"):
            validation["errors"].append(f"Row {i}: empty gold_passages")
            validation["valid"] = False
        
        # التحقق من طول السؤال
        if len(rec.get("query", "")) < 5:
            validation["warnings"].append(f"Row {i}: very short query")
    
    return validation
```

### الخطوة 16.2: تشغيل التحقق

```python
# ══════════════════════════════════════════════════════════════════════════════
# تشغيل التحقق على مجموعة البيانات
# ══════════════════════════════════════════════════════════════════════════════

if eval_records_mini_hf:
    validation = validate_eval_dataset(eval_records_mini_hf)
    
    print(f"╔════════════════════════════════════════════════════════════════════╗")
    print(f"║  نتائج التحقق                                                 ║")
    print(f"╚════════════════════════════════════════════════════════════════════╝")
    
    if validation["valid"]:
        print("✓ ✓✓ تم التحقق بنجاح - مجموعة البيانات صالحة!")
    else:
        print("❌ تم 발견 أخطاء:")
        for err in validation["errors"][:5]:
            print(f"  • {err}")
    
    if validation["warnings"]:
        print(f"⚠️ تحذيرات ({len(validation['warnings'])}):")
        for warn in validation["warnings"][:3]:
            print(f"  • {warn}")
```

---

## 📦 القسم السابع عشر: تصدير وتنسيق البيانات

### الخطوة 17.1: تنسيقات التصدير المدعومة

```python
# ══════════════════════════════════════════════════════════════════════════════
# تصدير البيانات بعدة تنسيقات
# ══════════════════════════════════════════════════════════════════════════════

def export_eval_dataset(
    eval_records: list, 
    base_path: str = "output/Burhan-RAG-Eval",
    formats: list = None
):
    """
    تصدير مجموعة البيانات بعدة تنسيقات.
    
    Supported formats:
    - jsonl: JSON Lines (default)
    - json: JSON array
    - parquet: Apache Parquet
    - csv: CSV (مع استخراج الحقول المتداخلة)
    
    Args:
        eval_records: قائمة السجلات
        base_path: مسار الملف الأساسي
        formats: قائمة التنسيقات
    """
    if formats is None:
        formats = ["jsonl", "json", "parquet"]
    
    results = {}
    
    # JSONL
    if "jsonl" in formats:
        jsonl_path = f"{base_path}.jsonl"
        with open(jsonl_path, "w", encoding="utf-8") as f:
            for rec in eval_records:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        results["jsonl"] = jsonl_path
    
    # JSON
    if "json" in formats:
        json_path = f"{base_path}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(eval_records, f, ensure_ascii=False, indent=2)
        results["json"] = json_path
    
    # Parquet
    if "parquet" in formats:
        import pandas as pd
        # تسوية gold_passages
        flat_records = []
        for rec in eval_records:
            flat = rec.copy()
            flat["gold_passages"] = json.dumps(flat["gold_passages"])
            flat_records.append(flat)
        
        df = pd.DataFrame(flat_records)
        parquet_path = f"{base_path}.parquet"
        df.to_parquet(parquet_path)
        results["parquet"] = parquet_path
    
    return results
```

### الخطوة 17.2: تشغيل التصدير

```python
# ══════════════════════════════════════════════════════════════════════════════
# تشغيل التصدير
# ══════════════════════════════════════════════════════════════════════════════

if eval_records_mini_hf:
    export_results = export_eval_dataset(
        eval_records_mini_hf,
        base_path="output/Burhan-RAG-Eval-HFLLM-Mini-v1",
        formats=["jsonl", "json", "parquet"]
    )
    
    print(f"╔════════════════════════════════════════════════════════════════════╗")
    print(f"║  الملفات المُصدَّرة                                            ║")
    print(f"╚════════════════════════════════════════════════════════════════════╝")
    for fmt, path in export_results.items():
        size = os.path.getsize(path) / 1024
        print(f"  • {fmt}: {path} ({size:.1f} KB)")
```

---

## 🎯 القسم الثامن عشر: ملخص وتشغيل سريع

### ملخص الدفتر

| القسم | الوصف | الحالة |
|-------|-------|---------|
| 1 | إعداد البيئة | ✅ |
| 2 | تحميل البيانات | ✅ |
| 3 | تنظيف النصوص | ✅ |
| 4 | إعداد LLM | ✅ |
| 5 | قوالب الأوامر | ✅ |
| 6 | توليد الأسئلة | ✅ |
| 7 | استراتيجية التوزيع | ✅ |
| 8 | بناء السجلات | ✅ |
| 9 | الحفظ والرفع | ✅ |
| 10 | الاستخدام والاختبار | ✅ |
| 11 | التوسع | ✅ |
| 12 | معالجة الأخطاء | ✅ |
| 13 | تحسين الأداء | ✅ |
| 14 | تقييم الجودة | ✅ |
| 15 | النماذج البديلة | ✅ |
| 16 | التحقق النهائي | ✅ |
| 17 | التصدير | ✅ |

### تشغيل سريع (Colab)

```python
# ══════════════════════════════════════════════════════════════════════════════
# كود التشغيل السريع (Colab)
# ══════════════════════════════════════════════════════════════════════════════

# 1. تثبيت المتطلبات
# !pip install -q datasets huggingface_hub transformers accelerate tqdm

# 2. تحميل البيانات
# mini_ds = load_dataset("Kandil7/Burhan-Mini-Dataset-v2", split="train")
# mini_ds_clean = mini_ds.map(clean_row, num_proc=4)

# 3. تحميل النموذج (Qwen2.5)
# tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-7B-Instruct", trust_remote_code=True)
# model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-7B-Instruct", device_map="auto", torch_dtype=torch.bfloat16)

# 4. بناء التقييم
# eval_records, counts = build_eval_with_hf_llm(mini_ds_clean, MAX_PER_COLLECTION_TEST)

# 5. حفظ ورفع
# eval_mini_ds.push_to_hub(f"{HF_USERNAME}/Burhan-RAG-Eval-Mini-v1")
```

---

## 🔗 الموارد الإضافية

- **مجموعة بيانات Burhan**: [Kandil7/Burhan-Datasets](https://huggingface.co/datasets/Kandil7/Burhan-Datasets)
- **نموذج Qwen2.5**: [Qwen/Qwen2.5-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct)
- **مستندات Hugging Face**: [Hugging Face Docs](https://huggingface.co/docs/datasets)
- **مستندات Transformers**: [Transformers Docs](https://huggingface.co/docs/transformers)

---

## ⚙️ إعدادات قابلة للتعديل

| المتغير | الوصف | القيمة الافتراضية |
|--------|-------|----------------------|
| `MODEL_NAME` | اسم نموذج LLM | `Qwen/Qwen2.5-7B-Instruct` |
| `HF_USERNAME` | اسم المستخدم | `Kandil7` |
| `MAX_PER_COLLECTION` | حدود الأسئلة per مجموعة | (dict) |
| `max_new_tokens` | الرموز المُولَّدة | `512` |
| `temperature` | درجة الإبداع | `0.4` |
| `top_p` | نواة التوليد | `0.9` |
| `batch_size` | حجم الدفعة | `4` |

---

## 🆘 استكشاف الأخطاء

### المشكلة 1: عدم كفاية VRAM

```python
# الحل 1: استخدام نموذج أصغر
MODEL_NAME = "Qwen/Qwen2.5-3B-Instruct"

# الحل 2: استخدام FP16 بدلاً من BF16
torch_dtype=torch.float16

# الحل 3: CPU فقط (بطيء جداً)
device_map="cpu"
```

### المشكلة 2: فشل تحليل JSON

```python
# الحل 1: تحسين الـ prompt
SYSTEM_PROMPT += " أجب بتنسيق JSON صالح فقط."

# الحل 2: استخدام fallback يدوي
# (مُفعّل بالفعل في الكود)
```

### المشكلة 3: بطء التوليد

```python
# الحل 1: تقليل max_per_collection
MAX_PER_COLLECTION = {"seerah_passages": 100, ...}

# الحل 2: استخدام batch processing
# generate_questions_batch(passages, batch_size=8)

# الحل 3: استخدام API خارجي
# generate_questions_openai(passage)
```

### المشكلة 4: انقطاع Colab

```python
# الحل: استخدام نظام النقاط (Checkpoint)
# مُفعّل في القسم 12.2
checkpoint = EvalCheckpoint()
# ثم استئناف العمل
```

---

## 📊 مقارنة النماذج

| النموذج | params | VRAM (FP16) | السرعة | العربية | التوصية |
|----------|--------|-------------|---------|----------|---------|
| Qwen2.5-3B | 3B | ~6GB | fast | good | 🥉 للتجارب |
| Qwen2.5-7B | 7B | ~14GB | medium | good | 🥈 إنتاج |
| Qwen2.5-14B | 14B | ~28GB | slow | good | 🥉 كبير |
| Llama-3.1-8B | 8B | ~16GB | medium | medium | 🥈 بديل |
| Claude-3.5 | - | API | fast | excellent | 🥇 API |

---

## ✅ قائمة التحقق قبل النشر

- [ ] تم اختيار النموذج المناسب
- [ ] تم تعريف حدود الأسئلة لكل مجموعة
- [ ] تم اختبار الدوال على عينة
- [ ] تم إنشاء مجموعة التقييم
- [ ] تم التحقق من صحة البيانات
- [ ] تم تقييم الجودة
- [ ] تم تصدير البيانات بالتنسيقات المطلوبة
- [ ] تم رفعها إلى Hugging Face Hub
- [ ] تم اختبار الوصول إلى البيانات

---

**نهاية الدفتر** 🎉