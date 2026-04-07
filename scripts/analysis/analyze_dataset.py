#!/usr/bin/env python
"""Comprehensive analysis of extracted_books dataset."""
import os
import re
import json
import hashlib
from collections import Counter, defaultdict

PATH = r'K:\business\projects_v2\Athar\datasets\data\extracted_books'
METADATA_PATH = r'K:\business\projects_v2\Athar\datasets\data\metadata'

def get_all_files():
    files = os.listdir(PATH)
    # Exclude non-book files
    book_files = [f for f in files if f not in ('extraction_state.json', 'file_list.txt')]
    return sorted(book_files)

def analyze_sizes(files):
    sizes = []
    for f in files:
        fp = os.path.join(PATH, f)
        sizes.append((f, os.path.getsize(fp)))
    sizes.sort(key=lambda x: x[1])
    
    size_values = [s[1] for s in sizes]
    print("=== FILE SIZE DISTRIBUTION ===")
    print(f"Total files: {len(sizes)}")
    print(f"Smallest: {sizes[0][0]} -> {sizes[0][1]:,} bytes")
    print(f"Largest: {sizes[-1][0]} -> {sizes[-1][1]:,} bytes")
    n = len(sizes)
    print(f"Median: {sizes[n//2][1]:,} bytes")
    print(f"Average: {sum(size_values)//n:,} bytes")
    print(f"Q1: {sizes[n//4][1]:,} bytes")
    print(f"Q3: {sizes[3*n//4][1]:,} bytes")
    
    print("\n=== SIZE BUCKETS ===")
    buckets = {'<1KB':0, '1-10KB':0, '10-50KB':0, '50-100KB':0, '100-500KB':0, '500KB-1MB':0, '1MB+':0}
    for s in size_values:
        if s < 1024: buckets['<1KB'] += 1
        elif s < 10240: buckets['1-10KB'] += 1
        elif s < 51200: buckets['10-50KB'] += 1
        elif s < 102400: buckets['50-100KB'] += 1
        elif s < 512000: buckets['100-500KB'] += 1
        elif s < 1048576: buckets['500KB-1MB'] += 1
        else: buckets['1MB+'] += 1
    for k, v in buckets.items():
        print(f"  {k}: {v:,}")
    
    return sizes

def analyze_naming(files):
    print("\n=== NAMING PATTERNS ===")
    numeric_prefix = sum(1 for f in files if re.match(r'^\d+_', f))
    print(f"Files with numeric prefix: {numeric_prefix}/{len(files)}")
    
    # Extract numeric IDs
    ids = []
    for f in files:
        m = re.match(r'^(\d+)_', f)
        if m:
            ids.append(int(m.group(1)))
    
    if ids:
        print(f"ID range: {min(ids)} to {max(ids)}")
        print(f"Unique IDs: {len(set(ids))}")
        print(f"Missing IDs (gaps): {max(ids) - min(ids) + 1 - len(set(ids))}")
    
    # Analyze underscore patterns
    underscore_counts = Counter(f.count('_') for f in files)
    print("\nUnderscore count distribution:")
    for k, v in sorted(underscore_counts.items()):
        print(f"  {k} underscores: {v:,} files")
    
    return ids

def check_encoding_and_content(files, sizes, sample_count=50):
    print("\n=== ENCODING & CONTENT ANALYSIS ===")
    
    # Sample files across size ranges
    n = len(sizes)
    sample_indices = set()
    # Pick from different size buckets
    for pct in [0, 5, 10, 25, 50, 75, 90, 95, 99]:
        idx = n * pct // 100
        for offset in range(-2, 3):
            if 0 <= idx + offset < n:
                sample_indices.add(idx + offset)
    
    # Also add some random samples
    import random
    random.seed(42)
    for _ in range(20):
        sample_indices.add(random.randint(0, n-1))
    
    sample_indices = sorted(sample_indices)[:sample_count]
    samples = [sizes[i] for i in sample_indices]
    
    encoding_issues = []
    content_stats = []
    
    for fname, fsize in samples:
        fp = os.path.join(PATH, fname)
        
        # Try different encodings
        content = None
        encoding_used = None
        for enc in ['utf-8', 'utf-8-sig', 'windows-1256', 'iso-8859-6']:
            try:
                with open(fp, 'r', encoding=enc) as f:
                    content = f.read()
                encoding_used = enc
                break
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        if content is None:
            encoding_issues.append(fname)
            continue
        
        # Analyze content
        lines = content.split('\n')
        words = content.split()
        
        # Check for chapter/section markers
        chapter_markers = []
        for line in lines[:100]:  # Check first 100 lines
            line_stripped = line.strip()
            if any(marker in line_stripped for marker in ['فصل', 'باب', 'كتاب', 'جزء', 'مقدمة', 'خاتمة', 'الفصل', 'الباب']):
                chapter_markers.append(line_stripped[:80])
        
        # Check for page separators
        page_sep_chars = Counter(content)
        has_page_breaks = '---' in content or '===' in content or '___' in content
        
        # Check for metadata
        has_title = bool(re.search(r'العنوان|العنوان:|Title:', content[:500]))
        has_author = bool(re.search(r'المؤلف|المؤلف:|Author:', content[:500]))
        
        # Arabic character ratio
        arabic_chars = sum(1 for c in content if '\u0600' <= c <= '\u06FF')
        arabic_ratio = arabic_chars / len(content) if content else 0
        
        content_stats.append({
            'file': fname,
            'size': fsize,
            'encoding': encoding_used,
            'lines': len(lines),
            'words': len(words),
            'chars': len(content),
            'arabic_ratio': round(arabic_ratio, 3),
            'has_chapter_markers': len(chapter_markers) > 0,
            'chapter_markers': chapter_markers[:3],
            'has_page_breaks': has_page_breaks,
            'has_title_meta': has_title,
            'has_author_meta': has_author,
        })
    
    print(f"\nEncoding issues: {len(encoding_issues)} files")
    if encoding_issues:
        print(f"  Files with encoding issues: {encoding_issues[:10]}")
    
    encodings = Counter(s['encoding'] for s in content_stats)
    print(f"\nEncoding distribution (sample):")
    for enc, cnt in encodings.most_common():
        print(f"  {enc}: {cnt}")
    
    print(f"\nContent statistics (sample of {len(content_stats)} files):")
    print(f"  Avg lines: {sum(s['lines'] for s in content_stats)//len(content_stats):,}")
    print(f"  Avg words: {sum(s['words'] for s in content_stats)//len(content_stats):,}")
    print(f"  Avg arabic ratio: {sum(s['arabic_ratio'] for s in content_stats)/len(content_stats):.3f}")
    print(f"  Files with chapter markers: {sum(1 for s in content_stats if s['has_chapter_markers'])}")
    print(f"  Files with page breaks: {sum(1 for s in content_stats if s['has_page_breaks'])}")
    print(f"  Files with title metadata: {sum(1 for s in content_stats if s['has_title_meta'])}")
    print(f"  Files with author metadata: {sum(1 for s in content_stats if s['has_author_meta'])}")
    
    return content_stats

def check_quality_issues(files, sizes):
    print("\n=== QUALITY ISSUES ===")
    
    # Very small files (< 100 bytes)
    tiny_files = [(f, s) for f, s in sizes if s < 100]
    print(f"\nVery small files (<100 bytes): {len(tiny_files)}")
    for f, s in tiny_files[:10]:
        fp = os.path.join(PATH, f)
        with open(fp, 'r', encoding='utf-8', errors='ignore') as fh:
            content = fh.read()
        print(f"  {f} ({s} bytes): {repr(content[:100])}")
    
    # Check for duplicates via hash
    print("\nChecking for duplicate files (by content hash)...")
    hash_map = defaultdict(list)
    sample_for_hash = sizes[:2000]  # Sample for speed
    for fname, fsize in sample_for_hash:
        fp = os.path.join(PATH, fname)
        with open(fp, 'rb') as f:
            h = hashlib.md5(f.read()).hexdigest()
        hash_map[h].append(fname)
    
    duplicates = {h: flist for h, flist in hash_map.items() if len(flist) > 1}
    print(f"Duplicate groups (in sample of {len(sample_for_hash)}): {len(duplicates)}")
    for h, flist in list(duplicates.items())[:10]:
        print(f"  Hash {h}: {flist[:5]}")
    
    # Near-duplicate detection (same ID, different name)
    id_map = defaultdict(list)
    for f, _ in sizes:
        m = re.match(r'^(\d+)_', f)
        if m:
            id_map[m.group(1)].append(f)
    
    dup_ids = {k: v for k, v in id_map.items() if len(v) > 1}
    print(f"\nFiles sharing same ID: {len(dup_ids)}")
    for k, v in list(dup_ids.items())[:10]:
        print(f"  ID {k}: {v}")

def categorize_files(files):
    print("\n=== CATEGORIZATION ANALYSIS ===")
    
    # Category keywords in Arabic
    category_keywords = {
        'fiqh': ['فقه', 'فروع', 'أحكام', 'حلال', 'حرام', 'صلاة', 'زكاة', 'صيام', 'حج'],
        'hadith': ['حديث', 'أحاديث', 'سنن', 'صحيح', 'مسند', 'رواية', 'مسن'],
        'aqeedah': ['عقيدة', 'توحيد', 'إيمان', 'أصول الدين', 'إثبات', 'صفات الله'],
        'tafsir': ['تفسير', 'علوم القرآن', 'القراءات', 'المصحف'],
        'seerah': ['سيرة', 'نبوية', 'غزوات', 'صحاب', 'رسول'],
        'arabic_language': ['نحو', 'صرف', 'لغة', 'بلاغة', 'معجم', 'قاموس'],
        'history': ['تاريخ', 'حرب', 'دولة', 'خلافة', 'حضارة'],
        'islamic_culture': ['ثقافة', 'أخلاق', 'آداب', 'تربية', 'دعوة'],
        'comparative_religion': ['مقارنة', 'أديان', 'مسيحية', 'يهودية', 'استشراق'],
        'general': ['عام', 'متنوع'],
    }
    
    # Score each file against categories
    file_categories = {}
    for fname in files[:2000]:  # Sample for speed
        scores = {}
        title_part = fname.split('_', 1)[-1].replace('_', ' ').replace('.txt', '')
        
        for cat, keywords in category_keywords.items():
            score = sum(1 for kw in keywords if kw in title_part)
            if score > 0:
                scores[cat] = score
        
        if scores:
            best_cat = max(scores, key=scores.get)
            file_categories[fname] = (best_cat, scores[best_cat])
    
    cat_counts = Counter(c[0] for c in file_categories.values())
    print("\nCategory distribution (from filename analysis, sample of 2000):")
    for cat, cnt in cat_counts.most_common():
        print(f"  {cat}: {cnt}")
    
    uncat = sum(1 for f in files[:2000] if f not in file_categories)
    print(f"  Uncategorized: {uncat}")
    
    return file_categories

def sample_content_details(sizes, count=40):
    print("\n=== DETAILED CONTENT SAMPLES ===")
    
    # Select diverse samples
    n = len(sizes)
    indices = set()
    for i in range(count):
        indices.add(n * i // count)
    indices = sorted(indices)
    
    samples = [sizes[i] for i in indices]
    
    for fname, fsize in samples:
        fp = os.path.join(PATH, fname)
        try:
            with open(fp, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except:
            try:
                with open(fp, 'r', encoding='windows-1256', errors='replace') as f:
                    content = f.read()
            except:
                print(f"\n{'='*80}")
                print(f"FILE: {fname} ({fsize:,} bytes) - COULD NOT READ")
                continue
        
        lines = content.split('\n')
        non_empty = [l for l in lines if l.strip()]
        
        print(f"\n{'='*80}")
        print(f"FILE: {fname} ({fsize:,} bytes)")
        print(f"Lines: {len(lines)}, Non-empty: {len(non_empty)}, Words: {len(content.split())}")
        print(f"\n--- FIRST 15 LINES ---")
        for line in lines[:15]:
            print(f"  | {line[:120]}")
        print(f"\n--- LINES 15-25 ---")
        for line in lines[15:25]:
            print(f"  | {line[:120]}")
        print(f"\n--- LAST 10 LINES ---")
        for line in lines[-10:]:
            print(f"  | {line[:120]}")
        
        # Check for structural markers
        markers_found = []
        for i, line in enumerate(lines):
            ls = line.strip()
            if ls and (ls.startswith('===') or ls.startswith('---') or ls.startswith('___')):
                markers_found.append(f"Line {i}: {ls[:50]}")
        if markers_found:
            print(f"\n--- STRUCTURAL MARKERS ---")
            for m in markers_found[:5]:
                print(f"  {m}")

def check_metadata_directory():
    print("\n=== METADATA DIRECTORY ANALYSIS ===")
    if os.path.exists(METADATA_PATH):
        items = os.listdir(METADATA_PATH)
        print(f"Items in metadata: {items}")
        for item in items:
            fp = os.path.join(METADATA_PATH, item)
            if os.path.isfile(fp):
                with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                print(f"\n--- {item} (first 1000 chars) ---")
                print(content[:1000])
    else:
        print(f"Metadata directory not found: {METADATA_PATH}")
    
    # Also check for extraction_state.json
    state_file = os.path.join(PATH, 'extraction_state.json')
    if os.path.exists(state_file):
        with open(state_file, 'r', encoding='utf-8') as f:
            state = json.load(f)
        print(f"\n--- extraction_state.json ---")
        print(json.dumps(state, ensure_ascii=False, indent=2)[:2000])
    
    # Check file_list.txt
    flist_file = os.path.join(PATH, 'file_list.txt')
    if os.path.exists(flist_file):
        with open(flist_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        print(f"\n--- file_list.txt ({len(lines)} lines, first 30) ---")
        for line in lines[:30]:
            print(f"  {line.strip()}")

def main():
    files = get_all_files()
    print(f"Total book files: {len(files)}")
    
    sizes = analyze_sizes(files)
    analyze_naming(files)
    check_metadata_directory()
    content_stats = check_encoding_and_content(files, sizes, sample_count=50)
    check_quality_issues(files, sizes)
    categorize_files(files)
    sample_content_details(sizes, count=40)
    
    # Save detailed samples for further analysis
    print("\n\n=== ANALYSIS COMPLETE ===")

if __name__ == '__main__':
    main()
