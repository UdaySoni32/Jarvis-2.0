#!/bin/bash

echo "🧪 JARVIS 2.0 - QUICK SYSTEM TEST"
echo "=================================="
echo

# Check current directory
if [[ ! -f "main.py" ]]; then
    echo "❌ Error: Run this from the jarvis-2.0 directory"
    echo "   Command: cd ~/jarvis-2.0 && ./quick_test.sh"
    exit 1
fi

# Check virtual environment
if [[ ! -d "venv" ]]; then
    echo "❌ Error: Virtual environment not found"
    echo "   Run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

echo "✅ Directory structure looks good"

# Check Python dependencies
echo "🔍 Checking Python dependencies..."
source venv/bin/activate

# Check key packages
python3 -c "import fastapi, uvicorn, websockets, rich" 2>/dev/null
if [[ $? -eq 0 ]]; then
    echo "✅ FastAPI and WebSocket dependencies installed"
else
    echo "❌ Missing Python dependencies"
    echo "   Run: pip install -r requirements.txt"
    exit 1
fi

echo
echo "🚀 READY TO TEST! Run these commands:"
echo
echo "Terminal 1 (TUI):"
echo "  jarvis"
echo
echo "Terminal 2 (optional API Server):"
echo "  source venv/bin/activate"
echo "  python3 -m src.api.main"
echo
echo "🎯 Key test: Ask JARVIS 'how is the cpu usage like'"
echo
