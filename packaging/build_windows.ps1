<#
.SYNOPSIS
    Build the standalone Windows Finecut.exe bundle and optional Inno Setup installer.
.EXAMPLE
    .\packaging\build_windows.ps1
#>

[CmdletBinding()]
param(
    [switch]$SkipInstaller
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$PythonExe = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$PyInstallerExe = Join-Path $RepoRoot ".venv\Scripts\pyinstaller.exe"
$IconPath = Join-Path $RepoRoot "packaging\assets\finecut.ico"
$SpecPath = Join-Path $RepoRoot "packaging\finecut.spec"
$IssPath = Join-Path $RepoRoot "packaging\installer.iss"

if (-not (Test-Path $PythonExe)) {
    throw "Virtual environment not found at $PythonExe. Run: pip install -e `".[dev,build]`""
}
if (-not (Test-Path $PyInstallerExe)) {
    throw "PyInstaller not found at $PyInstallerExe. Run: .venv\Scripts\pip.exe install -e `".[dev,build]`""
}

$Version = (& $PythonExe -c "import finecut; print(finecut.__version__)").Trim()
Write-Host "Building Finecut v$Version..." -ForegroundColor Cyan

if (-not (Test-Path $IconPath)) {
    Write-Host "Generating Finecut icon at $IconPath..."
    & $PythonExe (Join-Path $RepoRoot "packaging\generate_icon.py")
}

Write-Host "Running PyInstaller (--onedir, windowed)..."
& $PyInstallerExe --noconfirm --clean $SpecPath

$BuiltExe = Join-Path $RepoRoot "dist\Finecut\Finecut.exe"
if (-not (Test-Path $BuiltExe)) {
    throw "Expected PyInstaller output not found: $BuiltExe"
}
Write-Host "Built standalone launcher: $BuiltExe" -ForegroundColor Green

if ($SkipInstaller) {
    exit 0
}

$IsccCandidates = @(
    (Get-Command ISCC.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue),
    (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"),
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe"
) | Where-Object { $_ -and (Test-Path $_) }

$IsccExe = $IsccCandidates | Select-Object -First 1
if (-not $IsccExe) {
    Write-Warning "Inno Setup (ISCC.exe) not found locally. Install Inno Setup 6 (e.g. 'winget install JRSoftware.InnoSetup') to compile FinecutSetup-$Version.exe."
    exit 0
}

Write-Host "Compiling Inno Setup installer with $IsccExe..."
& $IsccExe "/DAppVersion=$Version" $IssPath
$InstallerExe = Join-Path $RepoRoot "dist\installer\FinecutSetup-$Version.exe"
Write-Host "Built Windows installer: $InstallerExe" -ForegroundColor Green
