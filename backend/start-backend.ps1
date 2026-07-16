$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path .\venv\Scripts\python.exe)) {
    throw "Backend environment is missing. Run .\setup-backend.ps1 first."
}

& .\venv\Scripts\python.exe -m uvicorn main:app --reload
