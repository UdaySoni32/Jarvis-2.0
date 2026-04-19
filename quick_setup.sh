#!/bin/bash
set -euo pipefail

echo "🚀 JARVIS 2.0 Quick Setup"
echo "=========================="
echo

RUN_TESTS="${1:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ ! -f "main.py" ]]; then
    echo "❌ Error: Cannot find main.py in the project directory"
    echo "   Please run this script from the Jarvis-2.0 directory"
    exit 1
fi

if command -v apt >/dev/null 2>&1; then
    if command -v sudo >/dev/null 2>&1; then
        echo "📥 Installing system dependencies (may prompt for sudo password)..."
        sudo apt update
        sudo apt install -y \
            python3 \
            python3-pip \
            python3-venv \
            ffmpeg \
            libportaudio2 \
            portaudio19-dev \
            libasound2-dev \
            espeak-ng \
            scrot \
            tesseract-ocr \
            tesseract-ocr-eng \
            xclip \
            xsel \
            curl \
            git
    else
        echo "⚠️  sudo not found; skipping apt dependencies. Install manually if needed."
    fi
fi

echo
echo "🐍 Setting up Python virtual environment..."
if [[ ! -d "venv" ]]; then
    python3 -m venv venv
fi
source venv/bin/activate

echo
echo "📚 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

if [[ -f "web/package.json" ]]; then
    echo
    if command -v npm >/dev/null 2>&1; then
        echo "🌐 Installing web dependencies..."
        (cd web && npm install --silent)
    else
        echo "⚠️  npm not found; skipping web dependency install."
        echo "   Install Node.js 18+ and run: cd web && npm install"
    fi
fi

if [[ ! -f ".env" && -f ".env.example" ]]; then
    echo
    echo "🛠️  Creating .env from .env.example..."
    cp .env.example .env
fi

if [[ -f ".env" ]]; then
    sed -i 's|^DATABASE_URL=.*|DATABASE_URL=sqlite:///jarvis.db|' .env
fi

if [[ "$RUN_TESTS" == "--with-tests" ]]; then
    echo
    echo "🧪 Running quick verification..."
    ./quick_test.sh
fi

echo
echo "🔗 Installing local 'jarvis' command..."
install_local_command() {
    local local_bin="${HOME}/.local/bin"
    mkdir -p "$local_bin"
    chmod +x "$SCRIPT_DIR/jarvis"
    ln -sf "$SCRIPT_DIR/jarvis" "$local_bin/jarvis"
}

if install_local_command; then
    echo "✅ Installed: ${HOME}/.local/bin/jarvis"
    if [[ ":$PATH:" != *":${HOME}/.local/bin:"* ]]; then
        echo "⚠️  ${HOME}/.local/bin is not on PATH."
        echo "   Add this to your shell profile:"
        echo "   export PATH=\"\$HOME/.local/bin:\$PATH\""
    fi
else
    echo "⚠️  Could not install local jarvis command. You can still use: ./jarvis"
fi

echo
echo "✅ Setup complete!"
echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Next Steps"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo
echo "1) Add at least one model API key in .env (or use Ollama)"
echo "2) Start JARVIS TUI: jarvis"
echo "   (or: ./jarvis if ~/.local/bin is not on PATH yet)"
echo "3) Re-run setup/config wizard anytime: jarvis configure"
echo "4) Optional API server: source venv/bin/activate && python3 -m src.api.main"
echo "5) Optional Web UI: cd web && npm run dev"
echo "6) For voice mode, see SETUP.md -> 'First-time Voice Setup (Mic + Speaker)'"
echo
echo "📖 See SETUP.md and TESTING.md for full details."
echo "🎉 Welcome to JARVIS 2.0!"
