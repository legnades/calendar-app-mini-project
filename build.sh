#!/bin/bash

echo "Building Qubify-ITs Prodlendar..."
echo

# ----------------------------
# Check Python
# ----------------------------
if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: Python 3 is not installed."
    echo "Install it with:"
    echo "  sudo apt update && sudo apt install python3 python3-pip"
    exit 1
fi

# ----------------------------
# Check pip
# ----------------------------
if ! command -v pip3 >/dev/null 2>&1; then
    echo "ERROR: pip is not installed."
    echo "Install it with:"
    echo "  sudo apt install python3-pip"
    exit 1
fi

# ----------------------------
# Required Python libraries
# ----------------------------
REQUIRED_LIBS=("tkcalendar" "plyer" "pyinstaller")

MISSING=()

for lib in "${REQUIRED_LIBS[@]}"; do
    if ! python3 - <<EOF
import importlib.util
exit(0 if importlib.util.find_spec("$lib") else 1)
EOF
    then
        MISSING+=("$lib")
    fi
done

if [ ${#MISSING[@]} -ne 0 ]; then
    echo
    echo "Missing Python libraries:"
    for lib in "${MISSING[@]}"; do
        echo "  - $lib"
    done
    echo
    echo "Install them with:"
    echo "  pip3 install ${MISSING[*]}"
    exit 1
fi

# ----------------------------
# Build app
# ----------------------------
python3 -m PyInstaller \
    --onefile \
    --windowed \
    --clean \
    --noconfirm \
    --name "Qubify-ITs_Prodlendar" \
    calendar_app.py

echo
echo "Build completed successfully."
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

echo
read -p "Press ENTER to exit..."
