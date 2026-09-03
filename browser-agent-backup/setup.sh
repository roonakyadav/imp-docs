#!/bin/bash

# Professional Browser Agent Setup Script
# This script automates the installation of dependencies and browser setup.

echo "🚀 Starting Professional Browser Agent setup..."

# 1. Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
else
    echo "✅ Virtual environment already exists."
fi

# 2. Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# 3. Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# 4. Install dependencies
echo "📥 Installing dependencies from requirements.txt..."
pip install -r requirements.txt

# 5. Install Playwright browsers
echo "🌐 Installing Playwright browsers..."
playwright install chromium

# 6. Create required directories
echo "📁 Creating system directories..."
mkdir -p logs recordings screenshots sessions src/dashboard/static

# 7. Setup .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  IMPORTANT: Ensure Ollama is running and qwen2.5:7b is pulled."
    echo "   Run: ollama run qwen2.5:7b"
else
    echo "✅ .env file already exists."
fi

echo "--------------------------------------------------"
echo "✅ Professional Runtime Setup complete!"
echo "🚀 To run the agent, use:"
echo "   source venv/bin/activate"
echo "   python main.py 'Your task description here'"
echo "--------------------------------------------------"
