# CUSTOMER SUPPORT & OPERATIONAL GUIDE — NOVYRAX / METROLOGY WORKSTATION

**Official Support Contact**: `novyrax04@gmail.com`  
**Website**: `https://novyrax.vercel.app`  

---

## 1. Common Support Scenarios & Resolution Playbook

### 1.1 License Activation & Recovery
- **Problem**: Customer lost their signed license token JSON or changed workstations.
- **Resolution**: Customer emails `novyrax04@gmail.com` from their registered purchase email. The backend entitlement system regenerates the canonical signed token and delivers it within 12 business hours.

### 1.2 Windows SmartScreen Prompt During Installation
- **Problem**: Windows Defender SmartScreen displays *"Windows protected your PC"*.
- **Resolution**: Click **"More info"** $\to$ **"Run anyway"**. Verify the SHA-256 hash in PowerShell:
  ```powershell
  Get-FileHash .\Metrology-Workstation-v1.0.0-Windows-x64-Setup.exe -Algorithm SHA256
  ```

### 1.3 Refund Requests (30-Day Guarantee)
- **Problem**: Customer requests a refund within 30 days of purchase.
- **Resolution**: Support verifies the purchase in the MoR dashboard (Dodo / Lemon Squeezy), clicks "Issue Full Refund", and sends confirmation to the customer.

### 1.4 Mathematical & Scientific Inquiries
- **Problem**: Calibration technician requires explanation of Welch-Satterthwaite degrees of freedom or Method 6 guardband boundaries.
- **Resolution**: Direct the customer to the built-in **12-Stage Mathematical Replay viewer** inside the workstation and reference [Documentation](https://novyrax.vercel.app/docs).

---

## 2. Support SLAs by Plan

| Plan | Response SLA | Channels |
| :--- | :---: | :---: |
| **Community / Free** | Best Effort (48–72h) | Public GitHub Discussions |
| **Professional** | Within 24 Business Hours | Email (`novyrax04@gmail.com`) |
| **Business / Team** | Within 12 Business Hours | Priority Email & Screen Share |
| **Enterprise** | Within 4 Business Hours | Dedicated Technical Account Engineer |
