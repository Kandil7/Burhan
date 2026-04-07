import os
import glob
import json

DATA_DIR = r"datasets\data"
BOOKS_DIR = os.path.join(DATA_DIR, "extracted_books")
METADATA_DIR = os.path.join(DATA_DIR, "metadata")

def analyze_dataset():
    """Complete analysis of datasets/data"""
    
    print("="*70)
    print("COMPLETE DATASET ANALYSIS - datasets/data")
    print("="*70)
    
    # 1. Extracted books stats
    txt_files = glob.glob(os.path.join(BOOKS_DIR, "*.txt"))
    sizes = [os.path.getsize(f) for f in txt_files]
    total_size = sum(sizes)
    
    print(f"\n📚 EXTRACTED BOOKS")
    print(f"   Total files: {len(txt_files):,}")
    print(f"   Total size: {total_size/1e9:.2f} GB")
    print(f"   Avg size: {sum(sizes)/len(sizes)/1024:.1f} KB")
    print(f"   Largest: {max(sizes)/1e6:.1f} MB")
    print(f"   Smallest: {min(sizes)/1024:.1f} KB")
    
    # Size distribution
    large = [s for s in sizes if s > 10e6]  # > 10MB
    medium = [s for s in sizes if 1e6 < s <= 10e6]  # 1-10MB
    small = [s for s in sizes if s <= 1e6]  # < 1MB
    print(f"   > 10MB: {len(large)} books")
    print(f"   1-10MB: {len(medium)} books")
    print(f"   < 1MB: {len(small)} books")
    
    # 2. Metadata analysis
    print(f"\n📋 METADATA")
    with open(os.path.join(METADATA_DIR, "categories.json"), encoding="utf-8") as f:
        cats_data = json.load(f)
        categories = cats_data["categories"]
        print(f"   Categories: {len(categories)}")
    
    with open(os.path.join(METADATA_DIR, "authors.json"), encoding="utf-8") as f:
        authors = json.load(f)
        print(f"   Authors: {len(authors):,}")
    
    # 3. Category distribution from books.db
    import sqlite3
    conn = sqlite3.connect(os.path.join(METADATA_DIR, "books.db"))
    cur = conn.cursor()
    
    cur.execute("""
        SELECT cat_name, COUNT(*) as cnt, SUM(size_mb) as total_mb, 
               AVG(size_mb) as avg_mb, MIN(size_mb) as min_mb, MAX(size_mb) as max_mb
        FROM books 
        GROUP BY cat_name 
        ORDER BY cnt DESC
    """)
    
    print(f"\n📊 CATEGORY DISTRIBUTION (41 categories, 8,425 books)")
    print(f"{'Category':<30} {'Books':>6} {'Total GB':>8} {'Avg MB':>7} {'Min MB':>7} {'Max MB':>7}")
    print("-"*70)
    
    cat_groups = {}
    for row in cur.fetchall():
        cat_name, cnt, total_mb, avg_mb, min_mb, max_mb = row
        total_gb = total_mb / 1024
        
        # Group into super-categories
        if any(k in cat_name for k in ["الفقه", "فقه", "فرائض", "فتاوى", "سياسة", "قضاء"]):
            group = "Fiqh (Jurisprudence)"
        elif any(k in cat_name for k in ["حديث", "السنة", "شروح", "تخريج", "أطراف", "علل", "جوامع"]):
            group = "Hadith (Traditions)"
        elif any(k in cat_name for k in ["عقيدة", "فرق", "ردود"]):
            group = "Aqeedah (Creed)"
        elif any(k in cat_name for k in ["تفسير", "قرآن", "تجويد", "قراءات"]):
            group = "Quran & Tafsir"
        elif any(k in cat_name for k in ["سيرة", "تاريخ", "تراجم", "طبقات", "أنساب", "بلدان", "رحلات"]):
            group = "History & Biography"
        elif any(k in cat_name for k in ["لغة", "غريب", "معاجم", "نحو", "صرف", "أدب", "بلاغة", "عروض", "دواوين", "شعرية"]):
            group = "Arabic Language & Literature"
        elif any(k in cat_name for k in ["رقائق", "آداب", "أذكار"]):
            group = "Spirituality & Ethics"
        elif any(k in cat_name for k in ["عامة", "علوم أخرى", "منطق", "#", "فهارس"]):
            group = "General & Reference"
        else:
            group = "Other"
        
        cat_groups.setdefault(group, {"books": 0, "size_gb": 0})
        cat_groups[group]["books"] += cnt
        cat_groups[group]["size_gb"] += total_gb
        
        print(f"{cat_name:<30} {cnt:>6,} {total_gb:>8.1f} {avg_mb:>7.0f} {min_mb:>7.0f} {max_mb:>7.0f}")
    
    conn.close()
    
    # 4. Super-category summary
    print(f"\n🎯 SUPER-CATEGORY SUMMARY (for agent design)")
    print(f"{'Super-Category':<35} {'Books':>6} {'Size GB':>8}")
    print("-"*50)
    for group in sorted(cat_groups.items(), key=lambda x: -x[1]["books"]):
        name, stats = group
        print(f"{name:<35} {stats['books']:>6,} {stats['size_gb']:>8.1f}")
    
    # 5. Chunking strategy recommendations
    print(f"\n📝 RECOMMENDED CHUNKING STRATEGY")
    print(f"{'Super-Category':<35} {'Chunk Size':>10} {'Est. Chunks':>12}")
    print("-"*60)
    
    chunk_estimates = {
        "Hadith (Traditions)": ("1 hadith each", "~650K"),
        "Fiqh (Jurisprudence)": ("300-500 chars", "~800K"),
        "Quran & Tafsir": ("1 ayah + tafsir", "~50K"),
        "Aqeedah (Creed)": ("300-500 chars", "~100K"),
        "History & Biography": ("400-600 chars", "~500K"),
        "Arabic Language & Literature": ("300-500 chars", "~300K"),
        "Spirituality & Ethics": ("300-500 chars", "~200K"),
        "General & Reference": ("300-500 chars", "~100K"),
        "Other": ("300-500 chars", "~50K"),
    }
    
    for group in sorted(cat_groups.keys()):
        if group in chunk_estimates:
            chunk_size, est = chunk_estimates[group]
            print(f"{group:<35} {chunk_size:>12} {est:>12}")
    
    # 6. Priority ranking
    print(f"\n🚀 EMBEDDING PRIORITY (by ROI)")
    priorities = [
        ("P0 - Critical", "Sanadset Hadith", "650K hadith", "Already chunked, 0.08% done"),
        ("P0 - Critical", "Quran Ayahs", "6,236 ayahs", "Not embedded yet"),
        ("P1 - High", "Hadith Books (كتب السنة)", "1,226 books, 1.7 GB", "Need re-chunking"),
        ("P1 - High", "Tafsir Books", "270 books, 1.7 GB", "High-value content"),
        ("P2 - Medium", "Fiqh Books (all madhhabs)", "1,000+ books, 2.5 GB", "Core Islamic law"),
        ("P2 - Medium", "Aqeedah Books", "794 books, 0.6 GB", "Core theology"),
        ("P3 - Low", "History & Biography", "1,000+ books, 2.4 GB", "Historical context"),
        ("P3 - Low", "Arabic Language", "500+ books, 0.8 GB", "Grammar, lexicon"),
    ]
    
    for priority, name, volume, status in priorities:
        print(f"  {priority}: {name}")
        print(f"    Volume: {volume}")
        print(f"    Status: {status}")
        print()

if __name__ == "__main__":
    analyze_dataset()
