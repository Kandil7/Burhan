#!/usr/bin/env python3
"""
Import script for azkar-db from https://github.com/osamayy/azkar-db

Downloads azkar database and converts to Athar's dua format.

Usage:
    python scripts/import_azkar_db.py
"""
import json
import csv
import httpx
from pathlib import Path

AZKAR_DB_URL = "https://github.com/osamayy/azkar-db/raw/refs/heads/main/azkar.json"
OUTPUT_PATH = Path(__file__).parent.parent / "data" / "seed" / "azkar_imported.json"

def import_azkar():
    """Import azkar-db and convert to Athar format."""
    print("📥 Downloading azkar-db...")
    
    try:
        response = httpx.get(AZKAR_DB_URL, follow_redirects=True)
        response.raise_for_status()
        azkar_data = response.json()
        
        print(f"✅ Downloaded {len(azkar_data)} azkar entries")
        
        # Convert to Athar format
        athar_duas = []
        for i, zikr in enumerate(azkar_data, 1):
            dua = {
                "id": i,
                "category": zikr.get("category", "general"),
                "occasion": zikr.get("search", ""),
                "arabic_text": zikr.get("zekr", ""),
                "translation": "",  # Would need separate translation source
                "transliteration": "",
                "source": zikr.get("reference", "Azkar Database"),
                "reference": zikr.get("reference", ""),
                "narrator": "",
                "grade": "",
                "repeat_count": zikr.get("count", 1),
                "virtues": zikr.get("description", ""),
                "search_keywords": zikr.get("search", "")
            }
            athar_duas.append(dua)
        
        # Save converted data
        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(athar_duas, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Converted and saved to {OUTPUT_PATH}")
        print(f"📊 Total entries: {len(athar_duas)}")
        
        # Show sample
        print("\n📝 Sample Entry:")
        print("-" * 60)
        if athar_duas:
            sample = athar_duas[0]
            print(f"Category: {sample['category']}")
            print(f"Arabic: {sample['arabic_text'][:80]}...")
            print(f"Repeat: {sample['repeat_count']}")
            print(f"Reference: {sample['reference']}")
        
        return len(athar_duas)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 0


if __name__ == "__main__":
    import_azkar()
