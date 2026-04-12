#!/usr/bin/env python3
"""Verify contents of HuggingFace embeddings repository."""

import os
from dotenv import load_dotenv
load_dotenv()

try:
    from huggingface_hub import HfApi, login, hf_hub_download, list_repo_files
except ImportError:
    print("❌ huggingface_hub not installed")
    print("   Install: poetry add huggingface_hub")
    exit(1)

HF_TOKEN = os.environ.get("HF_TOKEN")
REPO_ID = "Kandil7/Athar-Embeddings"

def verify_repo():
    """List all files and their sizes in the embeddings repo."""
    if not HF_TOKEN:
        print("❌ HF_TOKEN not set in .env")
        exit(1)

    print("🔐 Logging in to HuggingFace...")
    login(token=HF_TOKEN)
    
    api = HfApi()
    
    try:
        print(f"\n📂 Repository: {REPO_ID}")
        print("="*70)
        
        # List all files
        files = api.list_repo_files(repo_id=REPO_ID, repo_type="dataset")
        
        print(f"📁 Total files: {len(files)}")
        print()
        
        if not files:
            print("⚠️  Repository is empty!")
            return
        
        # Show file structure
        print("📋 File Structure:")
        print("-"*70)
        for f in sorted(files):
            print(f"  - {f}")
        
        print()
        print("="*70)
        print("✅ Repository exists and is accessible with your token!")
        
    except Exception as e:
        print(f"❌ Failed to access repository: {e}")
        print()
        print("Possible reasons:")
        print("  1. Repository doesn't exist yet (needs to be created)")
        print("  2. Token doesn't have write access to this repo")
        print("  3. Repository is private and token is invalid")
        return

if __name__ == "__main__":
    verify_repo()
