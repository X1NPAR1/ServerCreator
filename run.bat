@echo off
REM ===========================================================================
REM  ServerCreator - run from source without installing the setup
REM  Publisher: X1NPAR1
REM
REM  This script locates Python, creates a local virtual environment on first
REM  use, installs the dependencies once, and launches the application.
REM ===========================================================================
setlocal enableextensions
chcp 65001 > nul
title ServerCreator - Launcher (X1NPAR1)
cd /d "%~dp0"

REM --- 1) Locate a real Python interpreter ----------------------------------
set "PYEXE="
where py >nul 2>nul && (py -3 --version >nul 2>nul && set "PYEXE=py -3")
if not defined PYEXE (
    where python >nul 2>nul && (python --version >nul 2>nul && set "PYEXE=python")
)

if not defined PYEXE (
    echo.
    echo [ServerCreator] Python bulunamadi / Python was not found.
    echo.
    echo Lutfen Python 3.10+ surumunu kurun ve "Add Python to PATH" secenegini isaretleyin.
    echo Please install Python 3.10+ and enable "Add Python to PATH".
    echo.
    echo Indirme / Download: https://www.python.org/downloads/
    echo.
    start "" "https://www.python.org/downloads/"
    pause
    exit /b 1
)

REM --- 2) Create the virtual environment on first run -----------------------
if not exist ".venv\Scripts\python.exe" (
    echo [ServerCreator] Sanal ortam olusturuluyor / Creating virtual environment...
    %PYEXE% -m venv .venv
    if errorlevel 1 (
        echo [ServerCreator] Sanal ortam olusturulamadi / Failed to create venv.
        pause
        exit /b 1
    )
)

set "VENV_PY=.venv\Scripts\python.exe"

REM --- 3) Install dependencies once (tracked by a marker file) --------------
if not exist ".venv\.deps_installed" (
    echo [ServerCreator] Bagimliliklar kuruluyor / Installing dependencies...
    "%VENV_PY%" -m pip install --upgrade pip >nul
    "%VENV_PY%" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [ServerCreator] Bagimliliklar kurulamadi / Failed to install dependencies.
        pause
        exit /b 1
    )
    echo installed> ".venv\.deps_installed"
)

REM --- 4) Launch the application --------------------------------------------
echo [ServerCreator] Baslatiliyor / Launching...
"%VENV_PY%" main.py
if errorlevel 1 (
    echo.
    echo [ServerCreator] Uygulama bir hata ile kapandi / The application exited with an error.
    pause
)

endlocal
