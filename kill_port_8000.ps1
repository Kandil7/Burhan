$ErrorActionPreference = "SilentlyContinue"
$connections = Get-NetTCPConnection -LocalPort 8000 -State Listen
if ($connections) {
    foreach ($conn in $connections) {
        Write-Host "Killing PID: $($conn.OwningProcess)"
        Stop-Process -Id $conn.OwningProcess -Force
    }
} else {
    Write-Host "No process found on port 8000"
}
