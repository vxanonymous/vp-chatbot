#!/bin/bash

# NOTE: This script is designed for macOS systems only.
# For other operating systems, please adapt the commands accordingly.

echo "Running Backend Tests..."
echo

cd backend

# Activate virtual environment
source venv/bin/activate

echo "Running unit tests..."
python -m pytest tests/ -v

echo
echo "Running linting..."
python -m flake8 app/

echo
echo "Running type checking..."
python -m mypy app/

read -p "Press enter to continue..."