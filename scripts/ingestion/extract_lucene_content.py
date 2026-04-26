"""
Try to read Lucene index using Java Lucene library or direct parsing.
"""
import subprocess
import os
from pathlib import Path

BASE_DIR = Path(r"K:\business\projects_v2\Burhan\datasets\system_book_datasets")

def try_java_lucene_reader():
    """Try to use Java to read Lucene index."""
    print("=== ATTEMPTING JAVA LUCENE READER ===")
    
    # Check if Java is available
    result = subprocess.run(["java", "-version"], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"Java is available: {result.stderr.split(chr(10))[0]}")
        
        # Create a simple Java program to read Lucene index
        java_code = '''
import org.apache.lucene.index.DirectoryReader;
import org.apache.lucene.store.FSDirectory;
import java.nio.file.Paths;

public class LuceneReader {
    public static void main(String[] args) throws Exception {
        String indexPath = args[0];
        try (var dir = FSDirectory.open(Paths.get(indexPath));
             var reader = DirectoryReader.open(dir)) {
            
            System.out.println("Num docs: " + reader.numDocs());
            System.out.println("Max doc: " + reader.maxDoc());
            
            // Get field names
            var fields = reader.getFieldInfos();
            System.out.println("Fields:");
            for (var fi : fields) {
                System.out.println("  - " + fi.name + " (stored=" + fi.getDocValuesType() + ")");
            }
            
            // Read first 5 documents
            System.out.println("\\nSample documents:");
            for (int i = 0; i < Math.min(5, reader.maxDoc()); i++) {
                var doc = reader.document(i);
                System.out.println("Doc " + i + ":");
                for (var field : doc.getFields()) {
                    String name = field.name();
                    String value = doc.get(name);
                    if (value != null && value.length() > 200) {
                        value = value.substring(0, 200) + "...";
                    }
                    System.out.println("  " + name + " = " + value);
                }
            }
        }
    }
}
'''
        
        # Check if lucene jars are available
        lucene_jars = []
        for root, dirs, files in os.walk(r"K:\business\projects_v2\Burhan"):
            for f in files:
                if f.endswith(".jar") and "lucene" in f.lower():
                    lucene_jars.append(os.path.join(root, f))
        
        if lucene_jars:
            print(f"\nFound {len(lucene_jars)} Lucene JAR files")
            for jar in lucene_jars[:5]:
                print(f"  {jar}")
        else:
            print("\nNo Lucene JAR files found in project")
    else:
        print("Java not available")


def try_lucli():
    """Try to use lucli (Lucene command line interface)."""
    print("\n=== ATTEMPTING LUCENE CLI ===")
    
    # Check for lucli
    result = subprocess.run(["lucli"], capture_output=True, text=True)
    if result.returncode == 0:
        print("lucli is available")
    else:
        print("lucli not available")


def analyze_lucene_cfs_file():
    """Try to parse Lucene compound file (.cfs) which might be easier."""
    print("\n=== ANALYZING LUCENE COMPOUND FILE (.cfs) ===")
    
    page_store = BASE_DIR / "store" / "page"
    cfs_files = list(page_store.glob("*.cfs"))
    
    if cfs_files:
        cfs_file = cfs_files[-1]
        print(f"Analyzing: {cfs_file.name} ({cfs_file.stat().st_size:,} bytes)")
        
        with open(cfs_file, "rb") as f:
            data = f.read(min(1000, cfs_file.stat().st_size))
            print(f"First 200 bytes hex: {data[:200].hex()}")
            
            # Look for readable strings
            import re
            text = data.decode("utf-8", errors="ignore")
            strings = re.findall(r'[\x20-\x7E]{3,}', text)
            print(f"Readable strings: {strings[:20]}")


def try_lucene_index_tool():
    """Try to use Luke or other Lucene index tools."""
    print("\n=== CHECKING FOR LUCENE TOOLS ===")
    
    # Check for luke
    result = subprocess.run(["luke"], capture_output=True, text=True)
    if result.returncode == 0:
        print("Luke is available")
    else:
        print("Luke not available")
    
    # Check for elastic search tools
    result = subprocess.run(["curl", "--version"], capture_output=True, text=True)
    if result.returncode == 0:
        print("curl is available - could use Elasticsearch's Lucene tools")


def parse_stored_fields_directly():
    """Try to parse Lucene stored fields format directly."""
    print("\n=== DIRECT STORED FIELDS PARSING ===")
    
    page_store = BASE_DIR / "store" / "page"
    
    # Find .fnm file to get field names
    fnm_files = list(page_store.glob("*.fnm"))
    if not fnm_files:
        print("No .fnm files found")
        return
    
    # Parse the latest .fnm file
    fnm_file = fnm_files[-1]
    print(f"Parsing field names from: {fnm_file.name}")
    
    with open(fnm_file, "rb") as f:
        data = f.read()
        
        # Skip header (Lucene94FieldInfos)
        # Format: magic + codec name + version + fields
        import re
        
        # Find all readable strings which are field names
        text = data.decode("utf-8", errors="ignore")
        field_names = []
        for match in re.finditer(r'\x00([\x20-\x7E]{2,})\x00', text):
            name = match.group(1)
            if not name.startswith("PerField") and not name.startswith("Lucene"):
                field_names.append(name)
        
        print(f"Field names found: {field_names}")
    
    # Now try to parse .fdt file
    fdt_files = sorted(page_store.glob("*.fdt"))
    if not fdt_files:
        print("No .fdt files found")
        return
    
    # Use a small .fdt file
    fdt_file = None
    for f in fdt_files:
        if f.stat().st_size < 10000000:
            fdt_file = f
            break
    
    if fdt_file is None:
        fdt_file = fdt_files[0]
    
    print(f"\nParsing stored fields from: {fdt_file.name} ({fdt_file.stat().st_size:,} bytes)")
    
    with open(fdt_file, "rb") as f:
        data = f.read()
        
        # Look for Arabic text patterns in the entire file
        # Try Windows-1256 decoding
        print("\nSearching for Arabic text in .fdt file...")
        
        # Try to decode the entire file as Windows-1256
        try:
            decoded = data.decode("windows-1256", errors="ignore")
            # Find Arabic text sequences
            arabic_matches = re.findall(r'[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF\s]{20,}', decoded)
            if arabic_matches:
                print(f"Found {len(arabic_matches)} Arabic text sequences")
                for i, match in enumerate(arabic_matches[:10]):
                    print(f"  [{i}] {match[:150]}")
            else:
                print("No Arabic text found with Windows-1256 decoding")
        except Exception as e:
            print(f"Error decoding: {e}")
        
        # Try UTF-8 decoding
        try:
            decoded = data.decode("utf-8", errors="ignore")
            arabic_matches = re.findall(r'[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF\s]{20,}', decoded)
            if arabic_matches:
                print(f"\nFound {len(arabic_matches)} Arabic text sequences (UTF-8)")
                for i, match in enumerate(arabic_matches[:5]):
                    print(f"  [{i}] {match[:150]}")
        except Exception as e:
            print(f"Error decoding UTF-8: {e}")


def main():
    print("="*80)
    print("LUCENE INDEX CONTENT EXTRACTION ATTEMPTS")
    print("="*80)
    
    try_java_lucene_reader()
    try_lucli()
    analyze_lucene_cfs_file()
    try_lucene_index_tool()
    parse_stored_fields_directly()


if __name__ == "__main__":
    main()
