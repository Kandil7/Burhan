"""Upload README with simplified YAML metadata."""

import os
from dotenv import load_dotenv
from huggingface_hub import HfApi

load_dotenv()
api = HfApi()
token = os.environ.get("HF_TOKEN")

# Simple YAML metadata (no complex features to avoid dtype issues)
readme_content = """---
annotations:
  train:
  - - question
    - text
  test:
  - - question
    - text
card:
  certified: false
  cohorts: []
  description: 100K Arabic Islamic passages for QA/RAG systems across 10 major Islamic collections
  homepage: https://Burhan.islamic
  license: cc-by-4.0
  papers: []
  pretty_name: Burhan Mini Dataset v2
  size_categories:
  - n<1M
  task_categories:
  - qa
  task_ids:
  - open-domain-qa
  languages:
  - ar
  tags:
  - arabic
  - islamic
  - qa
  - rag
splits:
  test:
    description: 5% test split
    num_examples: 5000
  train:
    description: 95% train split
    num_examples: 95000
supervision:
  field: content
  types: []
---

# Burhan Mini Dataset v2

100,000 Arabic Islamic passages for QA/RAG systems across 10 major collections.

## Dataset Overview

| Property | Value |
|----------|-------|
| Total Passages | 100,000 |
| Collections | 10 |
| Passages per Collection | 10,000 |
| Language | Arabic |
| Format | JSONL |

## Collections

1. **aqeedah_passages** - العقيدة (Islamic Theology/Aqeedah)
   - Topics: Tawhid, Attributes of Allah, Iman, Kufr, Shirk
   
2. **arabic_language_passages** - اللغة العربية (Arabic Language)
   - Topics: Arabic grammar, morphology, rhetoric

3. **fiqh_passages** - الفقه (Islamic Jurisprudence)
   - Topics: Fiqh of worship, transactions, family, inheritance

4. **general_islamic** - عام إسلامي (General Islamic)
   - Topics: General Islamic knowledge

5. **hadith_passages** - الحديث (Hadith)
   - Topics: Hadith sciences, collections

6. **islamic_history_passages** - التاريخ الإسلامي (Islamic History)
   - Topics: Early Islamic caliphates, scholars

7. **quran_tafsir** - تفسير القرآن (Quran Tafsir)
   - Topics: Quranic exegesis, tafsir sciences

8. **seerah_passages** - السيرة (Prophet's Biography)
   - Topics: Life of Prophet Muhammad

9. **spirituality_passages** - الروحانيات (Spirituality)
   - Topics: Tasawwuf, dhikr, dua

10. **usul_fiqh** - أصول الفقه (Principles of Fiqh)
    - Topics: Usul al-Fiqh, qiyas, ijma

## Data Schema

```json
{
  "content": "Arabic text passage...",
  "content_type": "page",
  "book_id": 1,
  "book_title": "Book Title",
  "category": "الفقه",
  "author": "Author Name",
  "author_death": 1225,
  "collection": "fiqh_passages",
  "page_number": 1,
  "section_title": "Section Title",
  "hierarchy": ["Book Title", "Section Title"]
}
```

## Use Cases

- Arabic Islamic QA systems
- RAG for Islamic knowledge
- Fine-tuning Arabic LLMs
- Islamic chatbots

## Example Usage

```python
from datasets import load_dataset
dataset = load_dataset("Kandil7/Burhan-Mini-Dataset-v2")
```

## License

CC BY 4.0

## Related

- [Burhan-Islamic-QA](https://huggingface.co/datasets/Kandil7/Burhan-Islamic-QA)
"""

# Save and upload
with open("README.md", "w", encoding="utf-8") as f:
    f.write(readme_content)

print("README.md created")

api.upload_file(
    path_or_fileobj=open("README.md", "rb"),
    path_in_repo="README.md",
    repo_id="Kandil7/Burhan-Mini-Dataset-v2",
    repo_type="dataset",
    token=token,
    commit_message="Simplify YAML metadata",
)

print("Uploaded successfully!")
