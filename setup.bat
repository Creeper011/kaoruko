@echo off
echo ========================================
echo Setting up Kaokuro Bot Environment
echo ========================================

REM Change to the script's directory to ensure we're in the project root
cd /d "%~dp0"
echo Current directory: %CD%
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.12.5
    pause
    exit /b 1
)

pip --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Pip not found. Please install pip.
    pause
    exit /b 1
)

echo Checking virtual environment...
echo.

REM Check if virtual environment exists
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo Virtual environment created successfully!
) else (
    echo Virtual environment found.
)

echo.
echo Activating virtual environment...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment.
    pause
    exit /b 1
)

echo.
echo Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo Dependencies installed successfully!
echo.

REM Check if configuration files exist
if not exist "config.yml" (
    echo WARNING: config.yml file not found. Make sure it exists.
    echo.
)

if not exist ".env" (
    echo WARNING: .env file not found. Make sure it exists.
    echo.
)

echo ========================================
echo Environment setup completed!
echo You can now run the bot using run.bat
echo ========================================
pause