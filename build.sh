#!/bin/bash

set -e

echo "Building Qubify-ITs Prodlendar..."
echo

# ----------------------------
# Ensure we're in script directory
# ----------------------------
cd "$(dirname "$0")"

# ----------------------------
# Check Python
# ----------------------------
if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: Python 3 is not installed."
    echo "Install it with:"
    echo "  sudo apt update && sudo apt install python3 python3-pip python3-venv python3-tk"
    exit 1
fi

# ----------------------------
# Check tkinter
# ----------------------------
set +e
python3 - <<EOF
import tkinter
EOF
TK_OK=$?
set -e

if [ $TK_OK -ne 0 ]; then
    echo "ERROR: tkinter is missing. Install it with:"
    echo "  sudo apt install python3-tk"
    exit 1
fi

# ----------------------------
# Virtual environment
# ----------------------------
VENV_DIR="./qubify-venv"

if [ -d "$VENV_DIR" ] && [ ! -f "$VENV_DIR/bin/activate" ]; then
    echo "Broken virtual environment detected. Recreating..."
    rm -rf "$VENV_DIR"
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

# ----------------------------
# Install required Python libraries inside venv
# ----------------------------
REQUIRED_LIBS=("tkcalendar" "plyer" "pyinstaller")
for lib in "${REQUIRED_LIBS[@]}"; do
    if ! python -c "import $lib" >/dev/null 2>&1; then
        echo "Installing $lib in virtual environment..."
        pip install --upgrade pip
        pip install "$lib"
    fi
done

# ----------------------------
# Build with PyInstaller inside venv
# ----------------------------
echo "Running PyInstaller..."
python -m PyInstaller \
    --onefile \
    --windowed \
    --clean \
    --noconfirm \
    --name "Qubify-ITs_Prodlendar" \
    calendar_app.py

echo
echo "Build completed successfully."
echo "Executable is located at ./dist/Qubify-ITs_Prodlendar"
echo

# ----------------------------
# Startup question
# ----------------------------
read -p "Start Qubify-ITs Prodlendar on system startup? (yes/no): " STARTUP

if [[ "$STARTUP" == "yes" ]]; then
    echo "Enabling startup..."
    mkdir -p ~/.config/systemd/user
    SERVICE_FILE=~/.config/systemd/user/qubify-prodlendar.service
    cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=Qubify-ITs Prodlendar

[Service]
ExecStart=$(pwd)/dist/Qubify-ITs_Prodlendar
Restart=on-failure

[Install]
WantedBy=default.target
EOF
    systemctl --user daemon-reload
    systemctl --user enable qubify-prodlendar.service
    echo "Startup enabled successfully."
else
    echo "Startup disabled."
fi

# ----------------------------
# Deactivate venv and finish
# ----------------------------
deactivate || true
echo
read -p "Press ENTER to exit..."
