[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$venvPath = Join-Path $repositoryRoot '.venv'
$venvPython = Join-Path $venvPath 'Scripts\python.exe'

try {
    $pythonPath = (& py -3.14 -c 'import sys; print(sys.executable)' 2>$null).Trim()
} catch {
    throw 'CPython 3.14 is required. Install it with the Windows Python launcher, then rerun this script.'
}
if (-not $pythonPath) {
    throw 'CPython 3.14 is required. Install it with the Windows Python launcher, then rerun this script.'
}
if (-not (Test-Path -LiteralPath $venvPython -PathType Leaf)) {
    & py -3.14 -m venv $venvPath
}
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r (Join-Path $repositoryRoot 'requirements.txt') -r (Join-Path $repositoryRoot 'requirements-dev.txt')
& $venvPython -m ruff check $repositoryRoot
& $venvPython -m ruff format --check $repositoryRoot
Write-Host "Development environment ready at $venvPath"
