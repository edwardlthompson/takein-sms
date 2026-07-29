# Build TakeIn SMS for Windows (PyInstaller + bundled platform-tools)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

Write-Host "==> Installing Python deps"
python -m pip install -r requirements.txt

$VendorAdb = Join-Path $Root "vendor\platform-tools\adb.exe"
if (-not (Test-Path $VendorAdb)) {
    Write-Host "==> Downloading Android platform-tools"
    $zip = Join-Path $env:TEMP "platform-tools-latest-windows.zip"
    $url = "https://dl.google.com/android/repository/platform-tools-latest-windows.zip"
    Invoke-WebRequest -Uri $url -OutFile $zip
    $dest = Join-Path $Root "vendor"
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    Expand-Archive -Path $zip -DestinationPath $dest -Force
    if (-not (Test-Path $VendorAdb)) {
        throw "platform-tools extract failed; adb.exe missing at $VendorAdb"
    }
    Write-Host "    Bundled adb at $VendorAdb"
} else {
    Write-Host "==> Using existing vendor\platform-tools"
}

Write-Host "==> Building TakeInSMS.exe (one-folder)"
python -m PyInstaller --noconfirm TakeInSMS.spec

$out = Join-Path $Root "dist\TakeInSMS\TakeInSMS.exe"
if (Test-Path $out) {
    Write-Host "==> Done: $out"
} else {
    throw "Build finished but exe not found: $out"
}
