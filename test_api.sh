#!/bin/bash

# JARVIS 2.0 API Test Script

echo "🚀 JARVIS 2.0 API Server Test"
echo "=============================="
echo

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Warning: Virtual environment not activated"
    echo "   Run: source venv/bin/activate"
    exit 1
fi

# Install requirements
echo "📦 Installing API dependencies..."
pip install -q fastapi uvicorn python-jose passlib python-multipart websockets psutil

echo

# Start API server in background
echo "🌐 Starting API server on http://localhost:8000..."
python3 -m src.api.main &
API_PID=$!

# Wait for server to start
sleep 3

# Test endpoints
echo
echo "🧪 Testing API endpoints..."
echo

# Health check
echo "1. Health check:"
curl -s http://localhost:8000/health | python3 -m json.tool
echo

echo "2. Root endpoint:"
curl -s http://localhost:8000/ | python3 -m json.tool
echo

echo "3. API docs available at:"
echo "   📖 http://localhost:8000/docs"
echo "   📖 http://localhost:8000/redoc"
echo

# Cleanup
echo "Press Enter to stop the API server..."
read
kill $API_PID 2>/dev/null

echo "✅ API server stopped"
