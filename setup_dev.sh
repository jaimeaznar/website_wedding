#!/bin/bash

# Exit on error
set -e

echo "Setting up development environment..."

# Create and activate virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Install pre-commit hooks
echo "Installing pre-commit hooks..."
pre-commit install

# Create necessary directories if they don't exist
mkdir -p logs
mkdir -p htmlcov

echo "Development environment setup complete!"
echo "To activate the environment, run: source venv/bin/activate" 