# 🧪 JARVIS 2.0 Complete Testing Guide

**Test your fully functional AI assistant system!**

---

## 🎯 What You're Testing

✅ **API Server** - REST API with authentication, chat, streaming  
✅ **Web Interface** - Next.js React app with real-time chat  
✅ **Voice Interface** - Wake word, STT, TTS, conversation mode  
✅ **CLI Interface** - Terminal chat with full plugin system  

---

## 🚀 Quick Start (5 minutes)

### 1. Start API Server

```bash
cd ~/jarvis-2.0

# Activate environment
source venv/bin/activate

# Start API server (port 8000)
python3 -m src.api.main
```

**Expected Output:**
```
🚀 Starting JARVIS API Server...
Environment: development
Creating database tables...
✅ Database tables created
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 2. Start Web Interface

**Open new terminal:**

```bash
cd ~/jarvis-2.0/web

# Install dependencies (first time only)
npm install

# Start web app (port 3000)
npm run dev
```

**Expected Output:**
```
- ready started server on 0.0.0.0:3000, url: http://localhost:3000
- event compiled client and server successfully
```

### 3. Test Complete System

**Open browser:** http://localhost:3000

1. **Register Account** - Create your user
2. **Login** - Authenticate  
3. **Chat** - Send messages to JARVIS
4. **Stream** - Toggle streaming responses
5. **Settings** - View system metrics
6. **Models** - Switch AI models

---

## 📋 Detailed Testing Checklist

### ✅ API Server Tests

**Terminal 1: API Server**

```bash
# Health check
curl http://localhost:8000/health

# Expected: {"status":"healthy","version":"2.0.0"}

# Interactive docs
open http://localhost:8000/docs
```

**Test Authentication:**

```bash
# Register user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com", 
    "password": "test123",
    "full_name": "Test User"
  }'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "test123"
  }'

# Save the access_token from response
TOKEN="your-token-here"

# Test protected endpoint
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/system/status
```

**Test Chat API:**

```bash
# Send message
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello JARVIS! How are you?"
  }'

# Expected: AI response with conversation_id
```

### ✅ Web Interface Tests

**Browser: http://localhost:3000**

1. **Registration Flow:**
   - Click "Sign up" 
   - Fill form (username, email, password)
   - Submit → Should auto-login and redirect to chat

2. **Authentication:**
   - Try login with wrong password → Should show error
   - Login with correct credentials → Should redirect to chat
   - Logout → Should redirect to login page

3. **Chat Interface:**
   - Send message → Should get AI response
   - Toggle streaming → Test both modes
   - Long message → Should auto-resize textarea
   - Enter key → Send message
   - Shift+Enter → New line
   - Clear chat → Should clear messages

4. **Settings Page:**
   - Click settings icon
   - View system metrics (CPU, Memory, Disk)
   - Check model information
   - Try switching models
   - View account information

5. **Responsive Design:**
   - Resize browser window
   - Test on mobile device
   - All elements should adapt properly

### ✅ Voice Interface Tests

**Terminal 2: Voice Chat**

```bash
cd ~/jarvis-2.0
source venv/bin/activate

# Test voice components
python3 -c "
from src.voice.voice_assistant import create_voice_assistant
va = create_voice_assistant()
print('✅ Voice assistant created successfully')
print('Available TTS engines:', va.tts_engine.__class__.__name__)
print('Available STT engines:', va.stt_engine.__class__.__name__)
"

# Start voice mode (if microphone available)
python3 main.py --voice

# Or test specific components
python3 -c "
from src.voice.tts_engine import create_tts_engine
tts = create_tts_engine('pyttsx3')
tts.speak('Hello! JARVIS voice system is working correctly.')
print('✅ Text-to-speech test complete')
"
```

### ✅ CLI Interface Tests

**Terminal 3: CLI Chat**

```bash
cd ~/jarvis-2.0
source venv/bin/activate

# Start CLI
python3 main.py

# Try these commands:
❯ hello
❯ help
❯ status
❯ github search "machine learning"
❯ weather
❯ calculate 2 + 2
❯ exit
```

---

## 🔧 System Integration Tests

### Test Full Workflow

1. **Start all services:**
   - API Server (Terminal 1)
   - Web App (Terminal 2) 
   - CLI (Terminal 3)

2. **Cross-platform test:**
   - Send message via Web Interface
   - Check conversation in API docs
   - Use CLI to continue same conversation
   - Verify message history persists

3. **Model switching:**
   - Switch model in Web settings
   - Send message via Web
   - Send message via CLI
   - Both should use new model

4. **Authentication test:**
   - Login via Web Interface
   - Use API directly with token
   - Verify user data consistency

---

## 📊 Performance Tests

### Load Testing

```bash
# Test API performance
curl -w "time_total: %{time_total}s\nsize_download: %{size_download} bytes\n" \
  -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/system/status

# Expected: < 200ms response time
```

### Memory Usage

```bash
# Monitor processes
top -p $(pgrep -f "python.*main.py\|node.*next")

# Expected:
# - API server: < 200MB RAM
# - Web app: < 100MB RAM
# - CLI: < 50MB RAM
```

---

## 🐛 Common Issues & Solutions

### API Server Won't Start

**Error:** `Port 8000 already in use`
```bash
# Find and kill process using port
sudo netstat -tulpn | grep :8000
# Kill specific process
kill -9 <PID>
```

**Error:** `ModuleNotFoundError`
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### Web App Issues

**Error:** `EADDRINUSE: Port 3000 in use`
```bash
# Find and kill process
sudo netstat -tulpn | grep :3000
kill -9 <PID>
# Or use different port
npm run dev -- --port 3001
```

**Error:** `Failed to fetch`
```bash
# Check API server is running
curl http://localhost:8000/health
# Update API URL in web/.env.local
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > web/.env.local
```

### Authentication Issues

**Error:** `401 Unauthorized`
```bash
# Clear browser localStorage
# In browser console:
localStorage.clear()
location.reload()
```

### Database Issues

**Error:** `Database locked`
```bash
# Stop all JARVIS processes
pkill -f "python.*main.py"
# Restart API server
python3 -m src.api.main
```

---

## ✅ Success Criteria

After testing, you should have:

**✅ API Server:**
- Health endpoint responding
- User registration/login working
- Chat completions working
- System status displaying metrics
- Token authentication functional

**✅ Web Interface:**
- Beautiful responsive UI
- Registration and login flow
- Real-time chat with streaming
- Settings page with system info
- Model switching working

**✅ CLI Interface:**
- Interactive REPL working
- Plugin system functional
- Memory system active
- Voice mode accessible

**✅ Integration:**
- All components communicate properly
- Data persistence across interfaces
- Model switching affects all interfaces
- Authentication tokens work everywhere

---

## 🚀 Next Steps After Testing

Once testing is complete, you can:

1. **Deploy to production**
2. **Add more AI models**
3. **Create custom plugins**
4. **Build mobile app**
5. **Add more voice features**
6. **Integrate with external services**

---

**Your JARVIS 2.0 system is ready for testing! 🎉**

---

**Testing Guide Version**: 2.0.0  
**Last Updated**: April 8, 2026