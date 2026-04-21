#!/usr/bin/env python3
"""
Quick RAG Data Seeder for Athar Islamic QA System.

Seeds sample fiqh and general Islamic passages into Qdrant
with embeddings to enable RAG search.

Usage:
    python scripts/seed_rag_quick.py
"""

import sys
import asyncio
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.indexing.embeddings.embedding_model import EmbeddingModel
from src.indexing.vectorstores.qdrant_store import VectorStore
from src.config.logging_config import setup_logging

setup_logging()

# Sample fiqh passages
FIQH_PASSAGES = [
    {
        "content": "حكم صلاة الجماعة: صلاة الجماعة سنة مؤكدة عند جمهور العلماء، وواجبة عند الحنابلة في أصح الروايات. وقد واظب النبي ﷺ عليها ولم يتركها قط، وأمر بها أمته. قال ﷺ: 'صلاة الجماعة أفضل من صلاة الفذ بسبع وعشرين درجة'. رواه البخاري ومسلم.",
        "metadata": {"source": "Fiqh al-Sunnah", "type": "fiqh_book", "language": "ar", "topic": "prayer"},
    },
    {
        "content": "حكم الزكاة: الزكاة ركن من أركان الإسلام الخمسة، وهي فرض عين على كل مسلم ملك نصاباً وحال عليه الحول. قال تعالى: ﴿وَأَقِيمُوا الصَّلَاةَ وَآتُوا الزَّكَاةَ﴾. والنصاب في الذهب 85 غراماً، وفي الفضة 595 غراماً، ومقدار الزكاة 2.5% من المال.",
        "metadata": {"source": "Al-Fiqh al-Islami", "type": "fiqh_book", "language": "ar", "topic": "zakat"},
    },
    {
        "content": "حكم الصيام: صيام رمضان فرض عين على كل مسلم بالغ عاقل قادر مقيم. قال تعالى: ﴿يَا أَيُّهَا الَّذِينَ آمَنُوا كُتِبَ عَلَيْكُمُ الصِّيَامُ كَمَا كُتِبَ عَلَى الَّذِينَ مِن قَبْلِكُمْ لَعَلَّكُمْ تَتَّقُونَ﴾. ويفطر المريض والمسافر ويقضيان لاحقاً.",
        "metadata": {"source": "Subul al-Salam", "type": "fiqh_book", "language": "ar", "topic": "fasting"},
    },
    {
        "content": "حكم الحج: الحج ركن من أركان الإسلام، فرض مرة واحدة في العمر على كل مسلم بالغ عاقل حر مستطيع بدناً ومالاً. قال تعالى: ﴿وَلِلَّهِ عَلَى النَّاسِ حِجُّ الْبَيْتِ مَنِ اسْتَطَاعَ إِلَيْهِ سَبِيلًا﴾. ويحج المسلم مرة واحدة وما شاء بعد ذلك تطوعاً.",
        "metadata": {"source": "Bulugh al-Maram", "type": "fiqh_book", "language": "ar", "topic": "hajj"},
    },
    {
        "content": "The ruling on Friday prayer (Jumu'ah): It is obligatory (fard 'ayn) on every adult sane Muslim male who is resident. Allah says: 'O you who believe, when the call is made for prayer on Friday, hasten to the remembrance of Allah.' Women, children, travelers and the sick are exempted. The prayer consists of a khutbah (sermon) followed by two rak'ahs.",
        "metadata": {"source": "Reliance of the Traveller", "type": "fiqh_book", "language": "en", "topic": "jumuah"},
    },
]

# Sample general Islamic passages
GENERAL_PASSAGES = [
    {
        "content": "عمر بن الخطاب رضي الله عنه: هو أبو حفص عمر بن الخطاب القرشي العدوي، ثاني الخلفاء الراشدين. أسلم في السنة السادسة من البعثة، وهاجر إلى المدينة. بويع بالخلافة بعد أبي بكر الصديق رضي الله عنه سنة 13 هـ. عُرف بالعدل والشدة في الحق. استشهد سنة 23 هـ.",
        "metadata": {
            "source": "Siyar A'lam al-Nubala",
            "type": "islamic_history",
            "language": "ar",
            "topic": "companions",
        },
    },
    {
        "content": "التوحيد: هو إفراد الله سبحانه وتعالى بالعبادة، وهو أساس دعوة جميع الرسل والأنبياء. أركانه ثلاثة: توحيد الربوبية (إفراد الله بالخلق والملك والتدبير)، وتوحيد الألوهية (إفراد الله بالعبادة)، وتوحيد الأسماء والصفات (إثبات ما أثبته الله لنفسه من الأسماء والصفات).",
        "metadata": {"source": "Al-Tawhid", "type": "islamic_theology", "language": "ar", "topic": "tawheed"},
    },
    {
        "content": "The Prophet Muhammad ﷺ: Muhammad ibn Abdullah, the final prophet and messenger of Allah, was born in Mecca in the Year of the Elephant (570 CE). He received the first revelation at age 40 in the Cave of Hira through Angel Jibreel. He preached monotheism for 23 years, established the Islamic state in Medina, and passed away in 632 CE at age 63.",
        "metadata": {"source": "Ar-Raheeq Al-Makhtum", "type": "seerah", "language": "en", "topic": "prophet"},
    },
    {
        "content": "الإيمان بالله: هو التصديق الجازم بوجود الله تعالى وإفراده بالربوبية والألوهية والأسماء والصفات. وأركان الإيمان ستة: الإيمان بالله، وملائكته، وكتبه، ورسله، واليوم الآخر، والقدر خيره وشره. وهو أساس الدين وأصله الذي عليه مدار جميع التعاليم الإسلامية.",
        "metadata": {
            "source": "Al-Aqeedah al-Tahawiyyah",
            "type": "islamic_theology",
            "language": "ar",
            "topic": "faith",
        },
    },
    {
        "content": "Ramadan: The ninth month of the Islamic calendar, in which the Quran was revealed. It is a month of fasting, prayer, and reflection. Muslims fast from dawn to sunset, abstaining from food, drink, and sinful acts. The night of Laylat al-Qadr falls in the last ten nights and is better than a thousand months. The month ends with Eid al-Fitr.",
        "metadata": {
            "source": "Islamic Calendar Guide",
            "type": "islamic_knowledge",
            "language": "en",
            "topic": "ramadan",
        },
    },
]


async def seed_rag_data():
    """Seed sample data into Qdrant with embeddings."""
    print("\n" + "=" * 60)
    print("🌱 ATHAR RAG DATA SEEDER")
    print("=" * 60 + "\n")

    # Initialize embedding model
    print("📥 Loading embedding model...")
    embedder = EmbeddingModel()
    await embedder.load_model()
    print(f"✓ Model loaded: {embedder.MODEL_NAME}")
    print(f"  Device: {embedder.device}")
    print()

    # Initialize vector store
    print("📊 Connecting to Qdrant...")
    store = VectorStore()
    await store.initialize()
    print("✓ Connected to Qdrant\n")

    # Seed fiqh passages
    print("📚 Seeding Fiqh passages...")
    fiqh_texts = [p["content"] for p in FIQH_PASSAGES]
    fiqh_embeddings = await embedder.encode(fiqh_texts)
    await store.upsert("fiqh_passages", FIQH_PASSAGES, fiqh_embeddings)
    print(f"  ✓ Seeded {len(FIQH_PASSAGES)} fiqh passages\n")

    # Seed general passages
    print("📚 Seeding General Islamic passages...")
    general_texts = [p["content"] for p in GENERAL_PASSAGES]
    general_embeddings = await embedder.encode(general_texts)
    await store.upsert("general_islamic", GENERAL_PASSAGES, general_embeddings)
    print(f"  ✓ Seeded {len(GENERAL_PASSAGES)} general passages\n")

    # Show stats
    print("=" * 60)
    print("✓ RAG DATA SEEDED SUCCESSFULLY!")
    print("=" * 60 + "\n")

    stats = store.get_collection_stats("fiqh_passages")
    print(f"  Fiqh passages: {stats.get('vectors_count', 0)}")
    stats = store.get_collection_stats("general_islamic")
    print(f"  General passages: {stats.get('vectors_count', 0)}")
    print()

    # Test search
    print("🔍 Testing search...")
    test_query = "ما حكم صلاة الجماعة؟"
    query_emb = await embedder.encode_query(test_query)
    results = await store.search("fiqh_passages", query_emb, top_k=2)
    if results:
        print(f"  ✓ Search returned {len(results)} results")
        print(f"  Top result score: {results[0].get('score', 0):.3f}")
    else:
        print("  ✗ Search returned no results")
    print()


if __name__ == "__main__":
    asyncio.run(seed_rag_data())
