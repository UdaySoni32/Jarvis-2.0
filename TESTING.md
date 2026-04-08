# JARVIS 2.0 Testing Guide

How to test and verify JARVIS 2.0 functionality.

## Quick System Check

Verify your system is ready before testing:

```bash
cd ~/jarvis-2.0
./quick_test.sh
```

Expected output:
```
✅ Directory structure looks good
✅ FastAPI and WebSocket dependencies installed
✅ Web dependencies installed
🚀 READY TO TEST!
```

## Full System Test (5 minutes)

### Terminal 1: Start API Server
```bash
cd ~/jarvis-2.0
source venv/bin/activate
python3 -m src.api.main
```

Expected output:
```
🚀 Starting JARVIS 2.0 API Server...
✅ Database initialized successfully
✅ Plugin registry initialized
✅ LLM manager initialized
🎉 JARVIS 2.0 API Server started successfully
INFO: Uvicorn running on http://127.0.0.1:8000
```

### Terminal 2: Start Web Interface
```bash
cd ~/jarvis-2.0/web
npm run dev
```

Expected output:
```
▲ Next.js 14.x.x
✓ Ready in X.Xs
- Local: http://localhost:3000
```

### Browser Testing

1. **Open**: http://localhost:3000
2. **Register**: Create new account
3. **Login**: Use your credentials
4. **Chat**: Type message and watch **live streaming response**
5. **Check Status**: "WebSocket Connected" in header
6. **Test Fallback**: Click "WebSocket" button → Switch to "HTTP" → Send message
7. **Settings**: Check system status page

## Component Testing

### Test API Health
```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "database": "connected"
}
```

### Test API Info
```bash
curl http://localhost:8000/
```

### Test WebSocket (Browser Console)
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/chat?token=YOUR_TOKEN');
ws.onopen = () => console.log('Connected');
ws.onmessage = (e) => console.log('Message:', JSON.parse(e.data));
```

## Individual Interface Testing

### CLI Interface
```bash
python3 main.py
# Type: hello
# Type: help
# Type: status
# Type: exit
```

### Voice Interface
```bash
python3 main.py --voice
# Say "jarvis" (wake word)
# Ask: "What time is it?"
# Speak follow-up questions
```

## Success Criteria

### ✅ API Server
- Starts without errors
- Health check responds
- Shows plugin count
- Handles connections

### ✅ Web Interface
- Loads login page
- Registration works
- Authentication works
- Chat page loads

### ✅ WebSocket
- Green "Connected" status
- Messages show **live streaming** (character by character)
- Connection status updates
- Auto-reconnects on restart

### ✅ Fallback System
- WebSocket mode shows green status
- HTTP mode works (no streaming)
- Toggle between modes works
- Both receive AI responses

### ✅ Chat Features
- Receive AI responses
- Messages persist
- Settings page works
- Logout works

## Troubleshooting

### Issue: "Connection refused"
**Solution**: Check API server is running on port 8000
```bash
curl http://localhost:8000/health
```

### Issue: "WebSocket disconnected"
**Solution**: Restart API server and refresh browser

### Issue: Web app won't load
**Solution**: Reinstall dependencies
```bash
cd web
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Issue: No streaming (characters appear all at once)
**Solution**: Try HTTP mode or refresh page

### Issue: Python ModuleNotFoundError
**Solution**: Reinstall dependencies
```bash
pip install -r requirements.txt
```

### Issue: Port 8000 or 3000 already in use
**Solution**: Kill existing process or change port in .env

## Advanced Testing

### Test Plugins
```bash
# From CLI
❯ plugins list
❯ github search python
❯ docker ps
```

### Test Multiple Clients
Open multiple browser tabs to http://localhost:3000 and chat - watch presence indicators work

### Test Connection Recovery
1. Start chatting
2. Stop API server
3. Watch web app show "Disconnected"
4. Restart API server
5. Watch web app auto-reconnect

## Performance Testing

### Response Time
- Measure time from message send to first response
- WebSocket should stream immediately
- HTTP should respond within 2 seconds

### Concurrent Connections
- Open 5+ browser tabs
- Send messages from each
- System should handle all without errors

### Memory Usage
- Monitor API server process
- Should stay under 500MB
- Check for memory leaks over 1 hour

## Documentation

- **API Docs**: http://localhost:8000/docs
- **Setup**: See SETUP.md
- **Features**: See FEATURES.md

## Support

If issues persist:
1. Check terminal logs for errors
2. Review browser console for JS errors
3. Check API docs at localhost:8000/docs
4. Verify all dependencies installed
5. Try restarting both servers
