# 🧪 Testing JARVIS 2.0 on a Fresh Ubuntu Machine

This guide walks you through setting up and testing JARVIS 2.0 on a new/clean Ubuntu machine.

## Prerequisites

**System Requirements:**
- Ubuntu 20.04+ or Ubuntu 22.04 (recommended)
- Python 3.10+
- Node.js 18+
- 4GB RAM minimum (8GB recommended)
- Internet connection

**Check before starting:**
```bash
python3 --version  # Should be 3.10+
node --version     # Should be 18+
```

## Step-by-Step Setup

### Step 1: Clone the Repository

```bash
cd ~
git clone https://github.com/UdaySoni32/Jarvis-2.0.git
cd Jarvis-2.0
```

### Step 2: Run Quick Setup

```bash
bash quick_setup.sh
```

This will:
- Install system dependencies
- Create Python virtual environment
- Install Python dependencies
- Install Node.js dependencies
- Set up configuration

### Step 3: Configure Environment

```bash
# Copy example configuration
cp .env.example .env

# Edit with your API keys
nano .env
```

**Minimum Configuration** (at least one LLM provider):

```bash
# Option 1: OpenAI
OPENAI_API_KEY=sk-your-key-here
DEFAULT_LLM=openai

# Option 2: Ollama (local, free)
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_LLM=ollama
```

### Step 4: Run System Verification

```bash
bash quick_test.sh
```

## Full System Test

### Terminal 1: Start API Server

```bash
source venv/bin/activate
python3 -m src.api.main
```

Verify with:
```bash
curl http://localhost:8000/health
```

### Terminal 2: Start Web Interface

```bash
cd web
npm run dev
```

Then open: http://localhost:3000

## Web Interface Testing Checklist

1. **Registration**
   - Register with test@example.com / test123456
   - Should redirect to login

2. **Login**
   - Login with test credentials
   - Should show chat page

3. **Chat**
   - Send "Hello JARVIS"
   - Watch for live streaming response
   - Check "WebSocket Connected" indicator

4. **WebSocket Mode**
   - Click mode button
   - Switch to HTTP
   - Send message (should work without streaming)
   - Switch back to WebSocket

5. **Settings**
   - Check system status
   - Verify all services show "Connected"

## CLI Interface Testing

```bash
python3 main.py
```

Commands to test:
- hello
- what's the weather?
- help
- status
- exit

## API Testing

**Health check:**
```bash
curl http://localhost:8000/health
```

**View docs:**
- Open http://localhost:8000/docs

## Success Criteria

✅ **System is working if:**
1. Web interface authenticates
2. Chat responds with streaming
3. WebSocket shows connected
4. API health check passes
5. CLI works
6. Settings page loads

Congratulations! 🎉 JARVIS 2.0 is fully functional!

---

**Version**: 2.0.0 | **Status**: ✅ Production Ready
