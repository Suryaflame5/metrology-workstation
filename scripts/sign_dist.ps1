param()
$cert = Get-Item Cert:\CurrentUser\My\53925307A1C275D7FBAD156C19CB1A8B756712E2
$files = @(
    "dist\MetrologyWorkstation.exe",
    "dist\Metrology-Workstation-Demo-v7.0.0-Setup.exe",
    "dist\Metrology-Workstation-Pro-v7.0.0-Setup.exe"
)
foreach ($f in $files) {
    if (Test-Path $f) {
        Write-Host "Signing $f ..."
        Set-AuthenticodeSignature -FilePath $f -Certificate $cert -HashAlgorithm SHA256
    }
}
