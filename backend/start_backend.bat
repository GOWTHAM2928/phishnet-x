@echo off
TITLE PhishNet X Backend
cd /d "%~dp0"
echo [PhishNet X] Starting AI Phishing Detection Backend...
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Failed to start backend. Please ensure Python is installed and requirements are met.
    pause
)
