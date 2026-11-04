@echo off
setlocal
cd /d "%~dp0"
title Grand Line Draft 5.0.3

echo ==========================================
echo         GRAND LINE DRAFT 5.0.3
echo ==========================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo Erstelle eine lokale Python-Umgebung ...
    where py >nul 2>&1
    if not errorlevel 1 (
        py -3 -m venv .venv
    ) else (
        python -m venv .venv
    )
)

if not exist ".venv\Scripts\python.exe" (
    echo.
    echo FEHLER: Python wurde nicht gefunden oder die virtuelle Umgebung konnte nicht erstellt werden.
    echo Installiere Python 3.10 oder neuer von https://www.python.org/downloads/ und versuche es erneut.
    pause
    exit /b 1
)

call ".venv\Scripts\activate.bat"
if errorlevel 1 (
    echo FEHLER: Die virtuelle Umgebung konnte nicht aktiviert werden.
    pause
    exit /b 1
)

python -c "import streamlit, requests; from PIL import Image" >nul 2>&1
if errorlevel 1 (
    echo Installiere benoetigte Pakete fuer den ersten Start ...
    python -m pip install --disable-pip-version-check -r requirements.txt
    if errorlevel 1 (
        echo.
        echo FEHLER: Pakete konnten nicht installiert werden. Pruefe die Internetverbindung.
        pause
        exit /b 1
    )
) else (
    echo Pakete sind bereits installiert. Der schnelle lokale Start wird verwendet.
)

echo.
echo Starte Grand Line Draft ...
python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --browser.gatherUsageStats false
pause
