#!/bin/bash
# Metrology V2 macOS Installer
# Version: 2.0.0
# Edition: PRODUCTION

set -e

APP_NAME="MetrologyV2"
VERSION="2.0.0"
INSTALL_DIR="$HOME/.local/share/$APP_NAME"
DATA_DIR="$HOME/.local/share/$APP_NAME/data"
LOGS_DIR="$HOME/.local/share/$APP_NAME/logs"
APP_BUNDLE="/Applications/$APP_NAME.app"

echo "Installing $APP_NAME v$VERSION..."

# Check for root privileges
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (use sudo)"
    exit 1
fi

# Create directories
echo "Creating directories..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$DATA_DIR"
mkdir -p "$LOGS_DIR"

# Install Homebrew if not available
if ! command -v brew &> /dev/null; then
    echo "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Install Python 3.12
echo "Installing Python 3.12..."
brew install python@3.12

# Install required packages
echo "Installing required packages..."
python3.12 -m pip install --upgrade pip
python3.12 -m pip install --requirement requirements.txt

# Create .app bundle
echo "Creating .app bundle..."
APP_CONTENTS="$APP_BUNDLE/Contents"
mkdir -p "$APP_CONTENTS/MacOS"
mkdir -p "$APP_CONTENTS/Resources"

# Create Info.plist
cat > "$APP_CONTENTS/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>$APP_NAME</string>
    <key>CFBundleIdentifier</key>
    <string>com.novyrax.$APP_NAME</string>
    <key>CFBundleName</key>
    <string>$APP_NAME</string>
    <key>CFBundleVersion</key>
    <string>$VERSION</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
</dict>
</plist>
EOF

# Create launcher script
cat > "$APP_CONTENTS/MacOS/$APP_NAME" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/../Resources"
python3.12 -m metrology_v2.desktop.application
EOF

chmod +x "$APP_CONTENTS/MacOS/$APP_NAME"

echo "Installation completed successfully!"
echo "Application installed to: $APP_BUNDLE"
echo "Data directory: $DATA_DIR"
echo "Logs directory: $LOGS_DIR"
