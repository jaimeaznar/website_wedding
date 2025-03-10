#!/bin/bash
# setup_app.sh - Script to set up the application (after virtual environment is activated)

# Colors for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print section header
section() {
    echo -e "\n${BLUE}==== $1 ====${NC}\n"
}

# Print success message
success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Print warning message
warning() {
    echo -e "${YELLOW}! $1${NC}"
}

# Print error message
error() {
    echo -e "${RED}✗ $1${NC}"
}

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    error "Virtual environment is not activated."
    echo "Please activate the virtual environment first:"
    echo -e "${GREEN}source venv/bin/activate${NC}"
    exit 1
fi

success "Virtual environment is activated: $(python --version)"

section "Checking required files"

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    error "requirements.txt not found! Please create this file with your dependencies."
    exit 1
fi
success "Found requirements.txt"

# Check if .env file exists
if [ ! -f ".env" ]; then
    error ".env file not found. Please create this file with your environment variables."
    exit 1
fi
success ".env file found"

# Check if setup_update_db.sh exists
if [ ! -f "setup_update_db.sh" ]; then
    error "setup_update_db.sh not found. This file is required for database setup."
    exit 1
fi
success "Found setup_update_db.sh"

# Install dependencies
section "Installing dependencies"
echo "Installing dependencies from requirements.txt..."
pip install --upgrade pip
# Show package installation progress
pip install -r requirements.txt -v
if [ $? -ne 0 ]; then
    warning "Some dependencies failed to install. You may need to install them manually."
else
    success "Dependencies installed successfully"
fi

# Create logs directory if it doesn't exist
section "Setting up logs directory"
if [ ! -d "logs" ]; then
    mkdir -p logs
    success "Logs directory created"
else
    success "Logs directory already exists"
fi

# Run database setup script if migration message is provided
section "Database setup"
if [ -n "$1" ]; then
    echo "Running database setup script with message: $1"
    bash setup_update_db.sh "$1"
    if [ $? -ne 0 ]; then
        error "Database setup failed."
        exit 1
    fi
    success "Database setup complete"
else
    warning "No migration message provided. Skipping database setup."
    echo "To set up the database, run: ./setup_update_db.sh \"Your migration message\""
fi

# Final message
section "Setup complete"
echo -e "Your wedding website is now set up!"
echo -e "To run the application, use: ${GREEN}python run.py${NC}"
echo -e "Access the website at: ${GREEN}http://localhost:5000${NC}"
echo -e "Admin panel available at: ${GREEN}http://localhost:5000/admin${NC}"

echo -e "\nEnjoy your wedding website! 💍 👰 🤵"