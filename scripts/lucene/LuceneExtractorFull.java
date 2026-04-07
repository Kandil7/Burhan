import org.apache.lucene.index.*;
import org.apache.lucene.document.*;
import org.apache.lucene.store.*;
import java.nio.file.*;
import java.io.*;
import java.util.*;

/**
 * Enhanced LuceneExtractor for full-text extraction.
 *
 * Supports:
 *   - No truncation (full field values)
 *   - Offset-based extraction for batching
 *   - JSONL output format (one JSON object per line)
 *   - Progress reporting every N docs
 *
 * Usage:
 *   java LuceneExtractorFull <index_path> <output_path> [max_docs] [offset] [progress_interval]
 *
 * Examples:
 *   java LuceneExtractorFull /path/to/page/ output.jsonl -1 0 10000
 *   java LuceneExtractorFull /path/to/page/ output_batch1.jsonl 500000 0 10000
 *   java LuceneExtractorFull /path/to/page/ output_batch2.jsonl 500000 500000 10000
 */
public class LuceneExtractorFull {
    public static void main(String[] args) throws Exception {
        if (args.length < 2) {
            System.err.println("Usage: LuceneExtractorFull <index_path> <output_path> [max_docs] [offset] [progress_interval]");
            System.exit(1);
        }

        String indexPath = args[0];
        String outputPath = args[1];
        int maxDocs = args.length > 2 ? Integer.parseInt(args[2]) : -1;
        int offset = args.length > 3 ? Integer.parseInt(args[3]) : 0;
        int progressInterval = args.length > 4 ? Integer.parseInt(args[4]) : 10000;

        try (Directory dir = FSDirectory.open(Paths.get(indexPath));
             DirectoryReader reader = DirectoryReader.open(dir)) {

            int numDocs = reader.numDocs();
            int limit = maxDocs > 0 ? Math.min(maxDocs, numDocs - offset) : numDocs - offset;

            System.out.println("Index: " + indexPath);
            System.out.println("Total docs in index: " + numDocs);
            System.out.println("Offset: " + offset);
            System.out.println("Limit: " + limit);
            System.out.println("Extracting docs " + offset + " to " + (offset + limit - 1));

            // Get field names
            Set<String> fieldNames = new LinkedHashSet<>();
            for (LeafReaderContext ctx : reader.leaves()) {
                LeafReader leafReader = ctx.reader();
                for (FieldInfo fi : leafReader.getFieldInfos()) {
                    fieldNames.add(fi.name);
                }
            }
            System.out.println("Fields: " + fieldNames);

            // Extract documents - JSONL format (one JSON per line, no array)
            try (BufferedWriter writer = Files.newBufferedWriter(
                    Paths.get(outputPath),
                    StandardOpenOption.CREATE,
                    StandardOpenOption.WRITE)) {

                int globalDocIndex = 0;  // Global index across all leaves
                int extractedCount = 0;
                int skippedCount = 0;

                for (LeafReaderContext ctx : reader.leaves()) {
                    LeafReader leafReader = ctx.reader();
                    StoredFields storedFields = leafReader.storedFields();
                    int maxDocInLeaf = leafReader.maxDoc();  // includes deleted docs

                    for (int i = 0; i < maxDocInLeaf; i++) {
                        // Check if we should start extracting
                        if (globalDocIndex < offset) {
                            globalDocIndex++;
                            continue;
                        }

                        // Check if we've extracted enough
                        if (extractedCount >= limit) {
                            break;
                        }

                        try {
                            Document doc = storedFields.document(i);
                            if (doc == null) {
                                globalDocIndex++;
                                skippedCount++;
                                continue;
                            }

                            // Build JSON object
                            StringBuilder sb = new StringBuilder();
                            sb.append("{");
                            boolean first = true;

                            for (IndexableField indexableField : doc.getFields()) {
                                String name = indexableField.name();
                                String value = doc.get(name);
                                if (value != null) {
                                    if (!first) sb.append(",");
                                    // Escape JSON strings properly
                                    String escaped = escapeJson(value);
                                    sb.append("\"").append(name).append("\":\"").append(escaped).append("\"");
                                    first = false;
                                }
                            }
                            sb.append("}");

                            writer.write(sb.toString());
                            writer.newLine();
                            extractedCount++;

                            if (extractedCount % progressInterval == 0) {
                                System.out.println("  Extracted " + extractedCount + "/" + limit + " docs... (global index: " + globalDocIndex + ")");
                                writer.flush();
                            }
                        } catch (Exception e) {
                            skippedCount++;
                            // Skip documents that can't be read
                        }

                        globalDocIndex++;
                    }

                    if (extractedCount >= limit) break;
                }

                System.out.println("Extraction complete: " + outputPath);
                System.out.println("Extracted: " + extractedCount + " docs");
                System.out.println("Skipped: " + skippedCount + " docs");
            }
        }
    }

    /**
     * Properly escape a string for JSON output.
     */
    private static String escapeJson(String value) {
        if (value == null) return "";

        StringBuilder sb = new StringBuilder(value.length() + 16);
        for (int i = 0; i < value.length(); i++) {
            char c = value.charAt(i);
            switch (c) {
                case '\\': sb.append("\\\\"); break;
                case '"':  sb.append("\\\""); break;
                case '\n': sb.append("\\n"); break;
                case '\r': sb.append("\\r"); break;
                case '\t': sb.append("\\t"); break;
                case '\b': sb.append("\\b"); break;
                case '\f': sb.append("\\f"); break;
                default:
                    if (c < 0x20) {
                        // Control characters: escape as \XXXX
                        sb.append(String.format("\\u%04x", (int) c));
                    } else {
                        sb.append(c);
                    }
                    break;
            }
        }
        return sb.toString();
    }
}
