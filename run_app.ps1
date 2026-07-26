$ErrorActionPreference = "Stop"
$projectPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $projectPath
$apiProcess = Start-Process -FilePath python -ArgumentList "-m", "uvicorn", "backend.api:app", "--host", "127.0.0.1", "--port", "8000" -WindowStyle Hidden -PassThru
try {
    $env:ROAD_AUDIT_API_URL = "http://127.0.0.1:8000"
    python -m streamlit run app.py
}
finally {
    if (-not $apiProcess.HasExited) { Stop-Process -Id $apiProcess.Id }
}
