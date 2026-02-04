#!/bin/bash
# Quick start script for WhisperIT

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}WhisperIT - Audio/Video Transcription Application${NC}"
echo ""

# Initialize git repository if not already initialized
if [ ! -d ".git" ]; then
    echo "Initializing git repository with main branch..."
    git init -b main
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ Failed to create virtual environment${NC}"
        exit 1
    fi
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/upgrade requirements
echo "Installing dependencies (this may take a few minutes)..."
pip install --upgrade pip --quiet
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Failed to upgrade pip${NC}"
    exit 1
fi

pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Failed to install dependencies${NC}"
    echo "Try running manually: pip install -r requirements.txt"
    exit 1
fi

# Verify installation
python -c "import PySimpleGUI; import whisper" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠ Warning: Some packages may not be installed correctly${NC}"
    echo "Trying pip install again..."
    pip install -r requirements.txt
fi

# Run the application
echo -e "${GREEN}✓ Ready! Starting WhisperIT...${NC}"
echo ""
python src/gui.py
