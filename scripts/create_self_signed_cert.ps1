<#
.SYNOPSIS
    Creates a self-signed Authenticode Code-Signing Certificate and optionally signs CALIBRA executables.

.DESCRIPTION
    Generates a 2048-bit SHA-256 code-signing certificate in the CurrentUser certificate store.
    Exports the PFX (kept private, never committed to git) and can sign executables using Set-AuthenticodeSignature.

.NOTES
    IMPORTANT HONESTY & SECURITY NOTICE:
    A self-signed certificate establishes trust ONLY on machines where it has been manually trusted
    (e.g., imported into the Windows 'Trusted Root Certification Authorities' store).
    It does NOT bypass Microsoft Defender SmartScreen on unknown customer PCs.
    For customer PCs to not see SmartScreen warnings, a commercial publicly-trusted code-signing certificate
    (EV Cert) or Microsoft Store distribution is required.
#>

[CmdletBinding()]
param(
    [string]$TargetFile = "",
    [string]$CertSubject = "CN=CALIBRA Metrology Workstation Development",
    [string]$FriendlyName = "CALIBRA Metrology Development Certificate",
    [string]$PfxOutputPath = "$PSScriptRoot\..\assets\calibra-dev.pfx",
    [switch]$TrustLocally,
    [switch]$SignOnly
)

$ErrorActionPreference = "Stop"

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host " CALIBRA Metrology Workstation - Authenticode Signing Utility" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan

# 1. Locate or create certificate
$cert = Get-ChildItem -Path "Cert:\CurrentUser\My" -CodeSigningCert -ErrorAction SilentlyContinue |
    Where-Object { $_.Subject -like "*$CertSubject*" -or $_.FriendlyName -eq $FriendlyName } |
    Select-Object -First 1

if (-not $cert -and -not $SignOnly) {
    Write-Host "`n[*] Creating new self-signed Code-Signing Certificate..." -ForegroundColor Yellow
    $cert = New-SelfSignedCertificate `
        -Type Custom `
        -Subject $CertSubject `
        -FriendlyName $FriendlyName `
        -CertStoreLocation "Cert:\CurrentUser\My" `
        -KeyExportPolicy Exportable `
        -KeySpec Signature `
        -KeyLength 2048 `
        -KeyAlgorithm RSA `
        -HashAlgorithm SHA256 `
        -KeyUsage DigitalSignature `
        -TextExtension @("2.5.29.37={text}1.3.6.1.5.5.7.3.3") `
        -NotAfter (Get-Date).AddYears(3)

    Write-Host " [+] Created certificate: $($cert.Thumbprint)" -ForegroundColor Green
} elseif ($cert) {
    Write-Host "`n[+] Found existing Code-Signing Certificate: $($cert.Thumbprint)" -ForegroundColor Green
} else {
    Write-Error "No existing certificate found. Remove -SignOnly to create one."
}

# 2. Export PFX
$pfxFile = [System.IO.Path]::GetFullPath($PfxOutputPath)
$password = ConvertTo-SecureString -String "CalibraDev2026!" -Force -AsPlainText

if (-not (Test-Path $pfxFile) -and -not $SignOnly) {
    $pfxDir = [System.IO.Path]::GetDirectoryName($pfxFile)
    if (-not (Test-Path $pfxDir)) { New-Item -ItemType Directory -Path $pfxDir -Force | Out-Null }
    
    Export-PfxCertificate `
        -Cert "Cert:\CurrentUser\My\$($cert.Thumbprint)" `
        -FilePath $pfxFile `
        -Password $password | Out-Null
    Write-Host " [+] Exported private PFX to: $pfxFile" -ForegroundColor Green
    Write-Host "     (NOTE: .pfx is excluded by .gitignore and must NEVER be committed to git)" -ForegroundColor DarkGray
}

# 3. Optional Local Trust
if ($TrustLocally) {
    Write-Host "`n[*] Trusting certificate in CurrentUser Root store..." -ForegroundColor Yellow
    try {
        $rootStore = New-Object System.Security.Cryptography.X509Certificates.X509Store("Root", "CurrentUser")
        $rootStore.Open("ReadWrite")
        $rootStore.Add($cert)
        $rootStore.Close()
        Write-Host " [+] Certificate trusted in CurrentUser\Root (SmartScreen warning silenced on THIS PC)" -ForegroundColor Green
    } catch {
        Write-Warning "Failed to add to Root store: $_"
    }
}

# 4. Sign Target File if provided
if ($TargetFile -and (Test-Path $TargetFile)) {
    $resolvedTarget = [System.IO.Path]::GetFullPath($TargetFile)
    Write-Host "`n[*] Signing target binary: $resolvedTarget" -ForegroundColor Yellow
    
    try {
        $sig = Set-AuthenticodeSignature `
            -FilePath $resolvedTarget `
            -Certificate $cert `
            -HashAlgorithm SHA256 `
            -TimestampServer "http://timestamp.digicert.com"
        
        Write-Host " [+] Signature Status: $($sig.Status)" -ForegroundColor Green
        Write-Host "     Signer: $($sig.SignerCertificate.Subject)" -ForegroundColor DarkGray
    } catch {
        Write-Warning "Timestamp server unreachable, signing without timestamp..."
        $sig = Set-AuthenticodeSignature `
            -FilePath $resolvedTarget `
            -Certificate $cert `
            -HashAlgorithm SHA256
        Write-Host " [+] Signature Status: $($sig.Status)" -ForegroundColor Green
    }
}

Write-Host "`n=================================================================" -ForegroundColor Cyan
Write-Host " Authenticode Operation Complete" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
