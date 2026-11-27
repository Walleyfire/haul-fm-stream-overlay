# Build a NEW EXE from the editable source/ implementation.
# This does not use, unpack or overwrite the legacy v1.2.21 executable.
$ErrorActionPreference = "Stop"
$sourceDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $sourceDir
try {
    py -3 -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw "Installing runtime dependencies failed." }
    py -3 -m pip install "pyinstaller>=6.10,<7"
    if ($LASTEXITCODE -ne 0) { throw "Installing PyInstaller failed." }
    py -3 -m unittest discover -s . -p "test_*.py"
    if ($LASTEXITCODE -ne 0) { throw "Source tests failed." }
    py -3 -m PyInstaller --noconfirm --clean --onefile --windowed --name "HaulFM-Overlay-New" --collect-all webview --collect-all pypresence --add-data "ui.html;." app.py
    if ($LASTEXITCODE -ne 0) { throw "Building the EXE failed." }
    $built = Join-Path $sourceDir "dist\HaulFM-Overlay-New.exe"
    if (!(Test-Path $built)) { throw "Expected output EXE was not created." }
    Write-Host "New overlay built from editable source: $built"
}
finally {
    Pop-Location
}
