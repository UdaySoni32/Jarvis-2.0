# 🚀 JARVIS 2.0 - Quick Start Guide

**Welcome to JARVIS 2.0 Development!**

---

## 📁 Project Location
```bash
/home/uday/jarvis-2.0
```

---

## 📋 Key Files

### Planning & Documentation
- **PROJECT_PLAN.md** - Complete development roadmap (200+ tasks across 8 phases)
- **STATUS.md** - Current progress and next steps
- **README.md** - Project overview and features
- **CONTRIBUTING.md** - How to contribute
- **QUICKSTART.md** - This file!

### Configuration
- **.env.example** - Environment variables template
- **requirements.txt** - Python dependencies
- **requirements-dev.txt** - Development tools
- **docker-compose.yml** - Infrastructure (postgres, redis, chromadb, ollama)
- **Makefile** - Common commands

### Source Code
```
src/
├── core/      - AI engine, LLM integration, memory
├── plugins/   - Tool plugins (system, files, web, etc.)
├── agents/    - AI agents (planning, research, code, task)
├── api/       - REST API server (FastAPI)
├── cli/       - Command-line interface
└── gui/       - Desktop GUI (Tauri + React)
```

---

## ⚡ Quick Commands

### First Time Setup
```bash
cd /home/uday/jarvis-2.0

# Create virtual environment
make setup

# Activate virtual environment
source venv/bin/activate

# Install dependencies
make install

# Copy and configure environment
cp .env.example .env
nano .env  # Add your API keys
```

### Development
```bash
# Run CLI (when implemented)
make run

# Run API server
make run-api

# Run in development mode
make dev
```

### Code Quality
```bash
# Format code
make format

# Run linters
make lint

# Type checking
make type-check

# Run tests
make test

# Tests with coverage
make test-cov
```

### Docker Infrastructure
```bash
# Start all services (postgres, redis, chromadb, ollama)
make docker-run

# Stop services
make docker-stop
```

### Utilities
```bash
# Clean build artifacts
make clean

# Generate documentation
make docs

# Show all available commands
make help
```

---

## 🎯 Development Phases

### **Phase 0: Foundation** (Current - Week 1) ✅ 80% Complete
- ✅ Project structure
- ✅ Planning documents
- ✅ Configuration files
- ⏳ Environment setup
- ⏳ Git initialization

### **Phase 1: Core AI Engine** (Weeks 2-4) - NEXT
- [ ] CLI interface with REPL
- [ ] LLM integration (OpenAI + Ollama)
- [ ] Function calling system
- [ ] Memory & conversation history
- [ ] Core plugins (8 basic tools)

### **Phase 2: Advanced Intelligence** (Weeks 5-8)
- [ ] Vector database & semantic memory
- [ ] Multi-agent system
- [ ] Task automation engine
- [ ] Learning system

### **Phase 3: Multi-Modal** (Weeks 9-12)
- [ ] Voice interface (Whisper + TTS)
- [ ] Desktop GUI (Tauri)
- [ ] Web interface (Next.js)
- [ ] API server (FastAPI)

### **Phase 4-8**: Plugin ecosystem, mobile, security, deployment

---

## 🔑 Required API Keys

### Essential (for basic features)
- **OpenAI API Key** - For GPT-4 (get from: https://platform.openai.com/)
- OR use **Ollama** locally (free, no API key needed)

### Optional (for advanced features)
- **Anthropic Claude** - Alternative LLM
- **ElevenLabs** - Better text-to-speech
- **OpenWeatherMap** - Weather data
- **Google APIs** - Calendar, Gmail integration

Add these to `.env` file after copying from `.env.example`

---

## 📚 Learning Resources

### Project Files
1. Read **PROJECT_PLAN.md** - Understand the full vision
2. Check **STATUS.md** - See current progress
3. Read **README.md** - Project overview
4. Review **CONTRIBUTING.md** - Development guidelines

### External Resources
- [LangChain Documentation](https://python.langchain.com/)
- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)

---

## 🛠️ Next Steps

### To Start Development (Phase 1):

1. **Set up environment**
   ```bash
   cd /home/uday/jarvis-2.0
   make setup
   source venv/bin/activate
   make install
   ```

2. **Configure API keys**
   ```bash
   cp .env.example .env
   # Edit .env and add OPENAI_API_KEY or set DEFAULT_LLM=ollama
   ```

3. **Start coding!**
   - Open PROJECT_PLAN.md
   - Go to "Phase 1: Core AI Engine"
   - Pick a task (start with 1.1 Basic CLI Interface)
   - Implement it in `src/`
   - Write tests in `tests/`

---

## 💡 Tips

### Development Workflow
1. Always work in a virtual environment
2. Run `make format` before committing
3. Write tests for new features
4. Update STATUS.md when completing tasks
5. Use conventional commits (feat:, fix:, docs:, etc.)

### Testing Locally
```bash
# Test with local LLM (free, no API key)
ollama pull llama3
# Set DEFAULT_LLM=ollama in .env

# Start infrastructure
make docker-run
```

### Getting Help
- Check PROJECT_PLAN.md for detailed tasks
- Check STATUS.md for current progress
- Read existing code in original jarvis/ folder
- Ask questions in discussions/issues

---

## �� You're Ready!

Everything is set up. Time to start building JARVIS 2.0!

**Current Status**: Foundation complete ✅  
**Next Task**: Begin Phase 1 - Core AI Engine  
**First File to Create**: `src/cli/main.py` (CLI entry point)

Happy coding! 🚀

---

**Quick Navigation**:
- [Full Plan](PROJECT_PLAN.md) - All 200+ tasks
- [Current Status](STATUS.md) - Progress tracker
- [README](README.md) - Project overview
- [Contributing](CONTRIBUTING.md) - Guidelines
