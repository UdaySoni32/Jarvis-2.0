# JARVIS 2.0 Setup Guide

Complete setup and installation instructions for JARVIS 2.0.

## Prerequisites

- Python 3.10+
- Node.js 16+ (for web interface)
- npm or yarn
- pip (Python package manager)

## Quick Start (5 minutes)

### 1. Clone and Navigate
```bash
cd ~/jarvis-2.0
```

### 2. One Command Setup + Run (Recommended)
```bash
./jarvis setup
# or jarvis setup if ~/.local/bin is on PATH
```
`jarvis setup` bootstraps dependencies, runs the configuration wizard, and starts the TUI.

### 3. Start JARVIS TUI
```bash
jarvis
# or ./jarvis
```

### 4. Bootstrap Dependencies Only (Optional)
```bash
./quick_setup.sh
```
This installs Python dependencies, web dependencies, creates `.env`, and installs the local `jarvis` command in `~/.local/bin`.

### 5. Manual Python Environment (Optional)
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 6. Setup Web Interface (Optional)
```bash
cd web
npm install
cd ..
```

### 7. Configure Environment
```bash
cp .env.example .env
# Edit .env with your API keys and settings
```

### 8. Test Installation
```bash
./quick_test.sh
```

## Running JARVIS 2.0

### Start API Server
```bash
source venv/bin/activate
python3 -m src.api.main
```
Server runs on: `http://localhost:8000`

### Start Web Interface (in another terminal)
```bash
cd web
npm run dev
```
Web app runs on: `http://localhost:3000`

### Access
- **Web Chat**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Using JARVIS 2.0

### Web Interface
1. Register or login at http://localhost:3000
2. Start chatting with real-time streaming responses
3. Toggle between WebSocket (streaming) and HTTP (standard) modes
4. Check settings for system status

### CLI Interface
```bash
jarvis
# or ./jarvis
# Commands: hello, help, status, exit
```

### Voice Interface
```bash
python3 main.py --voice
# Say "jarvis" to wake up, then ask questions
```

## First-time Voice Setup (Mic + Speaker)

JARVIS voice uses:
- **Microphone input** via `sounddevice` (default system input device)
- **Speaker output** via TTS engine (`pyttsx3` by default)

On Linux, this access is provided through your local audio stack (ALSA/PulseAudio/PipeWire) and `/dev/snd` device permissions.

### 1. Install OS audio dependencies (Ubuntu/Debian)
```bash
# quick_setup.sh installs these automatically, but you can run manually too
sudo apt install -y ffmpeg libportaudio2 portaudio19-dev libasound2-dev espeak-ng
```

### 2. Enable voice in `.env`
```bash
VOICE_ENABLED=true
ENABLE_VOICE=true
STT_ENGINE=whisper
TTS_ENGINE=pyttsx3
```

### 3. Verify microphone devices are visible
```bash
source venv/bin/activate
python3 - <<'PY'
import sounddevice as sd
print("Default input/output device indexes:", sd.default.device)
print(sd.query_devices())
PY
```

### 4. Verify speaker playback (TTS)
```bash
source venv/bin/activate
python3 - <<'PY'
import pyttsx3
engine = pyttsx3.init()
engine.say("Jarvis voice setup successful")
engine.runAndWait()
PY
```

### 5. If mic access fails with permission errors
```bash
sudo usermod -aG audio $USER
```
Then log out and log back in (or reboot) so the new group membership takes effect.

## Troubleshooting

### Python Dependencies Missing
```bash
pip install -r requirements.txt
```

### Web App Won't Start
```bash
cd web && npm install
npm run dev
```

### WebSocket Connection Issues
- Ensure API server is running on port 8000
- Check browser console for errors
- Try HTTP mode if WebSocket fails
- Refresh page and retry

### Voice Mic/Speaker Not Working
- Check your default input/output device in system sound settings
- Re-run the device check in "First-time Voice Setup (Mic + Speaker)"
- Ensure `VOICE_ENABLED=true` and `ENABLE_VOICE=true` in `.env`
- If speaker audio is silent, test `pyttsx3` directly (step 4 above)

### Port Already in Use
```bash
# Find and kill process on port 8000
lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9

# Or use different port in .env
```

## Configuration

Edit `.env` file to configure:
- `LLM_PROVIDER`: openai, claude, gemini, or ollama
- `LLM_MODEL`: Model name for selected provider
- `DATABASE_URL`: Database connection string
- `API_PORT`: Server port (default 8000)
- `WEB_PORT`: Web app port (default 3000)

## Features

### Multi-Interface
- **Web**: Beautiful UI with real-time chat
- **CLI**: Rich terminal interface
- **Voice**: Hands-free interaction
- **API**: RESTful endpoints

### Real-time
- WebSocket streaming responses
- Typing indicators
- Presence system
- Live notifications

### Multi-Model AI
- OpenAI (GPT-4, GPT-3.5)
- Anthropic Claude
- Google Gemini
- Ollama (local)

### Plugins
- GitHub integration
- Docker management
- Database queries
- Calendar & email
- API testing
- Screen capture
- Clipboard manager

## Development

### Run Tests
```bash
source venv/bin/activate
pytest tests/ -v
```

### Build Web App
```bash
cd web
npm run build
npm start
```

## Database

JARVIS 2.0 uses SQLite by default. To use PostgreSQL:

```bash
# Install PostgreSQL client
pip install psycopg2-binary

# Update .env
DATABASE_URL=postgresql://user:password@localhost/jarvis
```

## Deployment

For production deployment:
1. Set `ENVIRONMENT=production` in .env
2. Use strong `SECRET_KEY`
3. Configure CORS origins
4. Setup SSL/TLS certificates
5. Use production ASGI server (Gunicorn, Hypercorn)

See deployment guides in the web interface settings.

## Support

For issues and questions:
- Check logs in `logs/` directory
- Review error messages in browser console
- Check API documentation at http://localhost:8000/docs
- Test individual components separately

## License

MIT License - See LICENSE file for details
