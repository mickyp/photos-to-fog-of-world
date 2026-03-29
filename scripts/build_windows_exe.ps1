param(
    [string]$Python = "py",
    [string]$DistDir = "dist"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$exiftool = & $Python -c "from scripts.build_fog_gpx import find_exiftool; print(find_exiftool())" 2>$null
if (-not $exiftool) {
    throw "ExifTool was not found. Install it first or place exiftool.exe next to the scripts."
}

& $Python -m pip install --upgrade pyinstaller

if (Test-Path (Join-Path $repoRoot "build")) {
    Remove-Item -Recurse -Force (Join-Path $repoRoot "build")
}

if (Test-Path (Join-Path $repoRoot $DistDir)) {
    Remove-Item -Recurse -Force (Join-Path $repoRoot $DistDir)
}

$commonArgs = @(
    "-m", "PyInstaller",
    "--noconfirm",
    "--clean",
    "--distpath", $DistDir,
    "--workpath", "build\pyinstaller",
    "--specpath", "build\spec",
    "--add-binary", "$exiftool;."
)

Push-Location $repoRoot
try {
    & $Python @commonArgs --name "photos-to-gpx-cli" scripts\fog_gpx_cli.py
    & $Python @commonArgs --windowed --name "photos-to-gpx-gui" scripts\fog_gpx_gui.py
}
finally {
    Pop-Location
}

Write-Host "Built executables in $repoRoot\$DistDir"
