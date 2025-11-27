#!/bin/bash

# NOTE: This script is designed for macOS systems only.
# For other operating systems, please adapt the commands accordingly.

echo "Starting Vacation Planning System Backend..."
echo

cd backend

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "Virtual environment created."
    echo
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing/Updating dependencies..."
pip install -r requirements.txt

echo
echo "Checking environment variables..."
if [ ! -f ".env" ]; then
    echo "WARNING: .env file not found!"
    echo "Please copy .env.example to .env and add your OpenAI API key"
    echo
    read -p "Press enter to continue..."
fi

echo "Starting FastAPI server..."
echo
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000