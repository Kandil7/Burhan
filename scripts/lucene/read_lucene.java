import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.regex.*;

public class read_lucene {
    public static void main(String[] args) throws Exception {
        if (args.length < 1) {
            System.err.println("Usage: java read_lucene <index_path> [max_docs]");
            System.exit(1);
        }
        
        String indexPath = args[0];
        System.out.println("=== DIRECT LUCENE INDEX PARSER ===");
        System.out.println("Index path: " + indexPath);
        
        Path storePath = Paths.get(indexPath);
        
        // Parse .fnm files to get field names
        List<Path> fnmFiles = getFiles(storePath, ".fnm");
        if (!fnmFiles.isEmpty()) {
            Path fnmFile = fnmFiles.get(fnmFiles.size() - 1);
            System.out.println("\n=== FIELD NAMES (from " + fnmFile.getFileName() + ") ===");
            List<String> fieldNames = parseFieldNames(fnmFile);
            System.out.println("Fields: " + fieldNames);
        }
        
        // Parse .fdt files
        List<Path> fdtFiles = getFiles(storePath, ".fdt");
        if (!fdtFiles.isEmpty()) {
            System.out.println("\n=== STORED FIELDS ANALYSIS ===");
            System.out.println("Found " + fdtFiles.size() + " .fdt files");
            
            long totalSize = 0;
            for (Path f : fdtFiles) {
                totalSize += Files.size(f);
            }
            System.out.println("Total .fdt size: " + String.format("%,d", totalSize) + " bytes (" + String.format("%.1f", totalSize/1024.0/1024.0) + " MB)");
            
            if (!fdtFiles.isEmpty()) {
                Path fdtFile = fdtFiles.get(0);
                System.out.println("\nParsing: " + fdtFile.getFileName() + " (" + Files.size(fdtFile) + " bytes)");
                parseFdtFile(fdtFile);
            }
        }
        
        // Parse .doc files
        List<Path> docFiles = getFiles(storePath, ".doc");
        if (!docFiles.isEmpty()) {
            System.out.println("\n=== DOC VALUES ANALYSIS ===");
            System.out.println("Found " + docFiles.size() + " .doc files");
            
            long totalSize = 0;
            for (Path f : docFiles) {
                totalSize += Files.size(f);
            }
            System.out.println("Total .doc size: " + String.format("%,d", totalSize) + " bytes (" + String.format("%.1f", totalSize/1024.0/1024.0) + " MB)");
        }
        
        // Search for Arabic text
        System.out.println("\n=== SEARCHING FOR ARABIC TEXT ===");
        searchForArabicText(storePath);
    }
    
    static List<Path> getFiles(Path dir, String ext) throws Exception {
        List<Path> files = new ArrayList<>();
        try (DirectoryStream<Path> stream = Files.newDirectoryStream(dir, "*" + ext)) {
            for (Path entry : stream) {
                files.add(entry);
            }
        }
        Collections.sort(files);
        return files;
    }
    
    static List<String> parseFieldNames(Path fnmFile) throws Exception {
        List<String> fieldNames = new ArrayList<>();
        byte[] data = Files.readAllBytes(fnmFile);
        String text = new String(data, "UTF-8");
        
        // Find field names
        Pattern pattern = Pattern.compile("\u0000([a-zA-Z_][a-zA-Z0-9_]{2,})\u0000");
        Matcher matcher = pattern.matcher(text);
        while (matcher.find()) {
            String name = matcher.group(1);
            if (!name.startsWith("PerField") && !name.startsWith("Lucene")) {
                fieldNames.add(name);
            }
        }
        return fieldNames;
    }
    
    static void parseFdtFile(Path fdtFile) throws Exception {
        byte[] data = Files.readAllBytes(fdtFile);
        int limit = Math.min(5000, data.length);
        
        // Print hex dump
        System.out.println("\nHex dump (first 256 bytes):");
        for (int i = 0; i < Math.min(256, limit); i += 16) {
            System.out.printf("  %04x: ", i);
            for (int j = i; j < Math.min(i + 16, limit); j++) {
                System.out.printf("%02x ", data[j] & 0xFF);
            }
            System.out.print("  ");
            for (int j = i; j < Math.min(i + 16, limit); j++) {
                char c = (char)(data[j] & 0xFF);
                System.out.print((c >= 32 && c < 127) ? c : '.');
            }
            System.out.println();
        }
        
        // Try Windows-1256 decoding
        System.out.println("\nTrying Windows-1256 decoding...");
        String decoded = new String(data, 0, Math.min(5000, data.length), "windows-1256");
        Pattern arabicPattern = Pattern.compile("[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF\\s]{20,}");
        Matcher matcher = arabicPattern.matcher(decoded);
        int count = 0;
        while (matcher.find() && count < 10) {
            String text = matcher.group();
            if (text.trim().length() > 10) {
                System.out.println("  [" + count + "] " + text.substring(0, Math.min(150, text.length())));
                count++;
            }
        }
        if (count == 0) {
            System.out.println("  No Arabic text found in first 5KB");
        }
    }
    
    static void searchForArabicText(Path storePath) throws Exception {
        List<Path> fdtFiles = getFiles(storePath, ".fdt");
        int totalArabicFound = 0;
        
        for (Path fdtFile : fdtFiles) {
            if (totalArabicFound >= 20) break;
            
            byte[] data = Files.readAllBytes(fdtFile);
            String decoded = new String(data, "windows-1256");
            
            Pattern arabicPattern = Pattern.compile("[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF\\s]{30,}");
            Matcher matcher = arabicPattern.matcher(decoded);
            
            while (matcher.find() && totalArabicFound < 20) {
                String text = matcher.group();
                if (text.trim().length() > 20) {
                    System.out.println("  [" + fdtFile.getFileName() + "] " + text.substring(0, Math.min(200, text.length())));
                    totalArabicFound++;
                }
            }
        }
        
        if (totalArabicFound == 0) {
            System.out.println("  No Arabic text found in .fdt files");
            System.out.println("\nTrying .doc files...");
            
            List<Path> docFiles = getFiles(storePath, ".doc");
            for (Path docFile : docFiles) {
                if (Files.size(docFile) > 100000000) continue;
                
                byte[] data = Files.readAllBytes(docFile);
                int limit = Math.min(100000, data.length);
                String decoded = new String(data, 0, limit, "windows-1256");
                
                Pattern arabicPattern = Pattern.compile("[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF\\s]{30,}");
                Matcher matcher = arabicPattern.matcher(decoded);
                
                int found = 0;
                while (matcher.find() && found < 5) {
                    String text = matcher.group();
                    if (text.trim().length() > 20) {
                        System.out.println("  [" + docFile.getFileName() + "] " + text.substring(0, Math.min(200, text.length())));
                        found++;
                        totalArabicFound++;
                    }
                }
                
                if (found > 0) break;
            }
        }
    }
}
