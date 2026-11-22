param([switch]$Windowed, [switch]$Fullscreen, [switch]$SoftwareRendering)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$projectPython = Join-Path $projectRoot '.venv\Scripts\pythonw.exe'
if ($Windowed -and $Fullscreen) { throw 'Choose either -Windowed or -Fullscreen.' }
if (-not (Test-Path -LiteralPath $projectPython)) {
    throw 'Run .\scripts\setup.ps1 first.'
}
$launchArgs = @('-m', 'app.main')
if ($Windowed) { $launchArgs += '--windowed' }
if ($Fullscreen) { $launchArgs += '--fullscreen' }
if ($SoftwareRendering) { $launchArgs += '--software-rendering' }
# pythonw avoids a terminal window when launched from Explorer/shortcuts.
Start-Process -FilePath $projectPython -ArgumentList $launchArgs -WorkingDirectory $projectRoot -WindowStyle Hidden
