# V5 KNOWN LIMITATIONS & SCOPE BOUNDARIES

**Product**: Metrology Workstation  
**Version**: `v5.0.0` (Production Engineering Workstation)  
**Date**: August 18, 2026  

---

## 1. Explicit Scope & Capability Boundaries

To prevent ambiguity and maintain mathematical rigor, the following operational boundaries are explicitly defined:

1. **Hardware Communication Protocols**:
   - The acquisition studio is designated as **MANUAL / CSV IMPORT**.
   - Direct hardware interface protocols (e.g. RS-232, USB-TMC, IEEE-488 GPIB, LXI VISA) are scheduled for hardware-specific drivers in future generation releases.
2. **Supported Decision Rules**:
   - Supported rules are strictly:
     - ANSI/NCSL Z540.3-2006 Method 6 (Default 2% False Accept Guardband)
     - ANSI/NCSL Z540.3-2006 Method 5 (Root-Sum-Square Guardband)
     - ISO 14253-1:2017 (Complete Conformance Guardband)
     - Simple 4:1 TUR Decision Rule
   - Proprietary custom laboratory decision equations require conversion into standard GUM/Z540.3 parameters.
3. **Multi-Variate Non-Linear GUM Models**:
   - First-order Taylor series propagation assumes local linearity of measurement functions around the mean.
   - For highly non-linear functions where higher-order Taylor terms are required, engineers should execute the included **JCGM 101:2008 Monte Carlo Engine** ($10^5$ to $10^6$ trials).
4. **Operating System Support**:
   - Currently compiled and native to **Windows 10 / Windows 11 (64-bit)** via standalone PE x64 binary and Inno Setup installer.
