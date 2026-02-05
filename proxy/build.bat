@echo off
REM Build script for Meshtastic Proxy GUI (Windows)
REM
REM Usage: build.bat
REM
REM This script builds a standalone Windows application that includes:
REM - Python runtime
REM - Qt GUI framework
REM - All dependencies
REM - Your proxy and AI handler code
REM
REM After modifying multi_client_proxy.py, proxy_gui.py, or ai_handler.py,
REM run this script to rebuild the app with your changes.

echo ======================================
echo Meshtastic Proxy - Build Script
echo ======================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed
    exit /b 1
)

echo Using Python:
python --version
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Install PyInstaller if not already installed
echo Installing PyInstaller...
pip install pyinstaller

REM Clean previous builds
echo Cleaning previous builds...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist

REM Build the application
echo.
echo Building application...
pyinstaller proxy_gui_onedir.spec

REM Check if build was successful
if %errorlevel% equ 0 (
    echo.
    echo ======================================
    echo Build completed successfully!
    echo ======================================
    echo Application: dist\MeshtasticProxy\
    echo Executable: dist\MeshtasticProxy\MeshtasticProxy.exe
    echo.
    echo To run the app:
    echo   dist\MeshtasticProxy\MeshtasticProxy.exe
) else (
    echo.
    echo ======================================
    echo Build failed!
    echo ======================================
    exit /b 1
)

pause
