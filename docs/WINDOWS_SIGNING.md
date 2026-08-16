# WINDOWS CODE SIGNING & SMARTSCREEN GUIDANCE — METROLOGY WORKSTATION

**Date**: 2026-08-16  
**Status**: HONEST TRANSPARENCY & SIGNING ROADMAP  

---

## 1. Current Code Signing State: Unsigned (Zero-Cost Baseline)

Under our **Zero/Minimum Upfront Cost** principle, initial independent distribution releases (`v1.0.0`) are published without a commercial EV (Extended Validation) Code Signing Certificate ($350–$600/year).

---

## 2. What Users Experience on Windows 10/11

When downloading and launching an unsigned binary or installer on Windows, **Windows Defender SmartScreen** may display an informational dialog:
> *"Windows protected your PC — Microsoft Defender SmartScreen prevented an unrecognized app from starting."*

### How Users Proceed Safely:
1. Click **"More info"** on the SmartScreen dialog.
2. Verify the application name is **"Metrology Workstation"**.
3. Click **"Run anyway"**.
4. (Optional) Verify the SHA-256 hash of the downloaded installer against the official release checksum in `SHA256SUMS.txt`:
   ```powershell
   Get-FileHash .\Metrology-Workstation-v1.0.0-Windows-x64-Setup.exe -Algorithm SHA256
   ```

---

## 3. Commercial Code Signing Roadmap

As project adoption scales, an EV Code Signing Certificate (e.g. via Sectigo, DigiCert, or SSL.com) or Microsoft Azure Trusted Signing will be integrated into the GitHub Actions release workflow:
- **Phase 1 (Current)**: Unsigned binary with cryptographic SHA-256 checksums published on GitHub Releases and official website.
- **Phase 2 (Future Upgrade)**: Azure Trusted Signing / Hardware Token EV signing automated in `.github/workflows/release.yml`.
