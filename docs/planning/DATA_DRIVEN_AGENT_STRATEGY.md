# 🕌 Athar Data-Driven Multi-Agent Architecture

**Based on complete analysis of 8,425 books (17.16 GB), 650K hadith, 41 categories**

---

## 📊 REAL DATA INVENTORY

### Super-Category Distribution

| Super-Category | Books | Size | % | Priority |
|----------------|-------|------|---|----------|
| **Hadith (Traditions)** | 2,135 | 4.6 GB | 26.8% | 🔴 P0 |
| **Fiqh (Jurisprudence)** | 1,519 | 3.8 GB | 22.2% | 🟡 P1 |
| **History & Biography** | 1,072 | 2.6 GB | 15.2% | 🟠 P2 |
| **Aqeedah (Creed)** | 945 | 0.7 GB | 11.2% | 🟡 P1 |
| **Arabic Language & Lit.** | 904 | 1.4 GB | 10.6% | 🔵 P3 |
| **Quran & Tafsir** | 725 | 2.1 GB | 12.3% | 🟡 P1 |
| **Spirituality & Ethics** | 619 | 0.4 GB | 7.3% | 🟠 P2 |
| **General & Reference** | 492 | 0.3 GB | 5.8% | 🔵 P3 |
| **Other** | 14 | 0.0 GB | 0.2% | - |

### Breakdown: Hadith Category (2,135 books, 4.6 GB)

| Sub-Category | Books | Size | Chunk Strategy |
|--------------|-------|------|----------------|
| كتب السنة | 1,226 | 1.7 GB | Individual hadith chunks |
| شروح الحديث | 262 | 1.6 GB | Per-hadith commentary |
| الجوامع | 135 | 0.8 GB | Individual hadith chunks |
| التخريج والأطراف | 123 | 0.4 GB | Per-hadith references |
| العلل والسؤلات الحديثية | 74 | 0.1 GB | Q&A format chunks |

### Breakdown: Fiqh Category (1,519 books, 3.8 GB)

| Sub-Category | Books | Size | Madhhab |
|--------------|-------|------|---------|
| الفقه العام | 204 | 0.5 GB | General |
| الفقه الحنفي | 83 | 0.4 GB | Hanafi |
| الفقه المالكي | 85 | 0.5 GB | Maliki |
| الفقه الشافعي | 86 | 0.7 GB | Shafi'i |
| الفقه الحنبلي | 147 | 0.6 GB | Hanbali |
| أصول الفقه | 247 | 0.4 GB | Principles (all) |
| الفتاوى | 64 | 0.5 GB | Fatwas (all) |
| علوم الفقه والقواعد | 55 | 0.1 GB | Legal maxims |
| السياسة الشرعية والقضاء | 100 | 0.1 GB | Islamic governance |
| الفرائض والوصايا | 28 | 0.0 GB | Inheritance |
| مسائل فقهية | 420 | 0.1 GB | Various fiqh issues |

### Breakdown: Arabic Language Category (904 books, 1.4 GB)

| Sub-Category | Books | Size |
|--------------|-------|------|
| النحو والصرف | 212 | 0.3 GB |
| الغريب والمعاجم | 129 | 0.4 GB |
| الأدب | 415 | 0.6 GB |
| البلاغة | 35 | 0.0 GB |
| الدواوين الشعرية | 25 | 0.0 GB |
| العروض والقوافي | 9 | 0.0 GB |
| كتب اللغة | 79 | 0.0 GB |

---

## 🎯 RECOMMENDED AGENT ARCHITECTURE

### Core Agents (Already Implemented)

| Agent | Collection | Vectors | Status |
|-------|-----------|---------|--------|
| **FiqhAgent** | fiqh_passages | 10,132 | ✅ Working |
| **SanadsetHadithAgent** | hadith_passages | 128 | ✅ Working |
| **QuranAgent** | PostgreSQL | 6,236 ayahs | ✅ Working |
| **TafsirAgent** | quran_tafsir | 0 | ⏳ Created, needs data |
| **AqeedahAgent** | aqeedah_passages | 0 | ⏳ Created, needs data |
| **SeerahAgent** | seerah_passages | 0 | ⏳ Created, needs data |
| **IslamicHistoryAgent** | islamic_history | 0 | ⏳ Created, needs data |
| **ArabicLanguageAgent** | arabic_language | 0 | ⏳ Created, needs data |
| **GeneralIslamicAgent** | general_islamic | 5 | ⏳ Created, needs data |
| **ChatbotAgent** | N/A | N/A | ✅ Working |

### Recommended New Agents

1. **FatwaAgent** (P1)
   - **Data:** 64 fatwa books, 0.5 GB
   - **Purpose:** Specific fatwa retrieval by scholar, topic, madhhab
   - **Collection:** `fatwa_passages`

2. **UsulFiqhAgent** (P2)
   - **Data:** 247 books on principles of jurisprudence
   - **Purpose:** Legal theory, methodology comparison
   - **Collection:** `usul_fiqh_passages` (already exists, needs data)

3. **MadhhabComparisonAgent** (P2)
   - **Data:** All 4 madhhab fiqh books
   - **Purpose:** Compare rulings across Hanafi, Maliki, Shafi'i, Hanbali
   - **Collections:** `hanafi_fiqh`, `maliki_fiqh`, `shafii_fiqh`, `hanbali_fiqh`

4. **NarratorAnalysisAgent** (P1)
   - **Data:** Sanadset narrator data, traجمat books
   - **Purpose:** Analyze narrator reliability, chain strength
   - **Collections:** `narrator_profiles`, `sanad_analysis`

5. **SpiritualityAgent** (P2)
   - **Data:** 619 books on riqaaq, adab, adhkar
   - **Purpose:** Spiritual guidance, ethical conduct
   - **Collection:** `spirituality_passages`

---

## 📝 OPTIMAL CHUNKING STRATEGY

### By Data Type

| Data Type | Chunk Size | Overlap | Boundary Rule | Metadata Fields |
|-----------|-----------|---------|---------------|-----------------|
| **Hadith** | 1 hadith | 0 | Complete hadith | sanad, matn, grade, book, number, narrators |
| **Quran Ayah** | 1 ayah | 0 | Natural | surah, ayah, juz, hizb, page |
| **Tafsir** | Per ayah | 50 chars | Ayah boundary | mufassir, book, surah:ayah, tafsir_text |
| **Fiqh Ruling** | 300-500 chars | 50 chars | Paragraph/chapter | book, author, madhhab, chapter, topic |
| **Fatwa** | Complete fatwa | 0 | Q&A boundary | mufti, question, answer, date, reference |
| **History/Bio** | 400-600 chars | 75 chars | Paragraph | book, author, period, person, place |
| **Spirituality** | 300-500 chars | 50 chars | Topic/chapter | book, author, topic, category |
| **Arabic Grammar** | Rule + examples | 50 chars | Complete rule | book, author, rule_type, examples |

### Estimated Total Chunks

| Collection | Est. Chunks | Embed Time (CPU) | Storage |
|------------|-------------|------------------|---------|
| sanadset_hadith | 650,986 | ~900 hours | ~2.6 GB |
| shamela_hadith | ~300,000 | ~400 hours | ~1.2 GB |
| quran_tafsir | ~50,000 | ~70 hours | ~200 MB |
| fiqh_all | ~800,000 | ~1100 hours | ~3.2 GB |
| aqeedah | ~100,000 | ~140 hours | ~400 MB |
| history_bio | ~500,000 | ~700 hours | ~2.0 GB |
| arabic_language | ~300,000 | ~400 hours | ~1.2 GB |
| spirituality | ~200,000 | ~280 hours | ~800 MB |
| **TOTAL** | **~2.9M** | **~4000 hours** | **~11.6 GB** |

---

## 🚀 IMPLEMENTATION PHASES

### Phase 1: Foundation (Week 1-2) ✅ Mostly Done
- ✅ SanadsetHadithAgent created
- ✅ FiqhAgent working with 10K vectors
- ✅ Query routing working
- ⏳ Embed remaining Sanadset hadith (650K - 128 done)

### Phase 2: Hadith Completion (Week 3-6)
- [ ] Process all Shamela hadith books (1,226 books)
- [ ] Create proper hadith chunking (per-hadith boundaries)
- [ ] Embed all hadith to Qdrant
- [ ] Add narrator search functionality
- **Target:** ~300K hadith vectors

### Phase 3: Quran + Tafsir (Week 7-8)
- [ ] Embed 6,236 Quran ayahs
- [ ] Process 270 tafsir books
- [ ] Create QuranTafsirAgent with multi-source retrieval
- **Target:** ~50K tafsir vectors

### Phase 4: Fiqh by Madhhab (Week 9-12)
- [ ] Categorize all fiqh books by madhhab
- [ ] Create separate collections per madhhab
- [ ] Build MadhhabComparisonAgent
- **Target:** ~800K fiqh vectors

### Phase 5: Aqeedah + Spirituality (Week 13-14)
- [ ] Process 945 aqeedah books
- [ ] Process 619 spirituality books
- [ ] Create SpiritualityAgent
- **Target:** ~300K vectors

### Phase 6: History + Language (Week 15-18)
- [ ] Process 1,072 history/biography books
- [ ] Process 904 Arabic language books
- [ ] Create NarratorAnalysisAgent
- **Target:** ~800K vectors

---

## 💡 IMMEDIATE NEXT STEPS

1. **Resume Sanadset embedding** (highest ROI)
   ```bash
   python scripts/embed_sanadset_hadith.py --limit 10000
   ```

2. **Create proper hadith chunker** for Shamela books
   - Each hadith = 1 chunk
   - Extract: sanad, matn, grade, book, number

3. **Seed Quran ayahs to vector store**
   - 6,236 ayahs with metadata
   - Fast: ~2 hours on CPU

4. **Process top 10 hadith books**
   - صحيح البخاري, صحيح مسلم, etc.
   - ~50K hadith from major collections

---

**Data Source:** Complete analysis of 8,425 books, 17.16 GB, 41 categories  
**Status:** Architecture designed, 10 agents created, embedding pipeline verified  
**Next:** Execute Phases 2-6 for full coverage
