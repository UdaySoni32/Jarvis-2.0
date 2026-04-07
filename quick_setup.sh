#!/bin/bash
set -e

echo "🚀 JARVIS 2.0 Quick Setup"
echo "=========================="
echo ""

# Get script directory and cd to it
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: Cannot find main.py in the project directory"
    echo "   Please make sure you're in the Jarvis-2.0 directory"
    exit 1
fi

# Install system dependencies
echo "📥 Installing system dependencies..."
sudo apt update
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    scrot \
    tesseract-ocr \
    tesseract-ocr-eng \
    xclip \
    xsel \
    curl \
    git

echo ""
echo "🐍 Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo ""
echo "📚 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "🧪 Running tests to verify installation..."
python -m pytest tests/ -v --tb=short || {
    echo "⚠️  Some tests failed, but this might be expected if optional dependencies are missing"
    echo "   You can still proceed with setup"
}

echo ""
echo "✅ Setup complete!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Next Steps:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1️⃣  Run the setup wizard to configure JARVIS:"
echo "   source venv/bin/activate"
echo "   python -m src.setup_wizard"
echo ""
echo "2️⃣  Or manually create config/settings.json with your API key"
echo ""
echo "3️⃣  Start JARVIS:"
echo "   python main.py"
echo ""
echo "📖 For detailed setup instructions, see SETUP_GUIDE.md"
echo ""
echo "🎉 Welcome to JARVIS 2.0!"
echo ""
