 # GitHub Release Structure Guide for Metrology Workstation v2.0.0

## Overview

This guide outlines the recommended GitHub repository structure and release process for Metrology Workstation v2.0.0 Premium. The website now points to GitHub Releases as the distribution backend, making proper release structure essential.

## Repository Structure

```
metrology-workstation/
├── .github/
│   └── workflows/
│       └── release.yml (optional CI/CD for releases)
├── releases/
│   ├── v2.0.0/
│   │   ├── MetrologyWorkstation-2.0.0-win-x64.exe
│   │   ├── MetrologyWorkstation-2.0.0-macos.dmg
│   │   ├── SHA256SUMS.txt
│   │   ├── SHA256SUMS.txt.asc (optional GPG signature)
│   │   └── RELEASE_NOTES.md
│   └── (future versions will follow same pattern)
├── source/ (or metrology_app/)
├── documentation/
├── README.md
└── LICENSE
```

## Release Asset Naming Convention

### Windows Installer
- **File**: `MetrologyWorkstation-2.0.0-win-x64.exe`
- **Size**: ~120 MB
- **Platform**: Windows 10/11 (64-bit)
- **Format**: Executable installer (Inno Setup or similar)

### macOS Package
- **File**: `MetrologyWorkstation-2.0.0-macos.dmg`
- **Size**: ~115 MB
- **Platform**: macOS 10.13+
- **Format**: Disk image with .app bundle

### Checksum File
- **File**: `SHA256SUMS.txt`
- **Content**: SHA-256 hashes for all release assets
- **Format**: Standard checksum file format

## SHA256SUMS.txt Format

```
SHA256 (MetrologyWorkstation-2.0.0-win-x64.exe) = <actual_hash>
SHA256 (MetrologyWorkstation-2.0.0-macos.dmg) = <actual_hash>
```

### Generating Checksums

**Windows (PowerShell):**
```powershell
Get-FileHash MetrologyWorkstation-2.0.0-win-x64.exe -Algorithm SHA256 | Format-List
Get-FileHash MetrologyWorkstation-2.0.0-macos.dmg -Algorithm SHA256 | Format-List
```

**macOS/Linux:**
```bash
shasum -a 256 MetrologyWorkstation-2.0.0-win-x64.exe
shasum -a 256 MetrologyWorkstation-2.0.0-macos.dmg
```

## GitHub Release Process

### Step 1: Build Release Assets

1. Run the cross-platform build script:
   ```bash
   python build_premium_cross_platform.py
   ```

2. Verify the generated installers:
   - Windows: `dist/MetrologyWorkstation-2.0.0-win-x64.exe`
   - macOS: `dist/MetrologyWorkstation-2.0.0-macos.dmg`

3. Generate SHA-256 checksums:
   ```bash
   shasum -a 256 dist/* > SHA256SUMS.txt
   ```

### Step 2: Create GitHub Release

1. Go to GitHub repository: `https://github.com/novyrax/metrology-workstation`
2. Navigate to **Releases** section
3. Click **Create a new release**
4. Tag version: `v2.0.0`
5. Release title: `Metrology Workstation v2.0.0 Premium`
6. Description: Use release notes from `RELEASE_NOTES.md`

### Step 3: Upload Release Assets

Upload the following files to the release:
- `MetrologyWorkstation-2.0.0-win-x64.exe`
- `MetrologyWorkstation-2.0.0-macos.dmg`
- `SHA256SUMS.txt`

### Step 4: Update Website Checksums

After creating the release, update the checksums in `website/download.html`:

```html
<!-- Replace PENDING_RELEASE_CHECKSUM with actual hashes -->
<code>ACTUAL_WINDOWS_SHA256_HASH</code>
<code>ACTUAL_MACOS_SHA256_HASH</code>
```

## Release Notes Template

```markdown
# Metrology Workstation v2.0.0 Premium

## Release Date
August 19, 2026

## New Features
- Advanced Analytics & Measurement Intelligence
- Fleet Management System
- Enterprise Certificate Generation
- Full API & Database Integration
- Plugin System & Custom Scripting

## Platform Support
- Windows 10/11 (64-bit)
- macOS 10.13+

## Installation
- Windows: Download and run the installer
- macOS: Download DMG and drag to Applications

## Verification
Verify download integrity using SHA-256 checksums provided in SHA256SUMS.txt

## Documentation
Full documentation available at: https://novyrax.vercel.app/docs
```

## Website Integration

The website now points to GitHub Releases:

```html
<!-- Windows Download -->
<a href="https://github.com/novyrax/metrology-workstation/releases/download/v2.0.0/MetrologyWorkstation-2.0.0-win-x64.exe">
  Download Windows Installer
</a>

<!-- macOS Download -->
<a href="https://github.com/novyrax/metrology-workstation/releases/download/v2.0.0/MetrologyWorkstation-2.0.0-macos.dmg">
  Download macOS Package
</a>
```

## Future Release Process

For future versions (v2.0.1, v2.1.0, etc.):

1. Update version numbers in build scripts
2. Build new release assets
3. Create new GitHub release with updated tag
4. Upload new assets
5. **No website changes needed** - links automatically point to latest release

## Security Best Practices

1. **Code Signing**: Sign Windows executables and macOS packages
2. **Checksum Verification**: Always provide SHA-256 checksums
3. **GPG Signatures**: Optionally sign checksums with GPG key
4. **Release Notes**: Document all changes and security updates
5. **Access Control**: Limit release creation to authorized team members

## Troubleshooting

### Download Links Not Working
- Verify GitHub release is published (not just draft)
- Check asset filenames match exactly
- Ensure repository is public or user has access

### Checksum Mismatch
- Regenerate checksums after any file changes
- Verify correct algorithm (SHA-256)
- Check file corruption during upload

### Version Conflicts
- Use semantic versioning (MAJOR.MINOR.PATCH)
- Tag releases with `v` prefix (v2.0.0)
- Update build scripts before creating new releases

## Maintenance

### Regular Tasks
- Monitor GitHub release downloads
- Update documentation for new features
- Archive old releases if needed
- Review and update security practices

### Emergency Rollback
- If critical bug discovered, create patch release
- Update website to point to stable version
- Document rollback procedure in release notes

---

**Next Steps:**
1. Build v2.0.0 release assets using `build_premium_cross_platform.py`
2. Generate SHA-256 checksums
3. Create GitHub release v2.0.0
4. Upload assets to release
5. Update website checksums in `download.html`
6. Test download links from website
