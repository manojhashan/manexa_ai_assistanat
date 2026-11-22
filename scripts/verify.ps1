param([switch]$SoftwareRendering)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$projectPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
$projectRuff = Join-Path $projectRoot '.venv\Scripts\ruff.exe'
$previousChromiumFlags = $env:QTWEBENGINE_CHROMIUM_FLAGS
$previousRhi = $env:QSG_RHI_BACKEND
$previousSoftware = $env:QSG_RHI_PREFER_SOFTWARE_RENDERER
if ($SoftwareRendering) {
    $env:QTWEBENGINE_CHROMIUM_FLAGS = '--ignore-gpu-blocklist'
    $env:QSG_RHI_BACKEND = 'd3d11'
    $env:QSG_RHI_PREFER_SOFTWARE_RENDERER = '1'
}
Push-Location -LiteralPath $projectRoot
try {
    if (-not (Test-Path -LiteralPath $projectPython)) { throw 'Run setup.ps1 -Development first.' }
    & $projectPython -m scripts.verify_vendor
    if ($LASTEXITCODE -ne 0) { throw 'Vendor integrity check failed.' }
    & $projectRuff check app tests scripts
    if ($LASTEXITCODE -ne 0) { throw 'Lint failed.' }
    & $projectRuff format --check app tests scripts
    if ($LASTEXITCODE -ne 0) { throw 'Formatting check failed.' }
    # A new workspace directory avoids inaccessible shared-temp leftovers. Never reuse a
    # user-supplied --basetemp path: pytest may remove its existing contents.
    $testTemp = Join-Path $projectRoot ('artifacts\pytest-' + [guid]::NewGuid().ToString('N'))
    & $projectPython -m pytest -q --basetemp $testTemp --tb=short
    if ($LASTEXITCODE -ne 0) { throw 'Unit/desktop checks failed.' }
    $smokeArgs = @('-m', 'app.main', '--smoke-test', '--fullscreen', '--smoke-report', 'artifacts\smoke.json', '--screenshot', 'artifacts\phase1-launch.png')
    if ($SoftwareRendering) { $smokeArgs += '--software-rendering' }
    & $projectPython @smokeArgs
    if ($LASTEXITCODE -ne 0) { throw 'Desktop/WebGL launch check failed.' }
    & $projectPython -m scripts.check_renderer --fullscreen
    if ($LASTEXITCODE -ne 0) { throw 'Renderer animation checks failed.' }
    Write-Host 'All checks passed. Reports and screenshots are in artifacts\.'
} finally {
    $env:QTWEBENGINE_CHROMIUM_FLAGS = $previousChromiumFlags
    $env:QSG_RHI_BACKEND = $previousRhi
    $env:QSG_RHI_PREFER_SOFTWARE_RENDERER = $previousSoftware
    Pop-Location
}
