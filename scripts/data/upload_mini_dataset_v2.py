#!/usr/bin/env python3
"""
Upload Mini Dataset V2 to a separate HuggingFace repository.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from huggingface_hub import HfApi, create_repo

# Configuration
DATASET_NAME = "Burhan-Mini-Dataset-v2"
REPO_ID = f"Kandil7/{DATASET_NAME}"
DATASET_DIR = Path("data/mini_dataset_v2")
LOCAL_TOKEN = os.getenv("HF_TOKEN") or os.getenv("HF_HUB_TOKEN")


def main():
    if not LOCAL_TOKEN:
        print("ERROR: HF_TOKEN not found in environment!")
        print("Please add HF_TOKEN to your .env file")
        return

    print("=" * 60)
    print(f"Uploading Mini Dataset V2 to {REPO_ID}")
    print("=" * 60)

    api = HfApi(token=LOCAL_TOKEN)

    # Check if repo exists, create if not
    try:
        api.repo_info(repo_id=REPO_ID, repo_type="dataset")
        print(f"Repository {REPO_ID} already exists")
    except Exception:
        print(f"Creating repository: {REPO_ID}")
        create_repo(
            repo_id=REPO_ID,
            repo_type="dataset",
            token=LOCAL_TOKEN,
            private=False,
        )
        print("Repository created!")

    # List files to upload
    files = sorted(DATASET_DIR.glob("*.jsonl"))
    print(f"\nFound {len(files)} JSONL files to upload:")
    for f in files:
        size_mb = f.stat().st_size / 1024 / 1024
        print(f"  - {f.name} ({size_mb:.1f} MB)")

    # Upload folder
    print("\nUploading files...")
    api.upload_folder(
        folder_path=str(DATASET_DIR),
        repo_id=REPO_ID,
        repo_type="dataset",
        commit_message="Upload Burhan Mini Dataset V2 (100K records, 10K per collection)",
    )

    print("\n" + "=" * 60)
    print("Upload Complete!")
    print("=" * 60)
    print(f"\nDataset URL: https://huggingface.co/datasets/{REPO_ID}")
    print("\nTo load the dataset:")
    print(f"  from datasets import load_dataset")
    print(f'  ds = load_dataset("{REPO_ID}")')


if __name__ == "__main__":
    main()
