import org.apache.lucene.index.*;
import org.apache.lucene.document.*;
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
            Set<String> fieldNames = new LinkedHashSet<>();
            for (LeafReaderContext ctx : reader.leaves()) {
                LeafReader leafReader = ctx.reader();
                for (FieldInfo fi : leafReader.getFieldInfos()) {
                    fieldNames.add(fi.name);
                }
            }
            System.out.println("Fields: " + fieldNames);
            
            // Extract documents using stored fields
            try (BufferedWriter writer = Files.newBufferedWriter(Paths.get(outputPath))) {
                writer.write("[\n");
                
                int docCount = 0;
                
                for (LeafReaderContext ctx : reader.leaves()) {
                    LeafReader leafReader = ctx.reader();
                    StoredFields storedFields = leafReader.storedFields();
                    int maxDocInLeaf = leafReader.numDocs();
                    
                    for (int i = 0; i < maxDocInLeaf && docCount < maxDoc; i++, docCount++) {
                        try {
                            Document doc = storedFields.document(i);
                            if (docCount > 0) writer.write(",\n");
                            writer.write("{\n");
                            
                            boolean first = true;
                            for (IndexableField field : doc.getFields()) {
                                String name = field.name();
                                String value = doc.get(name);
                                if (value != null) {
                                    if (!first) writer.write(",\n");
                                    // Truncate long values
                                    if (value.length() > 500) {
                                        value = value.substring(0, 500) + "...";
                                    }
                                    // Escape JSON strings
                                    value = value.replace("\\", "\\\\")
                                               .replace("\"", "\\\"")
                                               .replace("\n", "\\n")
                                               .replace("\r", "\\r")
                                               .replace("\t", "\\t");
                                    writer.write("  \"" + name + "\": \"" + value + "\"");
                                    first = false;
                                }
                            }
                            writer.write("\n}");
                            
                            if (docCount % 100 == 0) {
                                System.out.println("  Extracted " + docCount + " docs...");
                            }
                        } catch (Exception e) {
                            // Skip documents that can't be read
                        }
                    }
                    
                    if (docCount >= maxDoc) break;
                }
                
                writer.write("\n]\n");
            }
            
            System.out.println("Extraction complete: " + outputPath);
        }
    }
}
