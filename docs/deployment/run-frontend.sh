#!/bin/bash

# NOTE: This script is designed for macOS systems only.
# For other operating systems, please adapt the commands accordingly.

echo "Starting Vacation Planning System Frontend..."
echo

cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
    echo
fi

echo "Starting React development server..."
npm run dev