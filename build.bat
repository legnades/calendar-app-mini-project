@echo off
setlocal EnableExtensions EnableDelayedExpansion

echo ==========================================
echo Building Qubify-ITs Prodlendar
echo ==========================================
echo.

REM =====================================================
REM 1) Check Python
REM =====================================================
where python >nul 2>&1
IF ERRORLEVEL 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo.
    echo Install Python from:
    echo https://www.python.org/downloads/
    echo.
    echo During installation, ENABLE:
    echo  - Add Python to PATH
    echo.
    pause
    exit /b 1
)

REM =====================================================
REM 2) Check PyInstaller
REM =====================================================
python -m PyInstaller --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo ERROR: PyInstaller is not installed.
    echo.
    echo Install it with:
    echo   python -m pip install pyinstaller
    echo.
    pause
    exit /b 1
)

REM =====================================================
REM 3) Check required Python libraries
REM =====================================================
set MISSING_LIBS=

python - <<EOF >nul 2>&1
import tkcalendar
EOF
IF ERRORLEVEL 1 set MISSING_LIBS=%MISSING_LIBS% tkcalendar

python - <<EOF >nul 2>&1
import plyer
EOF
IF ERRORLEVEL 1 set MISSING_LIBS=%MISSING_LIBS% plyer

IF NOT "%MISSING_LIBS%"=="" (
    echo ERROR: Missing required Python libraries:
    echo   %MISSING_LIBS%
    echo.
    echo Install them with:
    echo   python -m pip install%MISSING_LIBS%
    echo.
    pause
    exit /b 1
)

REM =====================================================
REM 4) Build EXE
REM =====================================================
python -m PyInstaller ^
 --onefile ^
 --windowed ^
 --clean ^
 --noconfirm ^
 --hidden-import=plyer ^
 --hidden-import=plyer.platforms ^
 --hidden-import=plyer.platforms.win ^
 --hidden-import=plyer.platforms.win.notification ^
 calendar_app.py

IF NOT EXIST "dist\calendar_app.exe" (
    echo ERROR: Build failed. EXE not found.
    pause
    exit /b 1
)

REM =====================================================
REM 5) Rename EXE
REM =====================================================
ren "dist\calendar_app.exe" "Qubify-ITs Prodlendar.exe"

echo.
echo Build completed successfully.
echo.

REM =====================================================
REM 6) Startup question
REM =====================================================
set /p STARTUP=Start Qubify-ITs Prodlendar on Windows startup? (yes/no): 

IF /I "%STARTUP%" NEQ "yes" (
    echo Startup disabled.
    pause
    exit /b
)

echo Enabling startup...

set "EXE_PATH=%CD%\dist\Qubify-ITs Prodlendar.exe"
set "STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "LNK_PATH=%STARTUP_DIR%\Qubify-ITs Prodlendar.lnk"
set "PS_FILE=%TEMP%\startup_link.ps1"

IF NOT EXIST "%STARTUP_DIR%" (
    mkdir "%STARTUP_DIR%"
)

(
echo $w = New-Object -ComObject WScript.Shell
echo $s = $w.CreateShortcut("%LNK_PATH%")
echo $s.TargetPath = "%EXE_PATH%"
echo $s.WorkingDirectory = "%CD%\dist"
echo $s.Save()
) > "%PS_FILE%"

powershell -NoProfile -ExecutionPolicy Bypass -File "%PS_FILE%"
del "%PS_FILE%" >nul 2>&1

IF EXIST "%LNK_PATH%" (
    echo Startup enabled successfully.
) ELSE (
    echo ERROR: Failed to create startup shortcut.
)

echo.
pause

