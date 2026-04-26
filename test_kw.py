#!/usr/bin/env python3
"""Minimal keyword test."""

import re


def normalize(text):
    if not text:
        return ""
    text = re.sub(r"[\u064B-\u065F\u0670]", "", text)
    text = re.sub(r"[إأآٱ]", "ا", text)
    text = text.replace("ة", "ه").replace("ى", "ي")
    return text.lower().strip()


# Keywords from INTENT_KEYWORDS[Intent.FIQH]
keywords = ["صلاة", "صلاه", "صوم", "صيام", "زكاة", "زكاه", "حج", "عمرة"]
norm_kw = [normalize(k) for k in keywords]

query = "صلاة"
norm_q = normalize(query)

matches = [k for k in norm_kw if k in norm_q]

# Write result to file
with open("test_result.txt", "w", encoding="utf-8") as f:
    f.write(f"Query: {query} -> normalized: {norm_q}\n")
    f.write(f"Keywords: {norm_kw}\n")
    f.write(f"Matches: {matches}\n")
    f.write(f"Match count: {len(matches)}\n")
    if len(matches) > 0:
        f.write("SUCCESS: Keyword matched!\n")
    else:
        f.write("FAILED: No match\n")

print("Done - check test_result.txt")
