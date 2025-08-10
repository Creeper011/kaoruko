#!/bin/bash

echo "========================================"
echo "Starting Kaokuro Bot"
echo "========================================"

# Change to the script's directory to ensure we're in the project root
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "ERROR: Virtual environment not found."
    echo "Please run ./setup.sh first to configure the environment."
    exit 1
fi

echo "Activating virtual environment..."
source .venv/bin/activate
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to activate virtual environment."
    echo "Please run ./setup.sh to fix the environment."
    exit 1
fi

# Check if configuration files exist
if [ ! -f "config.yml" ]; then
    echo "WARNING: config.yml file not found. Make sure it exists."
    echo
fi

if [ ! -f ".env" ]; then
    echo "WARNING: .env file not found. Make sure it exists."
    echo
fi

echo "Starting the bot..."
echo "========================================"
echo

# Run the bot (using virtual environment Python)
python main.py

echo
echo "Bot stopped."