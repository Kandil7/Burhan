#!/usr/bin/env python3
"""
Upload remaining Mini Dataset V2 files.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from huggingface_hub import HfApi

REPO_ID = "Kandil7/Athar-Mini-Dataset-v2"
DATASET_DIR = Path("data/mini_dataset_v2")
LOCAL_TOKEN = os.getenv("HF_TOKEN") or os.getenv("HF_HUB_TOKEN")

# All files to upload
ALL_FILES = [
    "aqeedah_passages.jsonl",
    "arabic_language_passages.jsonl",
    "fiqh_passages.jsonl",
    "general_islamic.jsonl",
    "hadith_passages.jsonl",
    "islamic_history_passages.jsonl",
    "quran_tafsir.jsonl",
    "seerah_passages.jsonl",
    "spirituality_passages.jsonl",
    "usul_fiqh.jsonl",
    "stats.json",
]


def main():
    api = HfApi(token=LOCAL_TOKEN)

    # Check what's already there
    existing = api.list_repo_files(repo_id=REPO_ID, repo_type="dataset")
    print("Existing files:", existing)

    # Upload remaining
    for fname in ALL_FILES:
        if fname in existing:
            print(f"Skipping {fname} (already exists)")
            continue

        fpath = DATASET_DIR / fname
        if not fpath.exists():
            print(f"Skipping {fname} (file not found)")
            continue

        print(f"Uploading {fname}...")

        with open(fpath, "rb") as f:
            api.upload_file(
                path_or_fileobj=f,
                path_in_repo=fname,
                repo_id=REPO_ID,
                repo_type="dataset",
                commit_message=f"Upload {fname}",
            )
        print(f"  Done: {fname}")

    print("\nComplete!")


if __name__ == "__main__":
    main()
