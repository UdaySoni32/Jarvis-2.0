#!/bin/bash

echo "🌐 Creating JARVIS 2.0 Web Interface"
echo "===================================="
echo

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 18+ first."
    echo "   Visit: https://nodejs.org/"
    exit 1
fi

echo "✅ Node.js $(node --version) detected"
echo

# Create web directory
mkdir -p web
cd web

# Initialize Next.js app with TypeScript
echo "📦 Creating Next.js application..."
npx --yes create-next-app@latest . \
  --typescript \
  --tailwind \
  --app \
  --no-src-dir \
  --import-alias "@/*" \
  --use-npm

echo
echo "✅ Next.js app created!"
echo
echo "📦 Installing additional dependencies..."
npm install axios socket.io-client react-markdown zustand lucide-react

echo
echo "✨ Web interface setup complete!"
echo
echo "Next steps:"
echo "  cd web"
echo "  npm run dev"
echo
