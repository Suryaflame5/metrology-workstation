<#
.SYNOPSIS
    Automated Release & Integrity Verification for CALIBRA Metrology Workstation.

.DESCRIPTION
    Validates release artifacts (Demo and Professional installers), checking:
    - Existence & file size
    - PE header & x64 architecture
    - SHA-256 integrity checksums
    - Authenticode digital signature status (honest reporting)
#>

[CmdletBinding()]
param(
    [string]$DistDir = ""
)

if (-not $DistDir) {
    $DistDir = Join-Path $PSScriptRoot "..\dist"
}

$ErrorActionPreference = "Continue"

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host " CALIBRA Metrology Workstation - Release Verification Suite" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan

$distPath = [System.IO.Path]::GetFullPath($DistDir)
Write-Host "Dist Directory: $distPath`n" -ForegroundColor DarkGray

$artifacts = @(
    "MetrologyWorkstation.exe",
    "Metrology-Workstation-Demo-v7.0.0-Setup.exe",
    "Metrology-Workstation-Pro-v7.0.0-Setup.exe"
)

$report = @()

foreach ($name in $artifacts) {
    $filePath = Join-Path $distPath $name
    Write-Host "Checking: $name ..." -NoNewline
    
    if (-not (Test-Path $filePath)) {
        Write-Host " [NOT FOUND]" -ForegroundColor Red
        $report += [PSCustomObject]@{
            Artifact  = $name
            Status    = "MISSING"
            SizeMB    = 0
            Arch      = "N/A"
            SHA256    = "N/A"
            Signature = "N/A"
        }
        continue
    }

    $item = Get-Item $filePath
    $sizeMB = [math]::Round($item.Length / 1MB, 2)

    # 1. SHA-256 Hash
    $hash = (Get-FileHash -Path $filePath -Algorithm SHA256).Hash

    # 2. Architecture Check (PE Header)
    $arch = "x86"
    try {
        $bytes = [System.IO.File]::ReadAllBytes($filePath)
        $peOffset = [System.BitConverter]::ToInt32($bytes, 0x3C)
        $machine = [System.BitConverter]::ToUInt16($bytes, $peOffset + 4)
        if ($machine -eq 0x8664) { $arch = "x64 (AMD64)" }
    } catch {
        $arch = "Unknown"
    }

    # 3. Authenticode Signature Status
    $sig = Get-AuthenticodeSignature -FilePath $filePath
    $sigStatus = $sig.Status.ToString()
    $signer = if ($sig.SignerCertificate) { $sig.SignerCertificate.Subject } else { "None" }

    Write-Host " [OK] ($sizeMB MB, $arch, Signature: $sigStatus)" -ForegroundColor Green

    $report += [PSCustomObject]@{
        Artifact  = $name
        Status    = "PRESENT"
        SizeMB    = $sizeMB
        Arch      = $arch
        SHA256    = $hash
        Signature = "$sigStatus ($signer)"
    }
}

Write-Host "`n=================================================================" -ForegroundColor Cyan
Write-Host " VERIFICATION SUMMARY REPORT" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
$report | Format-Table -Property Artifact, Status, SizeMB, Arch, Signature -AutoSize

Write-Host "SHA-256 RELEASE CHECKSUMS:" -ForegroundColor Yellow
foreach ($r in $report) {
    if ($r.Status -eq "PRESENT") {
        Write-Host "$($r.SHA256)  $($r.Artifact)" -ForegroundColor White
    }
}
Write-Host "=================================================================" -ForegroundColor Cyan
