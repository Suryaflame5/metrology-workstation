# PRODUCTION CODE SIGNING STRATEGY — NOVYRAX / METROLOGY WORKSTATION

**Date**: 2026-08-16  
**Auditor**: Lead Security & Release Engineering  
**Application**: Metrology Workstation  

---

## 1. Current Signing Baseline & Honest Status

1. **Development & Sideload Testing**:
   - A local self-signed certificate (`CN=MetrologyWorkstation`) was previously used to validate Windows SDK `MakeAppx` and `SignTool` packaging.
   - Self-signed certificates are **strictly non-trusted** on third-party user machines unless manually imported into `Cert:\LocalMachine\Root` with administrative rights.
2. **Current Public Binary State**:
   - For direct web and GitHub Releases distribution under our **Zero Upfront Cost** baseline, Windows setup binaries are distributed as **Unsigned x64 Binaries with SHA-256 Checksums**.

---

## 2. Windows SmartScreen Mechanics & User Guidance

When an unsigned or newly signed binary is first downloaded on Windows:
- Windows Defender SmartScreen presents an informational prompt (*"Windows protected your PC"*).
- Users click **"More info"** $\to$ **"Run anyway"**.
- As download volume and reputation accumulate on GitHub and the web domain, SmartScreen reputation builds organically.
- Clear step-by-step instructions and SHA-256 verification commands are provided on the official [Download Page](https://novyrax.vercel.app/download).

---

## 3. Cheapest Legitimate Production Code Signing Options

| Provider / Method | Annual Cost | Infrastructure / Hardware | SmartScreen Immediate Reputation | Recommendation |
| :--- | :---: | :--- | :---: | :---: |
| **Azure Trusted Signing** | ~$120 / year ($10/mo) | Cloud-based HSM (No USB dongle needed) | ✅ High (Immediate trust) | **RECOMMENDED FOR NEXT STAGE** |
| **Sectigo / SSL.com EV** | ~$350 – $450 / year | Physical FIPS 140-2 Level 2 USB Token | ✅ High | High maintenance overhead |
| **DigiCert EV Code Sign**| ~$600 – $800 / year | Physical USB Token / Cloud KeyLocker | ✅ High | Expensive for bootstrapped indie |

---

## 4. Implementation Roadmap for Automated GitHub Signing

Once Azure Trusted Signing or an EV certificate is provisioned:
1. Store Azure credentials (`AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`) in GitHub Repository Secrets.
2. Integrate `azure/trusted-signing-action@v0.4.0` in `.github/workflows/release.yml`:
   ```yaml
   - name: Sign Windows Executable
     uses: azure/trusted-signing-action@v0.4.0
     with:
       azure-tenant-id: ${{ secrets.AZURE_TENANT_ID }}
       azure-client-id: ${{ secrets.AZURE_CLIENT_ID }}
       azure-client-secret: ${{ secrets.AZURE_CLIENT_SECRET }}
       endpoint: https://eus.codesigning.azure.net/
       code-signing-account-name: NovyraXSigning
       certificate-profile-name: MetrologyWorkstationProfile
       files: |
         dist/MetrologyWorkstation.exe
         dist/Metrology-Workstation-v1.0.0-Windows-x64-Setup.exe
   ```
3. Cryptographic digest remains anchored in `SHA256SUMS.txt`.
