#!/bin/bash

# DWH Project Analyzer - Startup Script
# =====================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════╗"
echo "║           🏗️  DWH Project Analyzer                    ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed. Please install Python 3.10+${NC}"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}📦 Creating virtual environment...${NC}"
    python3 -m venv "$VENV_DIR"
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}🔄 Activating virtual environment...${NC}"
source "$VENV_DIR/bin/activate"

# Check if dependencies are installed
if [ ! -f "$VENV_DIR/.deps_installed" ]; then
    echo -e "${YELLOW}📥 Installing dependencies...${NC}"
    pip install --upgrade pip -q
    pip install -r "$SCRIPT_DIR/requirements.txt"
    touch "$VENV_DIR/.deps_installed"
    echo -e "${GREEN}✅ Dependencies installed${NC}"
else
    echo -e "${GREEN}✅ Dependencies already installed${NC}"
fi

# Check for .env file
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    if [ -f "$SCRIPT_DIR/env.example" ]; then
        echo -e "${YELLOW}⚠️  No .env file found. Creating from env.example...${NC}"
        cp "$SCRIPT_DIR/env.example" "$SCRIPT_DIR/.env"
        echo -e "${YELLOW}📝 Please edit .env file and add your API keys${NC}"
    fi
fi

# Start the application
echo ""
echo -e "${GREEN}🚀 Starting DWH Project Analyzer...${NC}"
echo -e "${BLUE}   Open http://localhost:8501 in your browser${NC}"
echo ""

streamlit run "$SCRIPT_DIR/app.py" --server.headless=true
