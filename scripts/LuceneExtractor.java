import org.apache.lucene.index.*;
import org.apache.lucene.store.*;
import java.nio.file.*;
import java.io.*;

public class LuceneExtractor {
    public static void main(String[] args) throws Exception {
        String indexPath = args[0];
        String outputPath = args[1];
        int maxDocs = args.length > 2 ? Integer.parseInt(args[2]) : -1;

        try (Directory dir = FSDirectory.open(Paths.get(indexPath));
             DirectoryReader reader = DirectoryReader.open(dir)) {

            int numDocs = reader.numDocs();
            int maxDoc = maxDocs > 0 ? Math.min(maxDocs, numDocs) : numDocs;

            System.err.println("Index: " + indexPath);
            System.err.println("Total docs: " + numDocs);
            System.err.println("Extracting: " + maxDoc + " docs");

            int extracted = 0;
            
            try (BufferedWriter writer = Files.newBufferedWriter(Paths.get(outputPath))) {
                writer.write("[\n");

                for (int docID = 0; docID < reader.maxDoc() && extracted < maxDoc; docID++) {
                    try {
                        // Use the Document class from Lucene
                        org.apache.lucene.document.Document doc = reader.storedFields().document(docID);
                        
                        if (extracted > 0) writer.write(",\n");
                        writer.write("{\n");

                        boolean first = true;
                        for (IndexableField field : doc.getFields()) {
                            String name = field.name();
                            String value = doc.get(name);
                            if (value != null && !value.isEmpty()) {
                                if (!first) writer.write(",\n");
                                value = escapeJson(value);
                                writer.write("  \"" + name + "\": \"" + value + "\"");
                                first = false;
                            }
                        }
                        writer.write("\n}");
                        extracted++;

                        if (extracted % 1000 == 0) {
                            System.err.println("  Extracted " + extracted + " docs...");
                        }
                    } catch (Exception e) {
                        // Skip unreadable documents
                    }
                }

                writer.write("\n]\n");
            }

            System.err.println("Extraction complete: " + outputPath);
            System.err.println("Total extracted: " + extracted);
        }
    }
    
    private static String escapeJson(String s) {
        return s.replace("\\", "\\\\")
                .replace("\"", "\\\"")
                .replace("\n", "\\n")
                .replace("\r", "\\r")
                .replace("\t", "\\t");
    }
}
