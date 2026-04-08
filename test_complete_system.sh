#!/bin/bash
set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║        JARVIS 2.0 - COMPLETE SYSTEM TEST                 ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

PASS=0
FAIL=0

# Test function
test_item() {
    local name=$1
    local command=$2
    echo -n "Testing $name... "
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((PASS++))
    else
        echo -e "${RED}❌ FAIL${NC}"
        ((FAIL++))
    fi
}

echo -e "${BLUE}📋 SYSTEM REQUIREMENTS${NC}"
test_item "Python 3.10+" "python3 --version | grep -E '3\.(10|11|12)'"
test_item "Node.js 18+" "node --version | grep -E 'v(18|19|20)'"
test_item "npm" "npm --version > /dev/null"

echo ""
echo -e "${BLUE}📁 DIRECTORY STRUCTURE${NC}"
test_item "Source code exists" "test -d src"
test_item "Web app exists" "test -d web"
test_item "Config exists" "test -d config"
test_item "Tests exist" "test -d tests"

echo ""
echo -e "${BLUE}📦 PYTHON DEPENDENCIES${NC}"
source venv/bin/activate 2>/dev/null || true
test_item "FastAPI" "python3 -c 'import fastapi'"
test_item "SQLAlchemy" "python3 -c 'import sqlalchemy'"
test_item "LangChain" "python3 -c 'import langchain'"
test_item "WebSockets" "python3 -c 'import websockets'"
test_item "Rich" "python3 -c 'import rich'"

echo ""
echo -e "${BLUE}📚 NODE DEPENDENCIES${NC}"
test_item "React" "cd web && npm list react | grep react >/dev/null 2>&1"
test_item "Next.js" "cd web && npm list next | grep next >/dev/null 2>&1"
test_item "TypeScript" "cd web && npm list typescript | grep typescript >/dev/null 2>&1"

echo ""
echo -e "${BLUE}📝 DOCUMENTATION${NC}"
test_item "README.md" "test -f README.md"
test_item "SETUP.md" "test -f SETUP.md"
test_item "FEATURES.md" "test -f FEATURES.md"
test_item "TESTING.md" "test -f TESTING.md"

echo ""
echo -e "${BLUE}⚙️ CONFIGURATION${NC}"
test_item ".env.example exists" "test -f .env.example"
test_item ".gitignore exists" "test -f .gitignore"

echo ""
echo -e "${BLUE}📊 RESULTS${NC}"
echo "✅ Passed: $PASS"
echo "❌ Failed: $FAIL"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED! System is ready!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Start API: python3 -m src.api.main"
    echo "2. Start Web: cd web && npm run dev"
    echo "3. Open: http://localhost:3000"
    echo "4. API Docs: http://localhost:8000/docs"
    exit 0
else
    echo -e "${RED}⚠️  Some tests failed. Fix the issues and try again.${NC}"
    exit 1
fi
