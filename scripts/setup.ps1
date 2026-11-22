param([switch]$Development)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location -LiteralPath $projectRoot
try {
    if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
        if (Get-Command uv -ErrorAction SilentlyContinue) {
            & uv python install 3.12
            if ($LASTEXITCODE -ne 0) { throw 'Python 3.12 installation failed.' }
            & uv venv --python 3.12 .venv
        } else {
            & py -3.12 -m venv .venv
        }
        if ($LASTEXITCODE -ne 0) { throw 'Install Python 3.12 (64-bit) or uv, then run setup again.' }
    }
    $projectPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        & uv pip install --python $projectPython -r requirements-lock.txt
    } else {
        & $projectPython -m pip install -r requirements-lock.txt
    }
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
    if ($Development) {
        if (Get-Command uv -ErrorAction SilentlyContinue) {
            & uv pip install --python $projectPython -r requirements-dev.txt
        } else {
            & $projectPython -m pip install -r requirements-dev.txt
        }
        if ($LASTEXITCODE -ne 0) { throw 'Development dependency installation failed.' }
    }
    & $projectPython -m scripts.verify_vendor
    if ($LASTEXITCODE -ne 0) { throw 'Bundled renderer dependency verification failed.' }
    Write-Host 'MANEXA is installed. Run: .\scripts\run.ps1'
} finally {
    Pop-Location
}
