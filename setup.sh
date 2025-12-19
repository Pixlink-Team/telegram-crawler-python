#!/bin/bash

# Setup script for Telegram Service

echo "🚀 Telegram Service Setup Script"
echo "================================="
echo ""

# Check Python version
echo "✓ Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "  Python version: $python_version"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "  ✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate
echo "  ✓ Activated"
echo ""

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt
echo "  ✓ Dependencies installed"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file from .env.example..."
    cp .env.example .env
    echo "  ✓ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env file and set your configuration:"
    echo "   - TELEGRAM_API_ID"
    echo "   - TELEGRAM_API_HASH"
    echo "   - LARAVEL_BASE_URL"
    echo "   - WEBHOOK_SECRET_TOKEN"
    echo "   - API_SECRET_KEY"
    echo ""
else
    echo "✓ .env file already exists"
    echo ""
fi

# Create sessions directory
if [ ! -d "sessions" ]; then
    echo "📁 Creating sessions directory..."
    mkdir -p sessions
    echo "  ✓ Sessions directory created"
else
    echo "✓ Sessions directory already exists"
fi
echo ""

echo "✅ Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your credentials"
echo "2. Get Telegram API credentials from https://my.telegram.org"
echo "3. Run the service:"
echo "   python -m app.main"
echo "   or"
echo "   uvicorn app.main:app --reload"
echo ""
echo "📖 For more information, read README.md"
echo ""
