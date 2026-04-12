#!/usr/bin/env python3
"""Fix all hardcoded openai_model references to use settings.llm_model."""
import os

files_to_fix = [
    "src/core/router.py",
    "src/quran/quran_router.py",
    "src/agents/arabic_language_agent.py",
    "src/agents/aqeedah_agent.py",
    "src/agents/base_rag_agent.py",
    "src/infrastructure/llm_client.py",
    "src/agents/tafsir_agent.py",
    "src/agents/hadith_agent.py",
    "src/agents/fiqh_usul_agent.py",
    "src/agents/islamic_history_agent.py",
    "src/agents/general_islamic_agent.py",
    "src/agents/seerah_agent.py",
    "src/agents/fiqh_agent.py",
]

count = 0
for f in files_to_fix:
    if not os.path.exists(f):
        continue
    with open(f, "r", encoding="utf-8") as fh:
        content = fh.read()
    new = content.replace("settings.openai_model", "settings.llm_model")
    if new != content:
        with open(f, "w", encoding="utf-8") as fh:
            fh.write(new)
        count += 1
        print(f"Fixed: {f}")

print(f"Total fixed: {count} files")
