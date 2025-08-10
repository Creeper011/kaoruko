@echo off
echo ========================================
echo Starting Kaokuro Bot
echo ========================================

REM Change to the script's directory to ensure we're in the project root
cd /d "%~dp0"

REM Check if virtual environment exists
if not exist ".venv" (
    echo ERROR: Virtual environment not found.
    echo Please run setup.bat first to configure the environment.
    pause
    exit /b 1
)

echo Activating virtual environment...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment.
    echo Please run setup.bat to fix the environment.
    pause
    exit /b 1
)

REM Check if configuration files exist
if not exist "config.yml" (
    echo WARNING: config.yml file not found. Make sure it exists.
    echo.
)

if not exist ".env" (
    echo WARNING: .env file not found. Make sure it exists.
    echo.
)

echo Starting the bot...
echo ========================================
echo.

REM Run the bot (using virtual environment Python)
python main.py --debug

echo.
echo Bot stopped.
pause