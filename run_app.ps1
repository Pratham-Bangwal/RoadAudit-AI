$ErrorActionPreference = "Stop"
$projectPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $projectPath
$apiProcess = $null
$startedApi = $false

try {
    try {
        $null = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 2
        Write-Host "RoadAudit API is already running." -ForegroundColor Green
    }
    catch {
        Write-Host "Starting RoadAudit API..." -ForegroundColor Cyan
        $apiProcess = Start-Process -FilePath python -ArgumentList "-m", "uvicorn", "backend.api:app", "--host", "127.0.0.1", "--port", "8000" -WindowStyle Hidden -PassThru
        $startedApi = $true
        $apiReady = $false
        for ($attempt = 0; $attempt -lt 30; $attempt++) {
            Start-Sleep -Milliseconds 250
            try {
                $null = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 1
                $apiReady = $true
                break
            }
            catch { }
        }
        if (-not $apiReady) { throw "FastAPI did not become ready on port 8000." }
        Write-Host "RoadAudit API is ready." -ForegroundColor Green
    }
    $env:ROAD_AUDIT_API_URL = "http://127.0.0.1:8000"
    Write-Host "Opening RoadAudit dashboard at http://localhost:8501" -ForegroundColor Cyan
    python -m streamlit run app.py
}
finally {
    if ($startedApi -and $apiProcess -and -not $apiProcess.HasExited) {
        Stop-Process -Id $apiProcess.Id
    }
}
