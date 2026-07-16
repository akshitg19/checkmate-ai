$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$python = Get-Command py -ErrorAction SilentlyContinue
if ($python) {
    & py -3.11 -m venv venv
} else {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $python) {
        throw "Python 3.11 is required and was not found."
    }
    & python -m venv venv
}

$version = & .\venv\Scripts\python.exe -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ($version -ne "3.11") {
    throw "Python 3.11 is required, but the virtual environment uses Python $version."
}

& .\venv\Scripts\python.exe -m pip install --upgrade pip
& .\venv\Scripts\python.exe -m pip install -r requirements.txt

Write-Host "Backend ready. Run .\start-backend.ps1"
