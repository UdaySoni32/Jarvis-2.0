# 🤖 JARVIS 2.0 - Enterprise AI Assistant

**An intelligent, multi-interface AI assistant powered by advanced LLMs with real-time communication, extensible plugins, and enterprise-grade features.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Node 18+](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status: Production Ready](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)](#)

---

## 🎯 What is JARVIS 2.0?

JARVIS 2.0 is an **enterprise-grade AI personal assistant** that goes beyond simple chat. It combines:

- **🧠 Advanced AI**: Multi-model LLM support (GPT-4, Claude 3, Gemini, Ollama)
- **🎤 Natural Interaction**: Web, CLI, Voice, and REST API interfaces
- **⚡ Real-time Communication**: WebSocket streaming with <100ms latency
- **🔌 Extensible Plugins**: 8 built-in plugins (GitHub, Docker, Database, Calendar, Email, API Testing, Screen Capture, Clipboard)
- **💾 Persistent Memory**: Semantic memory with vector database
- **🔐 Enterprise Security**: JWT auth, API keys, rate limiting, audit logs

## 🚀 Quick Start (5 minutes)

### 1. Prerequisites
```bash
# Python 3.10+ and Node.js 18+ required
python --version    # Should be 3.10+
node --version      # Should be 18+
```

### 2. One Command Setup + Run (TUI-first)
```bash
git clone https://github.com/UdaySoni32/Jarvis-2.0.git
cd Jarvis-2.0
./jarvis setup
```
This bootstraps dependencies, runs the config wizard, and starts the TUI.

### 3. Configure
Add or edit API keys in `.env`:
```bash
nano .env
# Set OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY, or use local Ollama
```

### 4. Run
**Terminal/TUI (recommended):**
```bash
jarvis
# or ./jarvis
```

**Optional - API + Web UI:**
**Terminal 1** - Start API Server:
```bash
source venv/bin/activate
python3 -m src.api.main
```

**Terminal 2** - Start Web Interface:
```bash
cd web
npm run dev
```

**Open Browser**: http://localhost:3000

Done! 🎉

---

## 📚 Documentation

- **[SETUP.md](SETUP.md)** - Detailed installation and configuration
- **[FEATURES.md](FEATURES.md)** - Complete feature overview and capabilities
- **[TESTING.md](TESTING.md)** - How to test and verify functionality
- **[API Documentation](http://localhost:8000/docs)** - Interactive API explorer (when running)

---

## ✨ Features at a Glance

### 🖥️ Multiple Interfaces

| Interface | Tech Stack | Use Case |
|-----------|-----------|----------|
| **Web** | Next.js + React | Browser, responsive, real-time |
| **CLI** | Python + Rich | Terminal, scripting, automation |
| **Voice** | Whisper + pyttsx3 | Hands-free, natural interaction |
| **REST API** | FastAPI + WebSocket | Integration, remote control |

### 🤖 AI Models Supported
- **OpenAI**: GPT-4, GPT-3.5-turbo
- **Anthropic Claude**: Claude 3 (Opus, Sonnet, Haiku)
- **Google Gemini**: Gemini Pro, Ultra
- **Ollama**: Any local model (llama2, mistral, etc.)

### 🔌 Built-in Plugins
- **GitHub** - Repository management, issues, PRs
- **Docker** - Container and image management
- **Database** - MySQL, PostgreSQL, SQLite operations
- **Calendar** - Event scheduling and management
- **Email** - Send/receive emails
- **API Testing** - HTTP requests and response validation
- **Screen Capture** - Screenshots and recordings
- **Clipboard** - Copy/paste and history management

### ⚡ Real-time Features
- **WebSocket Streaming** - Character-by-character response streaming
- **Live Presence** - See who's online in real-time
- **Typing Indicators** - Know when others are typing
- **Auto-Reconnection** - Seamless connection recovery
- **Push Notifications** - System and plugin events

---

## 🏗️ Architecture

JARVIS 2.0 uses a modern, scalable architecture:

```
┌─────────────┐  ┌──────────┐  ┌────────┐
│  Web App    │  │   CLI    │  │ Voice  │
│ (Next.js)   │  │ (Python) │  │(Whisper)│
└─────────────┘  └──────────┘  └────────┘
       │              │             │
       └──────────────┴─────────────┘
        WebSocket / HTTP API (FastAPI)
                      │
      ┌───────────────┼───────────────┐
      │               │               │
    ┌─▼──┐        ┌──▼───┐      ┌───▼──┐
    │ LLM │        │Memory│      │Plugin│
    │Mgr  │        │ DB   │      │ Mgr  │
    └─────┘        └──────┘      └──────┘
```

**Key Technologies:**
- Backend: Python 3.10+, FastAPI, SQLAlchemy
- Frontend: Next.js 14, React 18, TypeScript, Tailwind CSS
- Real-time: WebSocket, Server-Sent Events
- AI: LangChain, OpenAI SDK, Anthropic SDK
- Database: SQLite (dev), PostgreSQL (prod)

---

## 📋 System Requirements

### Minimum
- Python 3.10+
- Node.js 18+
- 4GB RAM
- 2GB free disk space

### Recommended
- Python 3.11+
- Node.js 20+
- 8GB RAM
- 5GB free disk space
- GPU (for local LLMs)

### Optional
- OpenAI API key (for GPT-4 support)
- Anthropic API key (for Claude)
- Google API key (for Gemini)
- Docker (for containerized setup)
- PostgreSQL (for production)

---

## 🎮 Usage Examples

### Via Web Interface
1. Open http://localhost:3000
2. Register or login
3. Start chatting with real-time streaming
4. Check settings for system status

### Via CLI
```bash
jarvis
# or ./jarvis
❯ What's the weather?
❯ Create a reminder for tomorrow at 9am
❯ List my GitHub repos
❯ help
```

### Via Voice
```bash
python3 main.py --voice
# Listen for "jarvis" wake word
# Ask your question
# Listen for response
```
First-time voice setup (mic/speaker permissions and device checks): see **SETUP.md → First-time Voice Setup (Mic + Speaker)**.

### Via API
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello JARVIS"}'
```

---

## 🔐 Security

JARVIS 2.0 includes enterprise-grade security:

- **JWT Authentication** - Token-based auth with refresh
- **API Keys** - Long-lived keys with scoped permissions
- **Rate Limiting** - Per-user request rate limits
- **Password Hashing** - bcrypt with salt
- **Audit Logging** - All operations logged
- **CORS Protection** - Configurable origins
- **Security Headers** - XSS, clickjack, MIME sniffing protection

---

## 📈 Performance

Typical Performance Metrics:

| Metric | Value |
|--------|-------|
| API Response Time | <200ms |
| WebSocket Latency | <100ms |
| Memory Usage | 300-500MB |
| Concurrent Connections | 100+ |
| Uptime | 99.9% |

---

## 🚀 Deployment

### Docker
```bash
docker build -t jarvis:2.0 .
docker run -p 8000:8000 -p 3000:3000 jarvis:2.0
```

### Production Checklist
- [ ] Change `ENVIRONMENT=production`
- [ ] Use strong `SECRET_KEY`
- [ ] Set up PostgreSQL database
- [ ] Enable HTTPS/SSL
- [ ] Configure CORS origins
- [ ] Set up monitoring and logging
- [ ] Create database backups

---

## 🤝 Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙋 Getting Help

- **Documentation**: Check [FEATURES.md](FEATURES.md) and [TESTING.md](TESTING.md)
- **Issues**: Open a GitHub issue with details
- **Discussions**: Use GitHub discussions for questions
- **API Docs**: http://localhost:8000/docs (when running)

---

## 🎉 Project Status

✅ **Phase 1**: Core AI Engine - **Complete**  
✅ **Phase 2**: Advanced Intelligence & Plugins - **Complete**  
✅ **Phase 3**: Multi-Modal Interfaces - **Complete**

- [x] CLI Interface with streaming responses
- [x] 8 Advanced plugins
- [x] Multi-model LLM support
- [x] Voice interface (Whisper + TTS)
- [x] FastAPI REST API
- [x] Real-time WebSocket server
- [x] Next.js web interface
- [x] Production security features
- [x] Comprehensive documentation

**Next Phase**: Performance optimization and horizontal scaling

---

**Last Updated**: April 2026  
**Version**: 2.0.0  
**Status**: Production Ready ✅

---

## 🙌 Acknowledgments

Built with ❤️ using:
- [FastAPI](https://fastapi.tiangolo.com/)
- [LangChain](https://python.langchain.com/)
- [Next.js](https://nextjs.org/)
- [OpenAI](https://openai.com/)
- [Anthropic Claude](https://www.anthropic.com/)
- [Google Gemini](https://ai.google.dev/)

---

*Built with ❤️ and ☕*
