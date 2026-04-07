#!/usr/bin/env python
"""Deep content analysis of extracted books - focusing on quality and structure."""
import os
import re
import json
from collections import Counter, defaultdict

PATH = r'K:\business\projects_v2\Athar\datasets\data\extracted_books'
METADATA_PATH = r'K:\business\projects_v2\Athar\datasets\data\metadata'

def load_metadata():
    with open(os.path.join(METADATA_PATH, 'books.json'), 'r', encoding='utf-8') as f:
        books_data = json.load(f)
    # Create lookup by file name
    book_by_file = {}
    for b in books_data['books']:
        book_by_file[b['file']] = b
    return books_data, book_by_file

def read_file_content(filename):
    """Read file with multiple encoding attempts."""
    fp = os.path.join(PATH, filename)
    for enc in ['utf-8', 'utf-8-sig', 'windows-1256', 'iso-8859-6']:
        try:
            with open(fp, 'r', encoding=enc) as f:
                return f.read(), enc
        except (UnicodeDecodeError, UnicodeError):
            continue
    with open(fp, 'r', encoding='utf-8', errors='replace') as f:
        return f.read(), 'utf-8-replace'

def analyze_tiny_files(book_by_file):
    """Analyze files under 5KB."""
    print("=== TINY FILES ANALYSIS (< 5KB) ===")
    tiny = []
    for f in os.listdir(PATH):
        if f in ('extraction_state.json', 'file_list.txt'):
            continue
        size = os.path.getsize(os.path.join(PATH, f))
        if size < 5000:
            tiny.append((f, size))
    
    tiny.sort(key=lambda x: x[1])
    print(f"Total tiny files: {len(tiny)}")
    
    for fname, size in tiny[:30]:
        content, enc = read_file_content(fname)
        lines = content.strip().split('\n')
        meta = book_by_file.get(fname, {})
        print(f"\n--- {fname} ({size} bytes, {enc}) ---")
        print(f"  Category: {meta.get('cat_name', '?')}, Type: {meta.get('type', '?')}")
        print(f"  Lines: {len(lines)}")
        print(f"  Content preview: {repr(content[:200])}")

def analyze_content_structure(book_by_file, sample_size=20):
    """Analyze internal structure patterns."""
    print("\n=== CONTENT STRUCTURE ANALYSIS ===")
    
    # Get files across size ranges
    all_files = []
    for f in os.listdir(PATH):
        if f in ('extraction_state.json', 'file_list.txt'):
            continue
        all_files.append((f, os.path.getsize(os.path.join(PATH, f))))
    all_files.sort(key=lambda x: x[1])
    
    # Sample from different size buckets
    n = len(all_files)
    samples = []
    for pct in range(0, 100, 5):
        idx = n * pct // 100
        if idx < n:
            samples.append(all_files[idx])
    
    # Track structural patterns
    patterns = {
        'has_book_id_header': 0,
        'has_page_markers': 0,
        'has_footnote_markers': 0,
        'has_html_spans': 0,
        'has_separator_lines': 0,
        'has_toc_markers': 0,
        'has_volume_markers': 0,
        'has_basmala': 0,
        'has_publisher_info': 0,
        'has_footer_signature': 0,
    }
    
    structural_markers = defaultdict(list)
    
    for fname, fsize in samples[:sample_size]:
        content, enc = read_file_content(fname)
        lines = content.split('\n')
        
        # Check for patterns
        first_5 = '\n'.join(lines[:5])
        if 'Book ID:' in first_5 or 'book_id' in first_5.lower():
            patterns['has_book_id_header'] += 1
        
        # Page markers [Page N]
        page_matches = re.findall(r'\[Page\s+\d+\]', content)
        if page_matches:
            patterns['has_page_markers'] += 1
        
        # Footnotes [Footnotes]:
        if '[Footnotes]:' in content or '⦗' in content:
            patterns['has_footnote_markers'] += 1
        
        # HTML spans
        if '<span' in content:
            patterns['has_html_spans'] += 1
        
        # Separator lines (====, ----, ____)
        if re.search(r'={10,}|-{10,}|_{10,}', content):
            patterns['has_separator_lines'] += 1
        
        # TOC markers
        if 'toc-' in content:
            patterns['has_toc_markers'] += 1
        
        # Volume markers
        if re.search(r'المجلد|الجزء', content[:2000]):
            patterns['has_volume_markers'] += 1
        
        # Basmala
        if 'بسم' in content[:2000] or '﷽' in content[:2000]:
            patterns['has_basmala'] += 1
        
        # Publisher info
        if re.search(r'دار|ناشر|طبعة|نشر', content[:2000]):
            patterns['has_publisher_info'] += 1
        
        # Footer/author signature
        if re.search(r'تم بحمد|تم بفضْل|والحمد لله رب', content[-3000:]):
            patterns['has_footer_signature'] += 1
        
        # Collect unique structural patterns
        for line in lines[:50]:
            ls = line.strip()
            if re.match(r'^={10,}$|^-{10,}$|^_{10,}$', ls):
                structural_markers['separator'].append(f"{fname}: {ls[:30]}")
            if ls.startswith('[Page'):
                structural_markers['page_marker'].append(f"{fname}: {ls}")
                if len(structural_markers['page_marker']) <= 5:
                    break
    
    print(f"Sampled {sample_size} files across size ranges:")
    for pat, count in patterns.items():
        print(f"  {pat}: {count}/{sample_size} ({count*100//sample_size}%)")
    
    print("\n--- Structural marker examples ---")
    for marker_type, examples in structural_markers.items():
        print(f"\n{marker_type}:")
        for ex in examples[:5]:
            print(f"  {ex}")

def analyze_lineage_and_duplicates(book_by_file):
    """Check for potential duplicates and related files."""
    print("\n=== DUPLICATE & LINEAGE ANALYSIS ===")
    
    # Check for books with same title but different IDs
    title_to_ids = defaultdict(list)
    for fname in list(book_by_file.keys())[:5000]:
        meta = book_by_file[fname]
        title = meta.get('title', '').strip()
        if title:
            title_to_ids[title].append((meta['id'], fname))
    
    dup_titles = {t: ids for t, ids in title_to_ids.items() if len(ids) > 1}
    print(f"Exact duplicate titles: {len(dup_titles)}")
    for t, ids in list(dup_titles.items())[:10]:
        print(f"  '{t}': {ids}")
    
    # Check for similar filenames (same base, different edition)
    # Pattern: ID_title_ط_edition.txt vs ID_title.txt
    base_titles = defaultdict(list)
    for fname in os.listdir(PATH):
        if fname in ('extraction_state.json', 'file_list.txt'):
            continue
        m = re.match(r'^(\d+)_(.+)\.txt$', fname)
        if m:
            book_id, title_part = m.groups()
            # Remove edition suffixes
            cleaned = re.sub(r'_ط_.+|_-_ط_.+|_ت_.+$', '', title_part)
            base_titles[cleaned].append((book_id, fname))
    
    similar = {t: files for t, files in base_titles.items() if len(files) > 1}
    print(f"\nSimilar base titles (potential editions/versions): {len(similar)}")
    for t, files in list(similar.items())[:10]:
        print(f"  '{t[:60]}...': {files}")

def analyze_chunking_readiness(book_by_file):
    """Analyze patterns relevant to chunking."""
    print("\n=== CHUNKING READINESS ANALYSIS ===")
    
    all_files = []
    for f in os.listdir(PATH):
        if f in ('extraction_state.json', 'file_list.txt'):
            continue
        all_files.append((f, os.path.getsize(os.path.join(PATH, f))))
    all_files.sort(key=lambda x: x[1])
    
    # Sample medium and large files
    n = len(all_files)
    samples = [all_files[n//4], all_files[n//2], all_files[3*n//4], all_files[-1]]
    
    for fname, fsize in samples:
        content, enc = read_file_content(fname)
        meta = book_by_file.get(fname, {})
        
        lines = content.split('\n')
        words = content.split()
        
        # Count natural break points
        page_breaks = len(re.findall(r'\[Page\s+\d+\]', content))
        chapter_breaks = len(re.findall(r'<span[^>]*data-type="title"[^>]*>', content))
        footnote_sections = content.count('[Footnotes]:')
        separator_lines = len(re.findall(r'^={10,}$|^-{10,}$|^_{10,}$', content, re.MULTILINE))
        
        # Estimate Arabic word count
        arabic_words = len([w for w in words if any('\u0600' <= c <= '\u06FF' for c in w)])
        
        print(f"\n--- {fname} ---")
        print(f"  Category: {meta.get('cat_name', '?')}, Size: {fsize:,} bytes")
        print(f"  Lines: {len(lines)}, Words: {len(words)}, Arabic words: {arabic_words}")
        print(f"  Page markers: {page_breaks}")
        print(f"  Chapter/title spans: {chapter_breaks}")
        print(f"  Footnote sections: {footnote_sections}")
        print(f"  Separator lines: {separator_lines}")
        
        # Calculate average content between page breaks
        if page_breaks > 0:
            avg_lines_per_page = len(lines) // page_breaks
            avg_words_per_page = arabic_words // page_breaks
            print(f"  Avg lines/page: {avg_lines_per_page}")
            print(f"  Avg Arabic words/page: {avg_words_per_page}")
        
        # Show a sample page boundary
        page_match = re.search(r'\[Page\s+(\d+)\]\n(.+?)(?=\[Page\s+\d+\]|$)', content, re.DOTALL)
        if page_match:
            page_num = page_match.group(1)
            page_content = page_match.group(2).strip()
            page_words = page_content.split()
            print(f"\n  Sample page {page_num} ({len(page_words)} words):")
            print(f"    {page_content[:200]}...")

def main():
    books_data, book_by_file = load_metadata()
    
    analyze_tiny_files(book_by_file)
    analyze_content_structure(book_by_file, sample_size=30)
    analyze_lineage_and_duplicates(book_by_file)
    analyze_chunking_readiness(book_by_file)
    
    print("\n\n=== ANALYSIS COMPLETE ===")

if __name__ == '__main__':
    main()
