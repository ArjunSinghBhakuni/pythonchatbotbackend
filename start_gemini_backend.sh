#!/bin/bash

echo "Starting Gemini AI Backend..."
echo "================================"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 is not installed or not in PATH"
    exit 1
fi

# Install dependencies if needed
echo "Installing dependencies..."
pip3 install -r requirements.txt

# Start the backend
echo "Starting Gemini Backend..."
python3 run_gemini_backend.py




