#!/bin/bash
# Quick start script for WhisperIT
# Requires: conda (miniconda or anaconda)

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}WhisperIT - Audio/Video Transcription Application${NC}"
echo ""

# Check if conda is installed
if ! command -v conda &> /dev/null; then
    echo -e "${RED}✗ Conda is not installed${NC}"
    echo "Install Miniconda from: https://docs.conda.io/projects/miniconda/en/latest/"
    exit 1
fi

# Initialize git repository if not already initialized
if [ ! -d ".git" ]; then
    echo "Initializing git repository with main branch..."
    git init -b main
fi

# Create conda environment if it doesn't exist
ENV_NAME="whisperit"
if ! conda env list | grep -q "^${ENV_NAME}"; then
    echo "Creating conda environment 'whisperit' with Python 3.11..."
    conda create -n "${ENV_NAME}" python=3.11 -y
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ Failed to create conda environment${NC}"
        exit 1
    fi
fi

# Activate conda environment
echo "Activating conda environment..."
eval "$(conda shell.bash hook)"
conda activate "${ENV_NAME}"

# Install/upgrade pip
echo "Installing dependencies (this may take a few minutes)..."
pip install --upgrade pip --quiet
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Failed to upgrade pip${NC}"
    exit 1
fi

# Install requirements
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Failed to install dependencies${NC}"
    echo "Try running manually: pip install -r requirements.txt"
    exit 1
fi

# Verify installation
python -c "from faster_whisper import WhisperModel; import PyQt6" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠ Warning: Some packages may not be installed correctly${NC}"
    echo "Trying pip install again..."
    pip install -r requirements.txt
fi

# Run the application
echo -e "${GREEN}✓ Ready! Starting WhisperIT...${NC}"
echo ""
python src/gui.py
