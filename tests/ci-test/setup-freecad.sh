#!/bin/bash
# Setup FreeCAD AppImage - replicates .github/actions/setup-freecad/action.yaml
set -euo pipefail

# Validate required variables have safe defaults
FREECAD_TAG="${FREECAD_TAG:-1.0.2}"
APPIMAGE_DIR="${APPIMAGE_DIR:-$HOME/freecad-appimage}"

# Validate APPIMAGE_DIR is set and non-empty after defaults
if [[ -z "$APPIMAGE_DIR" ]]; then
    echo "ERROR: APPIMAGE_DIR is empty - cannot determine installation path"
    exit 1
fi

echo "=== Setting up FreeCAD $FREECAD_TAG ==="

# Skip if already set up (check for both wrapper scripts)
if [ -d "$APPIMAGE_DIR/squashfs-root/usr/bin" ] && [ -f "/usr/local/bin/freecad" ] && [ -f "/usr/local/bin/freecadcmd" ]; then
    echo "FreeCAD already set up (both wrapper scripts present), skipping download"
    exit 0
fi

# Detect architecture
ARCH=$(uname -m)
case "$ARCH" in
    x86_64)
        ARCH_SUFFIX="x86_64"
        ;;
    aarch64|arm64)
        ARCH_SUFFIX="aarch64"
        ;;
    *)
        echo "ERROR: Unsupported architecture: $ARCH"
        exit 1
        ;;
esac
echo "Detected architecture: $ARCH -> Linux-$ARCH_SUFFIX"

# Use direct download URL to avoid GitHub API rate limits
# Format: FreeCAD_1.0.2-conda-Linux-aarch64-py311.AppImage
APPIMAGE_URL="https://github.com/FreeCAD/FreeCAD/releases/download/${FREECAD_TAG}/FreeCAD_${FREECAD_TAG}-conda-Linux-${ARCH_SUFFIX}-py311.AppImage"
APPIMAGE_NAME="FreeCAD_${FREECAD_TAG}-conda-Linux-${ARCH_SUFFIX}-py311.AppImage"
APPIMAGE_PATH="$APPIMAGE_DIR/FreeCAD.AppImage"

echo "FreeCAD release: $FREECAD_TAG"
echo "AppImage URL: $APPIMAGE_URL"
echo "AppImage name: $APPIMAGE_NAME"

# Download
mkdir -p "$APPIMAGE_DIR"
if [ ! -f "$APPIMAGE_PATH" ]; then
    echo "Downloading FreeCAD AppImage..."
    curl -L --retry 3 --retry-delay 5 --retry-all-errors --connect-timeout 30 --max-time 600 \
        -f -o "$APPIMAGE_PATH" \
        "$APPIMAGE_URL"

    # Verify download succeeded and file exists
    if [[ ! -f "$APPIMAGE_PATH" ]]; then
        echo "ERROR: Download failed - file not found at $APPIMAGE_PATH"
        exit 1
    fi
fi
chmod +x "$APPIMAGE_PATH"

# Extract
cd "$APPIMAGE_DIR"
if [ ! -d "squashfs-root" ]; then
    echo "Extracting AppImage..."
    ./FreeCAD.AppImage --appimage-extract > /dev/null 2>&1
fi

# Verify
if [ ! -d "squashfs-root/usr/bin" ]; then
    echo "ERROR: Extracted AppImage missing expected structure"
    exit 1
fi

echo "Checking AppImage structure..."
# Use find instead of ls|pipe to satisfy shellcheck SC2012
find "$APPIMAGE_DIR/squashfs-root/" -maxdepth 1 -printf '%M %u %g %s %f\n' 2>/dev/null | head -20

# Create wrapper scripts using AppRun
echo "Creating wrapper scripts..."

# Derive APPDIR_PATH from APPIMAGE_DIR for consistency
APPDIR_PATH="$APPIMAGE_DIR/squashfs-root"

# Helper function to install wrapper script
# Uses sudo only if necessary (not root and sudo exists)
install_wrapper() {
    local wrapper_name="$1"
    local wrapper_content="$2"
    local wrapper_path="/usr/local/bin/$wrapper_name"
    local temp_file

    temp_file=$(mktemp)
    echo "$wrapper_content" > "$temp_file"
    chmod +x "$temp_file"

    # Install with sudo if not root and sudo is available
    if [[ $EUID -ne 0 ]]; then
        if command -v sudo &>/dev/null; then
            sudo mv "$temp_file" "$wrapper_path"
            sudo chmod +x "$wrapper_path"
        else
            echo "ERROR: Not running as root and sudo not available, cannot install to $wrapper_path"
            rm -f "$temp_file"
            exit 1
        fi
    else
        mv "$temp_file" "$wrapper_path"
        chmod +x "$wrapper_path"
    fi
}

# freecadcmd wrapper - avoid trailing colon in LD_LIBRARY_PATH
FREECADCMD_WRAPPER="#!/bin/bash
export APPDIR=\"$APPDIR_PATH\"
export LD_LIBRARY_PATH=\"\$APPDIR/usr/lib\${LD_LIBRARY_PATH:+:\$LD_LIBRARY_PATH}\"
exec \"\$APPDIR/usr/bin/freecadcmd\" \"\$@\""

install_wrapper "freecadcmd" "$FREECADCMD_WRAPPER"

# freecad (GUI) wrapper - avoid trailing colon in LD_LIBRARY_PATH
FREECAD_WRAPPER="#!/bin/bash
export APPDIR=\"$APPDIR_PATH\"
export LD_LIBRARY_PATH=\"\$APPDIR/usr/lib\${LD_LIBRARY_PATH:+:\$LD_LIBRARY_PATH}\"
exec \"\$APPDIR/usr/bin/freecad\" \"\$@\""

install_wrapper "freecad" "$FREECAD_WRAPPER"

echo "Wrapper scripts created at /usr/local/bin/freecad{,cmd}"

# Verify installation - fail the script if verification fails
# Use explicit paths to avoid PATH resolution issues
echo "=== Verifying FreeCAD installation ==="

# Check wrapper exists before running
if [[ ! -x /usr/local/bin/freecadcmd ]]; then
    echo "ERROR: freecadcmd wrapper not found or not executable at /usr/local/bin/freecadcmd"
    exit 1
fi

echo "--- freecadcmd --version ---"
if ! /usr/local/bin/freecadcmd --version; then
    echo "ERROR: freecadcmd version check failed"
    exit 1
fi

echo "--- freecadcmd Python test ---"
if ! /usr/local/bin/freecadcmd -c "import sys; print(f'FreeCAD Python: {sys.version}')"; then
    echo "ERROR: FreeCAD Python test failed"
    exit 1
fi

echo "=== FreeCAD setup complete ==="
