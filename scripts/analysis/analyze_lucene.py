"""
Analyze Lucene index structure to understand what fields are stored.
Lucene 9.x indexes store data in .cfs (compound file) or separate files.
"""
import os
import struct
from pathlib import Path

BASE_DIR = Path(r"K:\business\projects_v2\Athar\datasets\system_book_datasets")

def analyze_lucene_page_index():
    """Analyze the main page Lucene index which has the actual content."""
    print("="*80)
    print("LUCENE PAGE INDEX DEEP ANALYSIS")
    print("="*80)
    
    page_store = BASE_DIR / "store" / "page"
    
    # List all files by type
    file_types = {}
    for f in page_store.iterdir():
        if f.is_file():
            ext = f.suffix if f.suffix else "(no ext)"
            if ext not in file_types:
                file_types[ext] = []
            file_types[ext].append(f)
    
    print("\nFile types in page store:")
    for ext, files in sorted(file_types.items()):
        total_size = sum(f.stat().st_size for f in files)
        print(f"  {ext:10s}: {len(files):4d} files, {total_size:>12,} bytes ({total_size/1024/1024:.1f} MB)")
    
    # The .fdt files contain the actual stored field data
    # Let's try to parse the Lucene stored fields format
    print("\n=== ANALYZING .fdt FILES (STORED FIELDS) ===")
    
    fdt_files = sorted(page_store.glob("*.fdt"))
    print(f"\nFound {len(fdt_files)} .fdt files")
    
    # Check .fdx files (field index)
    fdx_files = sorted(page_store.glob("*.fdx"))
    print(f"Found {len(fdx_files)} .fdx files")
    
    # Check .fnm files (field names)
    fnm_files = sorted(page_store.glob("*.fnm"))
    print(f"Found {len(fnm_files)} .fnm files")
    
    # Try to parse .fnm file to get field names
    if fnm_files:
        print(f"\n=== PARSING .fnm FILE (FIELD NAMES) ===")
        fnm_file = fnm_files[-1]  # Use the latest one
        print(f"File: {fnm_file.name} ({fnm_file.stat().st_size:,} bytes)")
        
        with open(fnm_file, "rb") as f:
            data = f.read()
            print(f"First 200 bytes hex: {data[:200].hex()}")
            
            # Try to find field names in the file
            # Lucene stores field names as strings
            try:
                # Look for readable strings
                text_content = data.decode("utf-8", errors="ignore")
                print(f"\nReadable text in .fnm file:")
                # Find strings longer than 3 chars
                import re
                strings = re.findall(r'[\x20-\x7E]{3,}', text_content)
                for s in strings[:30]:
                    print(f"  Found string: {s}")
            except Exception as e:
                print(f"Error parsing .fnm: {e}")
    
    # Try to parse .fdt file for actual content
    if fdt_files:
        print(f"\n=== ANALYZING .fdt FILE CONTENT ===")
        # Use a medium-sized file
        fdt_file = None
        for f in fdt_files:
            if 100000 < f.stat().st_size < 5000000:
                fdt_file = f
                break
        
        if fdt_file is None:
            fdt_file = fdt_files[0]
        
        print(f"File: {fdt_file.name} ({fdt_file.stat().st_size:,} bytes)")
        
        with open(fdt_file, "rb") as f:
            data = f.read(min(10000, fdt_file.stat().st_size))
            
            # Print hex dump
            print(f"\nHex dump (first 500 bytes):")
            for i in range(0, min(500, len(data)), 16):
                hex_part = data[i:i+16].hex()
                ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
                print(f"  {i:04x}: {hex_part:48s} {ascii_part}")
            
            # Try to find Arabic text patterns
            # Arabic Unicode range: 0600-06FF
            print(f"\nSearching for Arabic text patterns...")
            for i in range(len(data) - 2):
                # Check for Windows-1256 Arabic bytes (0xC0-0xFF range often contains Arabic)
                if 0xC0 <= data[i] <= 0xFF and 0xC0 <= data[i+1] <= 0xFF:
                    # Try to decode as Windows-1256
                    try:
                        chunk = data[i:i+50]
                        decoded = chunk.decode("windows-1256")
                        if any('\u0600' <= c <= '\u06FF' for c in decoded):
                            print(f"  Offset {i:04x}: {decoded[:80]}")
                            break
                    except:
                        pass


def analyze_other_lucene_indexes():
    """Analyze other Lucene indexes (author, title, esnad, etc.)."""
    print("\n" + "="*80)
    print("OTHER LUCENE INDEXES ANALYSIS")
    print("="*80)
    
    store_dir = BASE_DIR / "store"
    
    for idx_name in ["author", "title", "esnad", "aya", "book", "s_author", "s_book"]:
        idx_dir = store_dir / idx_name
        if not idx_dir.exists():
            continue
        
        print(f"\n--- Index: {idx_name} ---")
        
        # Get .fnm file for field names
        fnm_files = list(idx_dir.glob("*.fnm"))
        if fnm_files:
            fnm_file = fnm_files[-1]
            with open(fnm_file, "rb") as f:
                data = f.read()
                # Try to find field names
                try:
                    text = data.decode("utf-8", errors="ignore")
                    import re
                    strings = re.findall(r'[\x20-\x7E]{3,}', text)
                    print(f"  Field names found: {strings}")
                except:
                    print(f"  Could not parse .fnm file")
        
        # Check .fdt files for content
        fdt_files = list(idx_dir.glob("*.fdt"))
        if fdt_files:
            total_size = sum(f.stat().st_size for f in fdt_files)
            print(f"  .fdt files: {len(fdt_files)}, total size: {total_size:,} bytes ({total_size/1024/1024:.1f} MB)")
            
            # Sample content
            if fdt_files:
                with open(fdt_files[0], "rb") as f:
                    data = f.read(min(2000, fdt_files[0].stat().st_size))
                    # Try Windows-1256
                    try:
                        decoded = data.decode("windows-1256", errors="ignore")
                        # Find Arabic text
                        import re
                        arabic_matches = re.findall(r'[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF\s]{10,}', decoded)
                        if arabic_matches:
                            print(f"  Found Arabic text samples:")
                            for match in arabic_matches[:5]:
                                print(f"    {match[:100]}")
                    except:
                        pass


def try_pyspark_lucene_reader():
    """Try to read Lucene index using available tools."""
    print("\n" + "="*80)
    print("ATTEMPTING TO READ LUCENE INDEX")
    print("="*80)
    
    # Check if lucene packages are available
    try:
        import lucene
        print("PyLucene is available!")
    except ImportError:
        print("PyLucene not available")
    
    try:
        # from pylucene import *
        print("PyLucene imports successful")
    except:
        pass
    
    # Check what Python packages are available
    import subprocess
    result = subprocess.run(["pip", "list"], capture_output=True, text=True)
    if "lucene" in result.stdout.lower():
        print("\nLucene packages found in pip:")
        for line in result.stdout.split("\n"):
            if "lucene" in line.lower():
                print(f"  {line}")
    else:
        print("\nNo Lucene Python packages found")


def main():
    analyze_lucene_page_index()
    analyze_other_lucene_indexes()
    try_pyspark_lucene_reader()


if __name__ == "__main__":
    main()
