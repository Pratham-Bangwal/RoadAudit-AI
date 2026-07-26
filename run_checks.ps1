$ErrorActionPreference = "Stop"
$projectPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $projectPath
python -m compileall app.py backend ai utils
python -m unittest discover -s tests -v
python -c "from streamlit.testing.v1 import AppTest; app=AppTest.from_file('app.py', default_timeout=30).run(); assert not app.exception, app.exception; print('Streamlit rendering check passed.')"
Write-Host "All RoadAudit AI checks passed." -ForegroundColor Green
