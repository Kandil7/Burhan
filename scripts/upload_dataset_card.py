#!/usr/bin/env python3
"""
Upload Dataset Card (README.md) to HuggingFace.

Creates a comprehensive dataset card with:
- Collection descriptions
- Schema documentation
- Usage examples
- Statistics
- Citation info
- Era classification

Usage:
    poetry run python scripts/upload_dataset_card.py
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

try:
    from huggingface_hub import HfApi, login
    HAS_HF = True
except ImportError:
    print("❌ huggingface_hub not installed")
    print("   Install: poetry add huggingface_hub")
    sys.exit(1)


def main():
    # Configuration
    REPO_ID = os.environ.get("HF_REPO_ID", "Kandil7/Athar-Datasets")
    HF_TOKEN = os.environ.get("HF_TOKEN")

    if not HF_TOKEN:
        print("❌ HF_TOKEN not set in .env")
        sys.exit(1)

    # Read README
    readme_path = Path(__file__).parent / "dataset_card_readme.md"

    if not readme_path.exists():
        print(f"❌ README not found: {readme_path}")
        sys.exit(1)

    with open(readme_path, 'r', encoding='utf-8') as f:
        readme_content = f.read()

    print(f"📄 README size: {len(readme_content):,} characters")

    # Upload
    api = HfApi()
    login(token=HF_TOKEN)

    print(f"📤 Uploading README to {REPO_ID}...")

    try:
        api.upload_file(
            path_or_fileobj=str(readme_path),
            path_in_repo="README.md",
            repo_id=REPO_ID,
            repo_type="dataset",
        )
        print(f"✅ README uploaded successfully!")
        print(f"🔗 View at: https://huggingface.co/datasets/{REPO_ID}")

    except Exception as e:
        print(f"❌ Failed to upload README: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
