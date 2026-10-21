@echo off
setlocal enabledelayedexpansion

:: ============================================
:: Burhan - FULL LUCENE EXTRACTION
:: ============================================
:: Extracts ALL Lucene indexes from Shamela system_book_datasets
:: 
:: Requirements:
::   - Java 11+ installed
::   - Lucene JARs in lib/lucene/
::   - ~15 GB free disk space
::
:: Time estimates:
::   - Esnad (35K docs):      ~5 minutes
::   - Author (3K docs):      ~5 minutes
::   - Book (8.4K docs):      ~10 minutes
::   - Title (3.9M docs):     ~30-60 minutes
::   - Page (7.3M docs):      ~2-4 hours
::
:: Total: ~3-5 hours for ALL indexes
:: ============================================

:: Configuration
set BASE_DIR=%~dp0..
set SCRIPTS_DIR=%BASE_DIR%\scripts
set STORE_DIR=%BASE_DIR%\datasets\system_book_datasets\store
set OUTPUT_DIR=%BASE_DIR%\data\processed
set LUCENE_CORE=%BASE_DIR%\lib\lucene\lucene-core-9.12.0.jar
set LUCENE_CODECS=%BASE_DIR%\lib\lucene\lucene-backward-codecs-9.12.0.jar
set CLASSPATH=.;%LUCENE_CORE%;%LUCENE_CODECS%
set JAVA_OPTS=-Xmx2g

:: Create output directory
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

echo ======================================================================
echo  Burhan - FULL LUCENE INDEX EXTRACTION
echo ======================================================================
echo.
echo  Starting: %DATE% %TIME%
echo  Base directory: %BASE_DIR%
echo  Output directory: %OUTPUT_DIR%
echo.

:: Check Java
where java >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Java not found! Please install Java 11+
    pause
    exit /b 1
)

:: Check Lucene JARs
if not exist "%LUCENE_CORE%" (
    echo ERROR: Lucene core JAR not found: %LUCENE_CORE%
    pause
    exit /b 1
)

if not exist "%LUCENE_CODECS%" (
    echo ERROR: Lucene backward codecs JAR not found: %LUCENE_CODECS%
    pause
    exit /b 1
)

echo Checking Java version:
java -version
echo.

:: ============================================
:: STEP 1: Compile Java Extractor
:: ============================================
echo ======================================================================
echo  STEP 1: Compiling Java Extractor
echo ======================================================================
cd /d "%SCRIPTS_DIR%"

if exist LuceneExtractor.class (
    echo LuceneExtractor.class already exists, skipping compilation
) else (
    echo Compiling LuceneExtractor.java...
    javac -cp "%CLASSPATH%" -encoding UTF-8 LuceneExtractor.java
    
    if %ERRORLEVEL% NEQ 0 (
        echo ERROR: Compilation failed!
        pause
        exit /b 1
    )
    echo Compilation successful!
)
echo.

:: ============================================
:: STEP 2: Extract Indexes
:: ============================================

:: Function to extract an index
:: Usage: call :extract_index INDEX_NAME MAX_DOCS STEP_NUMBER
:extract_index
set INDEX_NAME=%1
set MAX_DOCS=%2
set STEP_NUM=%3
set INDEX_PATH=%STORE_DIR%\%INDEX_NAME%
set OUTPUT_FILE=%OUTPUT_DIR%\lucene_%INDEX_NAME%.json

if not exist "%INDEX_PATH%" (
    echo WARNING: Index not found: %INDEX_PATH%
    echo.
    exit /b 1
)

echo ======================================================================
echo  STEP 2.%STEP_NUM%: Extracting %INDEX_NAME% index (%MAX_DOCS% docs)
echo ======================================================================
echo  Index path: %INDEX_PATH%
echo  Output file: %OUTPUT_FILE%
echo  Max docs: %MAX_DOCS%
echo  Started: %TIME%
echo.

cd /d "%SCRIPTS_DIR%"
java %JAVA_OPTS% -cp "%CLASSPATH%" LuceneExtractor "%INDEX_PATH%" "%OUTPUT_FILE%" %MAX_DOCS%

if %ERRORLEVEL% EQU 0 (
    echo  SUCCESS: Extraction complete
    if exist "%OUTPUT_FILE%" (
        for %%A in ("%OUTPUT_FILE%") do set SIZE=%%~zA
        echo  File size: !SIZE! bytes
    )
) else (
    echo  ERROR: Extraction failed
)
echo  Finished: %TIME%
echo.
exit /b 0

:: Extract Esnad (Hadith Chains)
call :extract_index esnad -1 1

:: Extract Author Biographies
call :extract_index author -1 2

:: Extract Book Index
call :extract_index book -1 3

:: Extract Title Index (Chapters/Sections)
call :extract_index title -1 4

:: Extract Page Index (Full Arabic Text - LARGEST)
call :extract_index page -1 5

:: Extract Aya (Quran Verses)
call :extract_index aya -1 6

:: Extract Search Author Index
call :extract_index s_author -1 7

:: Extract Search Book Index
call :extract_index s_book -1 8

:: ============================================
:: SUMMARY
:: ============================================
echo ======================================================================
echo  EXTRACTION COMPLETE
echo ======================================================================
echo.
echo  Finished: %DATE% %TIME%
echo.
echo  Output files:
dir /b "%OUTPUT_DIR%\lucene_*.json"
echo.
echo  Total size:
for /f "tokens=3" %%A in ('dir "%OUTPUT_DIR%\lucene_*.json" ^| findstr /i "File(s)"') do echo    %%A bytes
echo.
echo  Next steps:
echo    1. Merge with master catalog
echo    2. Build hierarchical chunks
echo    3. Upload to Hugging Face
echo    4. Embed on Colab GPU
echo.

pause
