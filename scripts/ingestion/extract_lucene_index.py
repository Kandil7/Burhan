"""
Extract content from Shamela Lucene indexes.
Downloads Lucene JARs and uses Java to read the index.
"""
import os
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Any

# Configuration
LUCENE_VERSION = "9.12.0"
BASE_DIR = Path(r"K:\business\projects_v2\Athar")
DATASETS_DIR = BASE_DIR / "datasets" / "system_book_datasets"
STORE_DIR = DATASETS_DIR / "store"
LUCENE_JARS_DIR = BASE_DIR / "lib" / "lucene"

def download_lucene_jars():
    """Download required Lucene JAR files."""
    print("=== DOWNLOADING LUCENE JARS ===")
    
    LUCENE_JARS_DIR.mkdir(parents=True, exist_ok=True)
    
    required_jars = [
        f"lucene-core-{LUCENE_VERSION}.jar",
        f"lucene-queryparser-{LUCENE_VERSION}.jar",
    ]
    
    base_url = f"https://repo1.maven.org/maven2/org/apache/lucene"
    
    for jar in required_jars:
        jar_path = LUCENE_JARS_DIR / jar
        if jar_path.exists():
            print(f"  Already exists: {jar}")
            continue
        
        # Determine the module name
        module = jar.replace(f"-{LUCENE_VERSION}.jar", "")
        url = f"{base_url}/{module}/{LUCENE_VERSION}/{jar}"
        
        print(f"  Downloading: {jar}")
        result = subprocess.run(
            ["curl", "-L", "-o", str(jar_path), url],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0 and jar_path.exists() and jar_path.stat().st_size > 1000:
            print(f"    Success: {jar_path.stat().st_size:,} bytes")
        else:
            print(f"    Failed: {result.stderr}")
            return False
    
    return True


def create_java_extractor():
    """Create Java program to extract Lucene index content."""
    java_code = '''
import org.apache.lucene.index.*;
import org.apache.lucene.store.*;
import java.nio.file.*;
import java.io.*;
import java.util.*;

public class LuceneExtractor {
    public static void main(String[] args) throws Exception {
        String indexPath = args[0];
        String outputPath = args[1];
        int maxDocs = args.length > 2 ? Integer.parseInt(args[2]) : -1;
        
        try (Directory dir = FSDirectory.open(Paths.get(indexPath));
             DirectoryReader reader = DirectoryReader.open(dir)) {
            
            int numDocs = reader.numDocs();
            int maxDoc = maxDocs > 0 ? Math.min(maxDocs, numDocs) : numDocs;
            
            System.out.println("Index: " + indexPath);
            System.out.println("Total docs: " + numDocs);
            System.out.println("Extracting: " + maxDoc + " docs");
            
            // Get field names
            List<String> fieldNames = new ArrayList<>();
            for (LeafReaderContext ctx : reader.leaves()) {
                for (FieldInfo fi : ctx.reader().getFieldInfos()) {
                    if (!fieldNames.contains(fi.name)) {
                        fieldNames.add(fi.name);
                    }
                }
            }
            System.out.println("Fields: " + fieldNames);
            
            // Extract documents
            try (BufferedWriter writer = Files.newBufferedWriter(Paths.get(outputPath))) {
                writer.write("[\\n");
                
                for (int i = 0; i < maxDoc; i++) {
                    try {
                        Document doc = reader.document(i);
                        if (i > 0) writer.write(",\\n");
                        writer.write("{\\n");
                        
                        boolean first = true;
                        for (IndexableField field : doc.getFields()) {
                            String name = field.name();
                            String value = doc.get(name);
                            if (value != null) {
                                if (!first) writer.write(",\\n");
                                // Escape JSON strings
                                value = value.replace("\\\\", "\\\\\\\\").replace("\\"", "\\\\\\"")
                                           .replace("\\n", "\\\\n").replace("\\r", "\\\\r")
                                           .replace("\\t", "\\\\t");
                                writer.write("  \\"" + name + "\\": \\"" + value + "\\"");
                                first = false;
                            }
                        }
                        writer.write("\\n}");
                        
                        if (i % 1000 == 0) {
                            System.out.println("  Extracted " + i + " docs...");
                        }
                    } catch (Exception e) {
                        // Skip documents that can't be read
                    }
                }
                
                writer.write("\\n]\\n");
            }
            
            System.out.println("Extraction complete: " + outputPath);
        }
    }
}
'''
    
    java_file = BASE_DIR / "scripts" / "LuceneExtractor.java"
    with open(java_file, "w", encoding="utf-8") as f:
        f.write(java_code)
    
    print(f"Created Java extractor: {java_file}")
    return java_file


def compile_java_extractor(java_file):
    """Compile the Java extractor."""
    print("\n=== COMPILING JAVA EXTRACTOR ===")
    
    # Get classpath
    jar_files = list(LUCENE_JARS_DIR.glob("*.jar"))
    classpath = ";".join(str(j) for j in jar_files)
    
    cmd = [
        "javac",
        "-cp", classpath,
        "-encoding", "UTF-8",
        str(java_file)
    ]
    
    print(f"Compiling: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("  Compilation successful")
        return True
    else:
        print(f"  Compilation failed: {result.stderr}")
        return False


def extract_index(index_name, max_docs=100):
    """Extract content from a specific Lucene index."""
    print(f"\n=== EXTRACTING INDEX: {index_name} ===")
    
    index_path = STORE_DIR / index_name
    if not index_path.exists():
        print(f"  Index not found: {index_path}")
        return None
    
    output_file = BASE_DIR / "output" / f"lucene_{index_name}.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Get classpath
    jar_files = list(LUCENE_JARS_DIR.glob("*.jar"))
    classpath = ";".join(str(j) for j in jar_files)
    
    cmd = [
        "java",
        "-cp", f".;{classpath}",
        "-Xmx2g",
        "LuceneExtractor",
        str(index_path),
        str(output_file),
        str(max_docs)
    ]
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(BASE_DIR / "scripts"))
    
    print(result.stdout)
    if result.stderr:
        print(f"Stderr: {result.stderr}")
    
    if output_file.exists():
        size = output_file.stat().st_size
        print(f"Output: {output_file} ({size:,} bytes)")
        return output_file
    
    return None


def main():
    print("="*80)
    print("SHAMELA LUCENE INDEX EXTRACTOR")
    print("="*80)
    
    # Step 1: Download Lucene JARs
    if not download_lucene_jars():
        print("\nFailed to download Lucene JARs. Please download manually:")
        print(f"  https://repo1.maven.org/maven2/org/apache/lucene/lucene-core/{LUCENE_VERSION}/")
        return
    
    # Step 2: Create Java extractor
    java_file = create_java_extractor()
    
    # Step 3: Compile
    if not compile_java_extractor(java_file):
        print("\nFailed to compile Java extractor")
        return
    
    # Step 4: Extract from small indexes first
    # Start with 'title' index (56 MB)
    extract_index("title", max_docs=100)
    
    # Then try 'author' index (1.9 MB)
    extract_index("author", max_docs=100)
    
    print("\n=== EXTRACTION COMPLETE ===")
    print("Check output files in:", BASE_DIR / "output")


if __name__ == "__main__":
    main()
