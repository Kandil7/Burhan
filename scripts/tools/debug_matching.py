#!/usr/bin/env python3
"""Debug keyword matching with the actual classifier."""

import asyncio
import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import only what's needed without going through router
from src.domain.intents import Intent
from src.domain.models import ClassificationResult


def normalize_arabic(text: str) -> str:
    """Robust Arabic text normalization for keyword matching."""
    if not text:
        return ""
    # Strip diacritics (tashkeel)
    text = re.sub(r"[\u064B-\u065F\u0670]", "", text)
    # Unify Alef variants
    text = re.sub(r"[إأآٱ]", "ا", text)
    # Unify Ta-Marbuta and Ya
    text = text.replace("ة", "ه").replace("ى", "ي")
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text.lower()


# Test with actual FIQH keywords
FIQH_KEYWORDS = [
    "صلاة",
    "صلاه",
    "صوم",
    "صيام",
    "زكاة",
    "زكاه",
    "حج",
    "عمرة",
    "طهارة",
    "طهاره",
    "وضوء",
    "غسل",
    "جنابة",
    "حكم",
    "يجوز",
    "حلال",
    "حرام",
    "فتوى",
    "واجب",
    "سنة",
]

# Pre-normalize keywords
norm_keywords = [normalize_arabic(kw) for kw in FIQH_KEYWORDS]

# Test queries
queries = ["صلاة", "صلاه", "ما حكم الصلاة؟"]

results = []
results.append("Normalized keywords: " + str(norm_keywords[:10]))

for query in queries:
    norm_query = normalize_arabic(query)
    results.append(f"\nQuery: '{query}' -> '{norm_query}'")

    matches = []
    for i, pattern in enumerate(norm_keywords):
        if pattern in norm_query:
            matches.append((FIQH_KEYWORDS[i], pattern))

    results.append(f"  Matches: {matches}")
    results.append(f"  Match count: {len(matches)}")

# Write to file
with open("debug_output.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(results))

print("Done - results in debug_output.txt")
