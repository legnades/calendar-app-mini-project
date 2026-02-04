#!/bin/bash
set -e

APP_NAME="Qubify-ITs_Prodlendar"
PY_FILE="calendar_app.py"
APPDIR="AppDir"
VENV=".build-venv"

echo "Building $APP_NAME AppImage..."
echo

cd "$(dirname "$0")"

# ----------------------------
# Check system deps
# ----------------------------
command -v python3 >/dev/null || { echo "python3 missing"; exit 1; }
command -v python3-venv >/dev/null || {
    echo "ERROR: python3-venv missing"
    echo "Install with: sudo apt install python3-venv"
    exit 1
}

# ----------------------------
# Create build venv
# ----------------------------
if [ ! -d "$VENV" ]; then
    echo "Creating build virtual environment..."
    python3 -m venv "$VENV"
fi

source "$VENV/bin/activate"

pip install --upgrade pip
pip install pyinstaller tkcalendar plyer

# ----------------------------
# Clean old output
# ----------------------------
rm -rf build dist "$APPDIR"

# ----------------------------
# PyInstaller build
# ----------------------------
echo "Running PyInstaller..."
pyinstaller \
    --onefile \
    --windowed \
    --clean \
    --noconfirm \
    --name "$APP_NAME" \
    "$PY_FILE"

# ----------------------------
# AppDir structure
# ----------------------------
echo "Creating AppDir..."
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/share/applications"

cp "dist/$APP_NAME" "$APPDIR/usr/bin/$APP_NAME"
chmod +x "$APPDIR/usr/bin/$APP_NAME"

# Desktop entry
cat > "$APPDIR/$APP_NAME.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=$APP_NAME
Exec=$APP_NAME
Terminal=false
Categories=Utility;
EOF

# AppRun
cat > "$APPDIR/AppRun" <<EOF
#!/bin/sh
HERE="\$(dirname "\$(readlink -f "\$0")")"
exec "\$HERE/usr/bin/$APP_NAME"
EOF
chmod +x "$APPDIR/AppRun"

# ----------------------------
# AppImage tool
# ----------------------------
if [ ! -f appimagetool.AppImage ]; then
    echo "Downloading appimagetool..."
    wget -q https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage -O appimagetool.AppImage
    chmod +x appimagetool.AppImage
fi

ARCH=x86_64 ./appimagetool.AppImage "$APPDIR"

# ----------------------------
# Cleanup
# ----------------------------
deactivate

echo
echo "DONE"
ls *.AppImage
echo
