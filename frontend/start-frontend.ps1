$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path .\node_modules)) {
    Write-Host "Installing frontend dependencies..."
    npm ci
}

npm run dev
