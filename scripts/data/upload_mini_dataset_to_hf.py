#!/usr/bin/env python3
"""
Upload Mini Dataset V2 to HuggingFace

Uploads the mini_dataset_v2 (100K records) to HuggingFace datasets.
"""

import os
import json
from pathlib import Path

# Set environment to use .env
from dotenv import load_dotenv

load_dotenv()

from huggingface_hub import HfApi, create_repo


# Configuration
DATASET_NAME = "Athar-Datasets"
DATASET_REPO_ID = f"Kandil7/{DATASET_NAME}"
DATASET_DIR = Path("data/mini_dataset_v2")
LOCAL_TOKEN = os.getenv("HF_TOKEN") or os.getenv("HF_HUB_TOKEN")


def main():
    """Upload mini dataset to HuggingFace."""

    if not LOCAL_TOKEN:
        print("ERROR: HF_TOKEN not found in environment!")
        print("Please add HF_TOKEN to your .env file")
        return

    print("=" * 60)
    print("Uploading Mini Dataset V2 to HuggingFace")
    print("=" * 60)

    # Initialize API
    api = HfApi(token=LOCAL_TOKEN)

    # Check if repo exists (skip if exists, create if not)
    try:
        api.repo_info(repo_id=DATASET_REPO_ID, repo_type="dataset")
        print(f"Repository {DATASET_REPO_ID} already exists, will upload files...")
    except Exception:
        # Create repo
        print(f"Creating repository: {DATASET_REPO_ID}")
        create_repo(
            repo_id=DATASET_REPO_ID,
            repo_type="dataset",
            token=LOCAL_TOKEN,
            private=False,
        )
        print("Repository created!")

    # Upload each file
    files = sorted(DATASET_DIR.glob("*.jsonl"))

    print(f"\nFound {len(files)} JSONL files to upload:")
    for f in files:
        print(f"  - {f.name} ({f.stat().st_size / 1024 / 1024:.1f} MB)")

    print("\nUploading files...")

    # Upload folder
    api.upload_folder(
        folder_path=str(DATASET_DIR),
        repo_id=DATASET_REPO_ID,
        repo_type="dataset",
        commit_message="Upload Athar Mini Dataset V2 (100K records)",
    )

    print("\n" + "=" * 60)
    print("Upload Complete!")
    print("=" * 60)
    print(f"\nDataset URL: https://huggingface.co/datasets/{DATASET_REPO_ID}")
    print("\nTo load the dataset:")
    print(f"  from datasets import load_dataset")
    print(f'  ds = load_dataset("{DATASET_REPO_ID}")')


if __name__ == "__main__":
    main()
