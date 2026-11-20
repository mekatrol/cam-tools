[CmdletBinding(SupportsShouldProcess, ConfirmImpact = 'Medium')]
param([Parameter()][string]$DestinationRoot)

$ErrorActionPreference = 'Stop'
$pluginName = 'MekatrolModelExporter'
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$sourcePath = Join-Path $repositoryRoot "src\$pluginName"
$manifestName = "$pluginName.manifest"
$entryModuleName = "$pluginName.py"

if (-not $DestinationRoot) {
    if (-not $env:APPDATA) { throw 'APPDATA is not defined; pass -DestinationRoot explicitly.' }
    $DestinationRoot = Join-Path $env:APPDATA 'Autodesk\Autodesk Fusion 360\API\Scripts'
}
$resolvedSource = [System.IO.Path]::GetFullPath($sourcePath)
$resolvedRoot = [System.IO.Path]::GetFullPath($DestinationRoot)
$destinationPath = Join-Path $resolvedRoot $pluginName
if ((Split-Path -Leaf $resolvedSource) -ne $pluginName) { throw "Unexpected source path: $resolvedSource" }
if ((Split-Path -Leaf $destinationPath) -ne $pluginName) { throw "Unexpected destination path: $destinationPath" }
if (-not (Test-Path -LiteralPath (Join-Path $resolvedSource $manifestName) -PathType Leaf)) { throw "Source manifest is missing: $manifestName" }
if (-not (Test-Path -LiteralPath (Join-Path $resolvedSource $entryModuleName) -PathType Leaf)) { throw "Source entry module is missing: $entryModuleName" }

if (-not $PSCmdlet.ShouldProcess($destinationPath, "Install $pluginName")) {
    Write-Host "Validated deployment plan for $destinationPath"
    return
}
New-Item -ItemType Directory -Path $resolvedRoot -Force | Out-Null
$stagingPath = Join-Path $resolvedRoot ".$pluginName.stage.$([guid]::NewGuid().ToString('N'))"
try {
    New-Item -ItemType Directory -Path $stagingPath | Out-Null
    Get-ChildItem -LiteralPath $resolvedSource -Force |
        Where-Object { $_.Name -notin @('__pycache__', '.venv', '.vscode') -and $_.Extension -ne '.pyc' } |
        Copy-Item -Destination $stagingPath -Recurse -Force
    foreach ($requiredFile in @($manifestName, $entryModuleName)) {
        if (-not (Test-Path -LiteralPath (Join-Path $stagingPath $requiredFile) -PathType Leaf)) { throw "Staged plugin is missing required file: $requiredFile" }
    }
    if (Test-Path -LiteralPath $destinationPath) {
        Remove-Item -LiteralPath $destinationPath -Recurse -Force
    }
    Move-Item -LiteralPath $stagingPath -Destination $destinationPath
} catch {
    throw
} finally {
    if (Test-Path -LiteralPath $stagingPath) { Remove-Item -LiteralPath $stagingPath -Recurse -Force }
}
Write-Host "Installed to: $destinationPath"
Write-Host 'In Fusion, open Utilities > Scripts and Add-Ins, select MekatrolModelExporter, and click Run.'
