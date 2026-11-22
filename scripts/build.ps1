# Build from fresh staging sources so setuptools cannot reuse retired renderer files in build/.
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$projectPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $projectPython)) { throw 'Run setup.ps1 first.' }
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) { throw 'Install uv to build the wheel.' }
$stagingRoot = Join-Path $projectRoot ('artifacts\build-source-' + [guid]::NewGuid().ToString('N'))
$wheelDirectory = Join-Path $projectRoot 'artifacts\wheel'
New-Item -ItemType Directory -Path $stagingRoot -Force | Out-Null
New-Item -ItemType Directory -Path $wheelDirectory -Force | Out-Null
foreach ($sourceName in @('app', 'pyproject.toml', 'README.md', 'LICENSE', 'THIRD_PARTY_NOTICES.md')) {
    Copy-Item -LiteralPath (Join-Path $projectRoot $sourceName) -Destination $stagingRoot -Recurse
}
Push-Location -LiteralPath $projectRoot
try {
    & uv build --wheel $stagingRoot --out-dir $wheelDirectory --quiet
    if ($LASTEXITCODE -ne 0) { throw 'Wheel build failed.' }
    $appVersion = & $projectPython -c 'from app import __version__; print(__version__)'
    if ($LASTEXITCODE -ne 0 -or $appVersion -notmatch '^\d+\.\d+\.\d+$') { throw 'Could not read application version.' }
    $wheelPath = Join-Path $wheelDirectory ('manexa_ai-' + $appVersion + '-py3-none-any.whl')
    & $projectPython -m scripts.verify_package $wheelPath
    if ($LASTEXITCODE -ne 0) { throw 'Packaged renderer asset check failed.' }
    Write-Host ('Built: ' + $wheelPath)
} finally {
    Pop-Location
}
