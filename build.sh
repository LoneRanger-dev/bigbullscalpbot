#!/bin/bash
# Build script for Render deployment

echo "Starting build process..."

# Check if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "Found requirements.txt"
    cat requirements.txt
else
    echo "ERROR: requirements.txt not found!"
    ls -la
    exit 1
fi

# Install requirements
echo "Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Build completed successfully!"