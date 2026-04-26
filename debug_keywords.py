#!/usr/bin/env python3
"""Debug keyword classifier directly."""

import re
import io
import sys

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def normalize_arabic(text: str) -> str:
    """Robust Arabic text normalization for keyword matching."""
    if not text:
        return ""
    text = re.sub(r"[\u064B-\u065F\u0670]", "", text)
    text = re.sub(r"[إأآٱ]", "ا", text)
    text = text.replace("ة", "ه").replace("ى", "ي")
    text = re.sub(r"\s+", " ", text).strip()
    return text.lower()


# Simulating KeywordBasedClassifier
FIQH_KEYWORDS = [
    "حكم",
    "يجوز",
    "حلال",
    "حرام",
    "فتوى",
    "واجب",
    "سنة",
    "مستحب",
    "مكروه",
    "مباح",
    "نفل",
    "قربة",
    "صلاة",
    "صوم",
    "زكاة",
    "حج",
    "عمرة",
    "طهارة",
    "وضوء",
    "جنابة",
    "غسل",
]

# Pre-normalize
_norm_keywords = [normalize_arabic(kw) for kw in FIQH_KEYWORDS]

results = []


def classify_keyword(query: str):
    """Simulate keyword classification."""
    if not query or not query.strip():
        return 0.0, "Empty query"

    norm_query = normalize_arabic(query)

    # Count matches
    matches = {}
    for i, pattern in enumerate(_norm_keywords):
        if pattern in norm_query:
            intent = "fiqh"
            if intent not in matches:
                matches[intent] = 0
            matches[intent] += 1

    if not matches:
        return 0.0, "No keywords matched"

    # Best match
    best_intent = max(matches, key=matches.get)
    count = matches[best_intent]

    # Confidence
    if count == 1:
        confidence = 0.7
    elif count == 2:
        confidence = 0.85
    else:
        confidence = 0.95

    return confidence, f"Matched {count} keywords for {best_intent}"


# Test queries
test_queries = [
    "صلاة",
    "ما حكم الصلاة؟",
    "زكاة",
    "حج",
    "غزوة بدر",
    "هجرة",
]

for q in test_queries:
    conf, reason = classify_keyword(q)
    results.append(f"Query: '{q}' -> confidence: {conf}, reason: {reason}")

# Write
with open("debug_keywords_output.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(results))

print("Done")
