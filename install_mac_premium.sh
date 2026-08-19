#!/bin/bash

# Mac Premium Installation Script for Metrology Workstation
# Professional installation script with dependency checking and validation

set -e  # Exit on error

# Version information
PRODUCT_VERSION="2.0.0"
PRODUCT_NAME="Metrology Workstation Premium"
COMPANY_NAME="NovyraX"
INSTALL_PATH="/Applications/Metrology Workstation Premium"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    local level=$1
    local message=$2
    local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    echo -e "[$timestamp] [$level] $message"
    echo "[$timestamp] [$level] $message" >> /tmp/metrology_premium_install.log
}

# Error handling
handle_error() {
    local error_message=$1
    log "ERROR" "$error_message"
    echo -e "${RED}Installation failed: $error_message${NC}"
    exit 1
}

# Check if running as root
check_admin() {
    if [[ $EUID -ne 0 ]]; then
        handle_error "This script must be run as root (use sudo)"
    fi
}

# Check macOS version
check_macos_version() {
    local macos_version=$(sw_vers -productVersion)
    local major_version=$(echo $macos_version | cut -d. -f1)
    
    log "INFO" "macOS version: $macos_version"
    
    if [[ $major_version -lt 10 ]]; then
        handle_error "macOS version $macos_version is not supported. Minimum required: 10.13 (High Sierra)"
    fi
}

# Check Homebrew installation
check_homebrew() {
    if command -v brew &> /dev/null; then
        log "INFO" "Homebrew is installed: $(brew --version)"
        return 0
    else
        log "WARNING" "Homebrew is not installed"
        return 1
    fi
}

# Install Homebrew if needed
install_homebrew() {
    log "INFO" "Installing Homebrew..."
    
    if /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"; then
        log "INFO" "Homebrew installation completed"
        
        # Add Homebrew to PATH for current session
        eval "$(/opt/homebrew/bin/brew shellenv 2>/dev/null)" || eval "$(/usr/local/bin/brew shellenv 2>/dev/null)"
        
        return 0
    else
        handle_error "Failed to install Homebrew"
    fi
}

# Check Python installation
check_python() {
    if command -v python3 &> /dev/null; then
        local python_version=$(python3 --version 2>&1)
        log "INFO" "Python found: $python_version"
        return 0
    else
        log "WARNING" "Python3 not found"
        return 1
    fi
}

# Install Python via Homebrew
install_python() {
    log "INFO" "Installing Python3 via Homebrew..."
    
    if brew install python3; then
        log "INFO" "Python3 installation completed"
        return 0
    else
        handle_error "Failed to install Python3"
    fi
}

# Install Python dependencies
install_dependencies() {
    log "INFO" "Installing Python dependencies..."
    
    local script_dir=$(dirname "$0")
    local requirements_path="$script_dir/requirements_premium.txt"
    
    if [[ ! -f "$requirements_path" ]]; then
        handle_error "requirements_premium.txt not found"
    fi
    
    # Upgrade pip first
    python3 -m pip install --upgrade pip
    
    # Install requirements
    if python3 -m pip install -r "$requirements_path" --upgrade; then
        log "INFO" "Python dependencies installed successfully"
    else
        handle_error "Failed to install Python dependencies"
    fi
}

# Create application directories
create_directories() {
    log "INFO" "Creating application directories..."
    
    local directories=(
        "$INSTALL_PATH"
        "$INSTALL_PATH/data"
        "$INSTALL_PATH/logs"
        "$INSTALL_PATH/plugins"
        "$INSTALL_PATH/temp"
        "$INSTALL_PATH/backups"
        "$HOME/Library/Application Support/MetrologyWorkstationPremium"
    )
    
    for dir in "${directories[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            log "INFO" "Created directory: $dir"
        fi
    done
}

# Copy application files
copy_application_files() {
    log "INFO" "Copying application files..."
    
    local script_dir=$(dirname "$0")
    
    # Copy Python files and directories
    local exclude_patterns=(".git" "__pycache__" "*.pyc" "build" "dist" ".pytest_cache" "*.md" "*.sh")
    
    # Copy main application files
    cp -r "$script_dir/metrology_app" "$INSTALL_PATH/" 2>/dev/null || true
    cp -r "$script_dir/metrology_core" "$INSTALL_PATH/" 2>/dev/null || true
    cp -r "$script_dir/website" "$INSTALL_PATH/" 2>/dev/null || true
    cp -r "$script_dir/standards" "$INSTALL_PATH/" 2>/dev/null || true
    cp "$script_dir/desktop_app.py" "$INSTALL_PATH/" 2>/dev/null || true
    cp "$script_dir/config.py" "$INSTALL_PATH/" 2>/dev/null || true
    
    # Copy assets if they exist
    if [[ -d "$script_dir/assets" ]]; then
        cp -r "$script_dir/assets" "$INSTALL_PATH/"
    fi
    
    log "INFO" "Application files copied successfully"
}

# Create .app bundle
create_app_bundle() {
    log "INFO" "Creating .app bundle..."
    
    local app_bundle="/Applications/Metrology Workstation Premium.app"
    local contents_dir="$app_bundle/Contents"
    local macos_dir="$contents_dir/MacOS"
    local resources_dir="$contents_dir/Resources"
    
    # Remove existing app bundle if it exists
    if [[ -d "$app_bundle" ]]; then
        rm -rf "$app_bundle"
    fi
    
    # Create .app structure
    mkdir -p "$macos_dir"
    mkdir -p "$resources_dir"
    
    # Create Info.plist
    cat > "$contents_dir/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDisplayName</key>
    <string>Metrology Workstation Premium</string>
    <key>CFBundleExecutable</key>
    <string>metrology_launcher</string>
    <key>CFBundleIdentifier</key>
    <string>com.novyrax.metrologypremium</string>
    <key>CFBundleName</key>
    <string>Metrology Workstation Premium</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>${PRODUCT_VERSION}</string>
    <key>CFBundleVersion</key>
    <string>${PRODUCT_VERSION}</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSRequiresAquaSystemAppearance</key>
    <false/>
</dict>
</plist>
EOF
    
    # Create launcher script
    cat > "$macos_dir/metrology_launcher" << EOF
#!/bin/bash
cd "$INSTALL_PATH"
python3 desktop_app.py
EOF
    
    chmod +x "$macos_dir/metrology_launcher"
    
    # Copy application files to Resources
    cp -r "$INSTALL_PATH/"* "$resources_dir/"
    
    # Copy icon if available
    if [[ -f "$INSTALL_PATH/assets/premium_icon.icns" ]]; then
        cp "$INSTALL_PATH/assets/premium_icon.icns" "$resources_dir/"
        # Add icon to Info.plist
        /usr/libexec/PlistBuddy -c "Add :CFBundleIconFile string premium_icon.icns" "$contents_dir/Info.plist" 2>/dev/null || true
    fi
    
    log "INFO" ".app bundle created successfully"
}

# Configure application
configure_application() {
    log "INFO" "Configuring application..."
    
    local config_dir="$HOME/Library/Application Support/MetrologyWorkstationPremium"
    local config_path="$config_dir/settings.json"
    
    cat > "$config_path" << EOF
{
    "version": "${PRODUCT_VERSION}",
    "edition": "PREMIUM",
    "install_path": "${INSTALL_PATH}",
    "first_run": true,
    "auto_update": true,
    "telemetry": false,
    "database_type": "sqlite",
    "log_level": "INFO"
}
EOF
    
    log "INFO" "Application configured"
}

# Create uninstall script
create_uninstall_script() {
    log "INFO" "Creating uninstall script..."
    
    local uninstall_script="/Applications/Metrology Workstation Premium Uninstall.command"
    
    cat > "$uninstall_script" << EOF
#!/bin/bash

# Uninstall Script for Metrology Workstation Premium

echo "Uninstalling Metrology Workstation Premium..."

# Stop application if running
pkill -f "metrology_launcher" || true

# Remove .app bundle
rm -rf "/Applications/Metrology Workstation Premium.app"

# Remove application files
rm -rf "${INSTALL_PATH}"

# Remove app data
rm -rf "$HOME/Library/Application Support/MetrologyWorkstationPremium"

# Remove uninstall script
rm -f "$0"

echo "Uninstallation completed."
EOF
    
    chmod +x "$uninstall_script"
    
    log "INFO" "Uninstall script created"
}

# Run post-installation validation
test_installation() {
    log "INFO" "Running installation validation..."
    
    local validation_errors=0
    
    # Check critical files
    local critical_files=(
        "desktop_app.py"
        "metrology_app/__init__.py"
        "metrology_core/__init__.py"
    )
    
    for file in "${critical_files[@]}"; do
        if [[ ! -f "$INSTALL_PATH/$file" ]]; then
            log "ERROR" "Critical file missing: $file"
            ((validation_errors++))
        fi
    done
    
    # Test Python import
    if cd "$INSTALL_PATH" && python3 -c "import metrology_app; import metrology_core" 2>/dev/null; then
        log "INFO" "Python modules import test passed"
    else
        log "ERROR" "Python modules import test failed"
        ((validation_errors++))
    fi
    
    if [[ $validation_errors -eq 0 ]]; then
        log "INFO" "Installation validation passed"
        return 0
    else
        log "ERROR" "Installation validation failed with $validation_errors errors"
        return 1
    fi
}

# Main installation process
main() {
    log "INFO" "Starting $PRODUCT_NAME v$PRODUCT_VERSION installation"
    log "INFO" "Install path: $INSTALL_PATH"
    
    # Check admin privileges
    check_admin
    
    # Check macOS version
    check_macos_version
    
    # Check and install Homebrew if needed
    if ! check_homebrew; then
        if [[ "$SILENT" != "true" ]]; then
            read -p "Homebrew is not installed. Would you like to install it? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                install_homebrew
            else
                handle_error "Homebrew is required for dependency management"
            fi
        else
            install_homebrew
        fi
    fi
    
    # Check and install Python if needed
    if ! check_python; then
        if [[ "$SILENT" != "true" ]]; then
            read -p "Python3 is not installed. Would you like to install it? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                install_python
            else
                handle_error "Python3 is required for installation"
            fi
        else
            install_python
        fi
    fi
    
    # Install dependencies
    if [[ "$SKIP_DEPENDENCIES" != "true" ]]; then
        install_dependencies
    fi
    
    # Create directories
    create_directories
    
    # Copy application files
    copy_application_files
    
    # Create .app bundle
    create_app_bundle
    
    # Configure application
    configure_application
    
    # Create uninstall script
    create_uninstall_script
    
    # Validate installation
    if test_installation; then
        log "INFO" "Installation completed successfully!"
        
        echo ""
        echo -e "${GREEN}========================================${NC}"
        echo -e "${GREEN}Installation Complete!${NC}"
        echo -e "${GREEN}========================================${NC}"
        echo -e "${BLUE}Product:${NC} $PRODUCT_NAME"
        echo -e "${BLUE}Version:${NC} $PRODUCT_VERSION"
        echo -e "${BLUE}Location:${NC} $INSTALL_PATH"
        echo ""
        echo "You can now launch the application from:"
        echo "  - Applications folder"
        echo "  - Spotlight search: 'Metrology Workstation Premium'"
        echo "  - Command: open '/Applications/Metrology Workstation Premium.app'"
        echo ""
        echo "To uninstall, run: '/Applications/Metrology Workstation Premium Uninstall.command'"
        echo ""
    else
        handle_error "Installation validation failed"
    fi
}

# Parse command line arguments
SILENT="false"
SKIP_DEPENDENCIES="false"
LICENSE_KEY=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --silent)
            SILENT="true"
            shift
            ;;
        --skip-dependencies)
            SKIP_DEPENDENCIES="true"
            shift
            ;;
        --license-key)
            LICENSE_KEY="$2"
            shift 2
            ;;
        --install-path)
            INSTALL_PATH="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--silent] [--skip-dependencies] [--license-key KEY] [--install-path PATH]"
            exit 1
            ;;
    esac
done

# Run main installation
main