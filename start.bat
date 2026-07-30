@echo off
chcp 65001 >nul
title WiFi Checker by itzlazzy

echo ========================================
echo    WiFi Checker - Program Launcher
echo ========================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed!
    echo Please install Python from https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

:: Check if program file exists
if not exist "wifi_checker.py" (
    echo [ERROR] wifi_checker.py file not found!
    echo Make sure the file is in the same folder as this BAT file.
    echo.
    pause
    exit /b 1
)

:: Install required libraries
echo [*] Checking and installing dependencies...
pip install speedtest-cli requests --quiet
echo.

:: Launch program
echo [*] Launching WiFi Checker...
echo.
python wifi_checker.py

:: Exit
pause