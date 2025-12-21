#!/bin/bash
# Oslo Commute Time Optimizer - Startup Script

echo "🚗 Starting Oslo Commute Time Optimizer..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "Creating .env from template..."
    cp .env.example .env
    echo "✅ Created .env - Please edit it with your API keys before running again."
    echo ""
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt

# Start the application
echo ""
echo "🚀 Starting server on http://localhost:8000"
echo "Press Ctrl+C to stop"
echo ""

cd backend
python main.py
