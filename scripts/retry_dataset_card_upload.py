#!/usr/bin/env python3
"""
Retry upload with better error handling and longer delays.
"""

import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

try:
    from huggingface_hub import HfApi, login
except ImportError:
    print("❌ huggingface_hub not installed")
    sys.exit(1)


def main():
    REPO_ID = os.environ.get("HF_REPO_ID", "Kandil7/Athar-Datasets")
    HF_TOKEN = os.environ.get("HF_TOKEN")

    if not HF_TOKEN:
        print("❌ HF_TOKEN not set")
        sys.exit(1)

    readme_path = Path(__file__).parent / "dataset_card_readme.md"

    if not readme_path.exists():
        print(f"❌ README not found: {readme_path}")
        sys.exit(1)

    api = HfApi()
    login(token=HF_TOKEN)

    max_retries = 10
    for attempt in range(1, max_retries + 1):
        try:
            print(f"📤 Attempt {attempt}/{max_retries}...")
            api.upload_file(
                path_or_fileobj=str(readme_path),
                path_in_repo="README.md",
                repo_id=REPO_ID,
                repo_type="dataset",
            )
            print(f"✅ README uploaded successfully!")
            print(f"🔗 View at: https://huggingface.co/datasets/{REPO_ID}")
            return

        except Exception as e:
            if "503" in str(e):
                wait = min(30, 2 ** attempt)
                print(f"⏳ HuggingFace server busy (503). Waiting {wait}s...")
                time.sleep(wait)
            else:
                print(f"❌ Failed: {e}")
                sys.exit(1)

    print(f"❌ Failed after {max_retries} attempts. HuggingFace may be down.")
    print("   Try again later.")


if __name__ == "__main__":
    main()
