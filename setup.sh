#!/bin/bash

echo "========================================"
echo "Setting up Kaokuro Bot Environment"
echo "========================================"

# Change to the script's directory to ensure we're in the project root
cd "$(dirname "$0")"
echo "Current directory: $(pwd)"
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 not found. Please install Python 3.12.5"
    exit 1
fi

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "ERROR: pip3 not found. Please install pip."
    exit 1
fi

echo "Checking virtual environment..."
echo

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment."
        exit 1
    fi
    echo "Virtual environment created successfully!"
else
    echo "Virtual environment found."
fi

echo
echo "Activating virtual environment..."
source .venv/bin/activate
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to activate virtual environment."
    exit 1
fi

echo
echo "Installing dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies."
    exit 1
fi

echo
echo "Dependencies installed successfully!"
echo

# Check if configuration files exist
if [ ! -f "config.yml" ]; then
    echo "WARNING: config.yml file not found. Make sure it exists."
    echo
fi

if [ ! -f ".env" ]; then
    echo "WARNING: .env file not found. Make sure it exists."
    echo
fi

echo "========================================"
echo "Environment setup completed!"
echo "You can now run the bot using ./run.sh"
echo "========================================"