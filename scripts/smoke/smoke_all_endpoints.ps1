# PowerShell Test Script for All Burhan API Endpoints

$baseUrl = "http://localhost:8000"
$testResults = @()
$passed = 0
$failed = 0

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Method = "GET",
        [string]$Path,
        [object]$Body = $null,
        [array]$ExpectedFields = @(),
        [int]$ExpectedStatus = 200
    )
    
    Write-Host "`n$('='*60)" -ForegroundColor Cyan
    Write-Host "Test: $Name" -ForegroundColor White
    Write-Host "URL: $Method $Path" -ForegroundColor Gray
    
    try {
        $params = @{
            Uri = "$baseUrl$Path"
            Method = $Method
            TimeoutSec = 30
            UseBasicParsing = $true
        }
        
        if ($Body) {
            $jsonBody = $Body | ConvertTo-Json -Depth 10
            $params.Body = [System.Text.Encoding]::UTF8.GetBytes($jsonBody)
            $params.Headers = @{ "Content-Type" = "application/json" }
            Write-Host "Body: $($jsonBody.Substring(0, [Math]::Min(100, $jsonBody.Length)))..." -ForegroundColor DarkGray
        }
        
        $response = Invoke-RestMethod @params
        $statusCode = 200
        
        Write-Host "Status: $statusCode (Expected: $ExpectedStatus)" -ForegroundColor Green
        
        if ($ExpectedFields.Count -gt 0) {
            $foundFields = @()
            foreach ($field in $ExpectedFields) {
                if ($response.PSObject.Properties.Name -contains $field) {
                    $foundFields += $field
                    $value = $response.$field
                    if ($value -is [System.Collections.IEnumerable] -and $value -isnot [string]) {
                        $value = "[$($value.Count) items]"
                    } elseif ($value -is [string] -and $value.Length -gt 80) {
                        $value = "$($value.Substring(0, 80))..."
                    }
                    Write-Host "  ✓ $field = $value" -ForegroundColor Green
                } else {
                    Write-Host "  ✗ Missing field: $field" -ForegroundColor Red
                }
            }
        }
        
        $script:passed++
        return $response
    }
    catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-Host "Status: $statusCode (Expected: $ExpectedStatus)" -ForegroundColor $(if ($statusCode -eq $ExpectedStatus) { "Green" } else { "Red" })
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
        
        if ($statusCode -eq $ExpectedStatus) {
            $script:passed++
        } else {
            $script:failed++
        }
        return $null
    }
}

Write-Host @"

╔══════════════════════════════════════════════════════════╗
║   🕌 Burhan ISLAMIC QA SYSTEM - COMPREHENSIVE API TEST   ║
╚══════════════════════════════════════════════════════════╝

Testing against: $baseUrl
"@ -ForegroundColor Yellow

# ========================================
# 1. HEALTH & INFO ENDPOINTS
# ========================================
Write-Host "`n$('='*60)" -ForegroundColor Magenta
Write-Host "HEALTH & INFO ENDPOINTS" -ForegroundColor Magenta
Write-Host $('='*60) -ForegroundColor Magenta

Test-Endpoint -Name "Health Check" -Path "/health" -ExpectedFields @("status", "version", "services")
Test-Endpoint -Name "Root Endpoint" -Path "/" -ExpectedFields @("name", "version", "docs")

# ========================================
# 2. QURAN ENDPOINTS
# ========================================
Write-Host "`n$('='*60)" -ForegroundColor Magenta
Write-Host "QURAN ENDPOINTS" -ForegroundColor Magenta
Write-Host $('='*60) -ForegroundColor Magenta

Test-Endpoint -Name "List All Surahs" -Path "/api/v1/quran/surahs" -ExpectedFields @("count")
Test-Endpoint -Name "Get Al-Fatihah" -Path "/api/v1/quran/surahs/1" -ExpectedFields @("number", "name_ar", "name_en", "verse_count")
Test-Endpoint -Name "Get Ayat al-Kursi" -Path "/api/v1/quran/ayah/2:255" -ExpectedFields @("surah_number", "ayah_number", "text_uthmani")
Test-Endpoint -Name "Search Quran" -Path "/api/v1/quran/search" -Method "POST" -Body @{ query = "رحمة"; limit = 5 } -ExpectedFields @("verses", "count")
Test-Endpoint -Name "Validate Quran Quote" -Path "/api/v1/quran/validate" -Method "POST" -Body @{ text = "بسم الله الرحمن الرحيم" } -ExpectedFields @("is_quran", "confidence")
Test-Endpoint -Name "Quran Analytics" -Path "/api/v1/quran/analytics" -Method "POST" -Body @{ query = "كم عدد آيات سورة البقرة؟" } -ExpectedFields @("sql", "result", "formatted_answer")
Test-Endpoint -Name "Get Tafsir" -Path "/api/v1/quran/tafsir/1:1" -ExpectedFields @("ayah", "tafsirs")

# ========================================
# 3. TOOL ENDPOINTS
# ========================================
Write-Host "`n$('='*60)" -ForegroundColor Magenta
Write-Host "TOOL ENDPOINTS" -ForegroundColor Magenta
Write-Host $('='*60) -ForegroundColor Magenta

Test-Endpoint -Name "Zakat Calculator" -Path "/api/v1/tools/zakat" -Method "POST" -Body @{
    assets = @{
        cash = 50000
        gold_grams = 100
        silver_grams = 500
    }
    debts = 5000
    madhhab = "shafii"
} -ExpectedFields @("is_zakatable", "zakat_amount", "nisab")

Test-Endpoint -Name "Prayer Times" -Path "/api/v1/tools/prayer-times" -Method "POST" -Body @{
    lat = 25.2854
    lng = 51.5310
    method = "egyptian"
} -ExpectedFields @("times", "qibla_direction")

Test-Endpoint -Name "Hijri Calendar" -Path "/api/v1/tools/hijri" -Method "POST" -Body @{
    gregorian_date = "2026-04-05"
} -ExpectedFields @("hijri_date", "gregorian_date")

Test-Endpoint -Name "Duas Retrieval" -Path "/api/v1/tools/duas" -Method "POST" -Body @{
    occasion = "morning"
    limit = 3
} -ExpectedFields @("duas", "count")

Test-Endpoint -Name "Inheritance Calculator" -Path "/api/v1/tools/inheritance" -Method "POST" -Body @{
    estate_value = 100000
    heirs = @{
        husband = $true
        father = $true
        mother = $true
        sons = 1
        daughters = 1
    }
} -ExpectedFields @("distribution", "total_distributed", "method")

# ========================================
# 4. QUERY ENDPOINT
# ========================================
Write-Host "`n$('='*60)" -ForegroundColor Magenta
Write-Host "MAIN QUERY ENDPOINT" -ForegroundColor Magenta
Write-Host $('='*60) -ForegroundColor Magenta

Test-Endpoint -Name "Greeting Query" -Path "/api/v1/query" -Method "POST" -Body @{
    query = "السلام عليكم"
    language = "ar"
} -ExpectedFields @("query_id", "intent", "intent_confidence", "answer")

Test-Endpoint -Name "Fiqh Query" -Path "/api/v1/query" -Method "POST" -Body @{
    query = "ما حكم صلاة الجمعة؟"
    language = "ar"
    madhhab = "shafii"
} -ExpectedFields @("query_id", "intent", "intent_confidence", "answer")

Test-Endpoint -Name "Quran Query" -Path "/api/v1/query" -Method "POST" -Body @{
    query = "كم عدد آيات سورة الإخلاص؟"
    language = "ar"
} -ExpectedFields @("query_id", "intent", "intent_confidence", "answer")

Test-Endpoint -Name "Dua Query" -Path "/api/v1/query" -Method "POST" -Body @{
    query = "أعطني دعاء السفر"
    language = "ar"
} -ExpectedFields @("query_id", "intent", "intent_confidence", "answer")

Test-Endpoint -Name "Zakat Query" -Path "/api/v1/query" -Method "POST" -Body @{
    query = "كيف احسب زكاة مالي؟"
    language = "ar"
} -ExpectedFields @("query_id", "intent", "intent_confidence", "answer")

# ========================================
# 5. RAG ENDPOINTS
# ========================================
Write-Host "`n$('='*60)" -ForegroundColor Magenta
Write-Host "RAG ENDPOINTS" -ForegroundColor Magenta
Write-Host $('='*60) -ForegroundColor Magenta

Test-Endpoint -Name "Fiqh RAG" -Path "/api/v1/rag/fiqh" -Method "POST" -Body @{
    query = "ما حكم صلاة الجماعة؟"
    language = "ar"
} -ExpectedFields @("answer", "citations", "confidence")

Test-Endpoint -Name "General RAG" -Path "/api/v1/rag/general" -Method "POST" -Body @{
    query = "من هو عمر بن الخطاب؟"
    language = "ar"
} -ExpectedFields @("answer", "citations", "confidence")

Test-Endpoint -Name "RAG Stats" -Path "/api/v1/rag/stats" -ExpectedFields @("collections", "total_documents", "embedding_model")

# ========================================
# 6. ERROR HANDLING
# ========================================
Write-Host "`n$('='*60)" -ForegroundColor Magenta
Write-Host "ERROR HANDLING" -ForegroundColor Magenta
Write-Host $('='*60) -ForegroundColor Magenta

Test-Endpoint -Name "404 Not Found" -Path "/api/v1/nonexistent" -ExpectedStatus 404
Test-Endpoint -Name "Invalid Query" -Path "/api/v1/query" -Method "POST" -Body @{
    query = ""
    language = "ar"
} -ExpectedStatus 422

# ========================================
# SUMMARY
# ========================================
Write-Host "`n$('='*60)" -ForegroundColor Yellow
Write-Host "TEST SUMMARY" -ForegroundColor Yellow
Write-Host $('='*60) -ForegroundColor Yellow

$total = $passed + $failed
Write-Host @"

Total Tests:  $total
Passed:       $passed  ✓
Failed:       $failed  $(if ($failed -gt 0) { "✗" } else { "" })
Success Rate: $([math]::Round(($passed / $total) * 100, 1))%

"@ -ForegroundColor $(if ($failed -eq 0) { "Green" } else { "Yellow" })

Write-Host "✓ Testing complete!" -ForegroundColor Green
