# 🚀 JARVIS 2.0 - Complete Setup Guide

This guide will walk you through setting up JARVIS 2.0 from scratch, step by step.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [First Run](#first-run)
5. [Usage Examples](#usage-examples)
6. [Troubleshooting](#troubleshooting)
7. [Advanced Configuration](#advanced-configuration)

---

## Prerequisites

### Required

- **Python 3.14+** (or 3.11+)
- **Git** (for cloning the repository)
- **Linux/macOS/WSL** (tested on Linux)

### Optional

- **OpenAI API Key** (for GPT-4 - get one at [platform.openai.com](https://platform.openai.com))
- **Ollama** (for local LLM - free alternative, install from [ollama.com](https://ollama.com))
- **OpenWeatherMap API Key** (for weather tool - free at [openweathermap.org](https://openweathermap.org/api))

### Check Python Version

```bash
python --version
# Should show Python 3.14.x or 3.11+

# If not available, try:
python3 --version
python3.14 --version
```

---

## Installation

### Step 1: Clone the Repository

```bash
# Navigate to where you want to install JARVIS
cd ~

# Clone the repository
git clone https://github.com/YOUR_USERNAME/jarvis-2.0.git

# Navigate into the directory
cd jarvis-2.0
```

### Step 2: Create Virtual Environment

**Important:** Always use a virtual environment to avoid dependency conflicts.

```bash
# Create virtual environment
python -m venv venv

# Or if python is Python 3.14:
python3 -m venv venv

# Activate it (Linux/macOS)
source venv/bin/activate

# Your prompt should now show (venv)
```

**Windows Users (WSL):**
```bash
# Same commands as above work in WSL
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
# Make sure venv is activated (you should see (venv) in prompt)

# Install core dependencies
pip install -r requirements.txt

# If you get errors, try upgrading pip first:
pip install --upgrade pip
pip install -r requirements.txt
```

**Dependencies installed:**
- `rich` - Beautiful terminal output
- `prompt-toolkit` - Interactive CLI
- `pydantic` - Configuration validation
- `python-dotenv` - Environment variables
- `httpx` - HTTP client
- `psutil` - System information

**Optional (for OpenAI):**
```bash
pip install openai tiktoken
```

### Step 4: Verify Installation

```bash
# Check if all imports work
python -c "import rich, prompt_toolkit, pydantic, httpx, psutil; print('✅ All dependencies installed!')"
```

---

## Configuration

### Option 1: Automatic Setup (Recommended)

The easiest way! Just run JARVIS and follow the setup wizard:

```bash
python -m src.cli
```

The setup wizard will:
1. Ask which LLM provider you want (OpenAI or Ollama)
2. Request API keys if needed
3. Test the connection
4. Create `.env` file automatically
5. Start JARVIS!

### Option 2: Manual Setup

If you prefer manual configuration:

```bash
# Copy example config
cp .env.example .env

# Edit with your favorite editor
nano .env
# or
vim .env
# or
code .env
```

**Minimal Configuration (using Ollama - no API key needed):**

```bash
# .env file
DEFAULT_LLM=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3

ENABLE_MEMORY=true
ENABLE_PLUGINS=true
DEBUG=false
LOG_LEVEL=INFO
```

**Full Configuration (using OpenAI GPT-4):**

```bash
# .env file
DEFAULT_LLM=openai
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4

# Optional: Weather API
OPENWEATHER_API_KEY=your_key_here

# Features
ENABLE_MEMORY=true
ENABLE_PLUGINS=true

# Debugging
DEBUG=false
LOG_LEVEL=INFO

# Memory settings
MAX_CONTEXT_MESSAGES=20
```

---

## First Run

### Using Ollama (Local, Free)

**Step 1: Install Ollama**

```bash
# Visit https://ollama.com and download
# Or on Linux:
curl -fsSL https://ollama.com/install.sh | sh

# Verify installation
ollama --version
```

**Step 2: Download a Model**

```bash
# Download llama3 (recommended - 4.7GB)
ollama pull llama3

# Or try smaller models:
ollama pull llama3.2    # Smaller, faster
ollama pull mistral     # Alternative
```

**Step 3: Start Ollama Server**

```bash
# Start Ollama (usually auto-starts)
ollama serve

# Test it
ollama run llama3 "Hello!"
```

**Step 4: Run JARVIS**

```bash
cd ~/jarvis-2.0
source venv/bin/activate
python -m src.cli

# If setup wizard appears, choose:
# 1. LLM Provider: Ollama
# 2. Model: llama3
# 3. Test connection
# 4. Start chatting!
```

### Using OpenAI (Cloud, Paid)

**Step 1: Get API Key**

1. Go to [platform.openai.com](https://platform.openai.com)
2. Sign up / Log in
3. Navigate to API Keys
4. Create new secret key
5. Copy it (starts with `sk-proj-...`)

**Step 2: Run JARVIS**

```bash
cd ~/jarvis-2.0
source venv/bin/activate
python -m src.cli

# Setup wizard will appear:
# 1. LLM Provider: OpenAI
# 2. API Key: sk-proj-xxxxxxxxxxxxx
# 3. Model: gpt-4 (or gpt-3.5-turbo for cheaper)
# 4. Test connection
# 5. Start chatting!
```

---

## Usage Examples

### Basic Chat

```bash
❯ Hello JARVIS!
JARVIS: Hello! I'm JARVIS 2.0, your AI assistant. How can I help you today?

❯ What can you do?
JARVIS: I can help you with many tasks! I have access to tools for:
- Math calculations
- Web searches
- Weather information
- Taking notes
- Setting timers
- System information
- File operations
- And more!
```

### Using Tools

**Calculator:**
```bash
❯ What's the square root of 144 plus 25 * 48?
🔧 Using tool: calculator(expression="sqrt(144) + 25 * 48")
JARVIS: That equals 1,212! (12 + 1,200)
```

**Web Search:**
```bash
❯ Search for Python best practices 2024
🔧 Using tool: websearch(query="Python best practices 2024")
JARVIS: I found several results about Python best practices...
[Shows search results]
```

**Weather:**
```bash
❯ What's the weather in London?
🔧 Using tool: weather(location="London")
JARVIS: In London, it's currently 15°C with partly cloudy skies...
```

**Notes:**
```bash
❯ Create a note: Buy groceries tomorrow
🔧 Using tool: notes(action="create", content="Buy groceries tomorrow")
JARVIS: Note created successfully!

❯ Show me my notes
🔧 Using tool: notes(action="list")
JARVIS: You have 1 note:
1. Buy groceries tomorrow
```

**System Info:**
```bash
❯ What's my CPU usage?
🔧 Using tool: systeminfo(info_type="cpu")
JARVIS: Your CPU is at 35% usage across 24 cores.
```

### Built-in Commands

JARVIS also has special commands (start with `/`):

```bash
❯ /help
Shows all available commands

❯ /tools
Lists all 10 available tools

❯ /memory
Shows memory statistics

❯ /sessions
Lists all conversation sessions

❯ /clear
Clears the screen

❯ /exit
Exits JARVIS
```

### Memory & Context

JARVIS remembers your conversation:

```bash
❯ My favorite color is blue
JARVIS: Got it! Blue is your favorite color.

❯ What's my favorite color?
JARVIS: Your favorite color is blue! You told me earlier.
```

---

## Troubleshooting

### Common Issues

#### 1. "ModuleNotFoundError: No module named 'XXX'"

**Solution:** Make sure virtual environment is activated and dependencies are installed.

```bash
# Activate venv
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

#### 2. "OpenAI API Error: Invalid API Key"

**Solution:** Check your API key in `.env` file.

```bash
# Verify .env file exists
cat .env

# Make sure OPENAI_API_KEY is correct
# It should start with sk-proj-

# Run setup wizard again
python -m src.cli
```

#### 3. "Ollama connection error"

**Solution:** Make sure Ollama server is running.

```bash
# Check if Ollama is running
ollama list

# If not running, start it
ollama serve

# Try again
python -m src.cli
```

#### 4. "Permission denied" when running JARVIS

**Solution:** Make sure you have write permissions.

```bash
# Check permissions
ls -la user_data/

# If needed, fix permissions
chmod -R 755 user_data/
```

#### 5. Tests failing

**Solution:** Run tests individually to identify the issue.

```bash
# Run each test file separately
python tests/test_function_calling.py
python tests/test_memory.py
python tests/test_plugins.py
python tests/test_integration.py
```

### Debug Mode

Enable debug mode for detailed logs:

```bash
# Edit .env
DEBUG=true
LOG_LEVEL=DEBUG

# Run JARVIS
python -m src.cli

# You'll see detailed logs of everything happening
```

### Clear Database

If memory system acts weird, reset the database:

```bash
# Backup first (optional)
cp user_data/conversations.db user_data/conversations.db.backup

# Remove database
rm user_data/conversations.db

# Restart JARVIS (will create new database)
python -m src.cli
```

---

## Advanced Configuration

### Multiple LLM Providers

You can configure both and switch between them:

```bash
# .env
DEFAULT_LLM=openai

# OpenAI config
OPENAI_API_KEY=sk-proj-xxxxx
OPENAI_MODEL=gpt-4

# Ollama config (fallback)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
```

If OpenAI fails, JARVIS automatically falls back to Ollama!

### Custom Models

**OpenAI:**
```bash
OPENAI_MODEL=gpt-4              # Best quality
OPENAI_MODEL=gpt-4-turbo        # Faster
OPENAI_MODEL=gpt-3.5-turbo      # Cheaper
```

**Ollama:**
```bash
OLLAMA_MODEL=llama3             # Recommended
OLLAMA_MODEL=llama3.2           # Smaller
OLLAMA_MODEL=mistral            # Alternative
OLLAMA_MODEL=codellama          # For code
```

### Memory Settings

Control how much conversation history to keep:

```bash
# .env
MAX_CONTEXT_MESSAGES=20    # Keep last 20 messages (default)
MAX_CONTEXT_MESSAGES=50    # More context (uses more tokens)
MAX_CONTEXT_MESSAGES=10    # Less context (faster)
```

### Disable Features

```bash
# .env
ENABLE_MEMORY=false        # Disable conversation memory
ENABLE_PLUGINS=false       # Disable all tools
```

### Weather API Setup

1. Go to [openweathermap.org/api](https://openweathermap.org/api)
2. Sign up for free account
3. Get your API key
4. Add to `.env`:

```bash
OPENWEATHER_API_KEY=your_key_here
```

Now weather tool will work!

---

## File Structure

```
jarvis-2.0/
├── src/
│   ├── core/              # Core systems
│   │   ├── config.py      # Configuration
│   │   ├── logger.py      # Logging
│   │   ├── llm/           # LLM providers
│   │   ├── tools/         # Tool system
│   │   └── memory/        # Memory system
│   ├── plugins/           # 10 tools
│   └── cli/               # CLI interface
├── tests/                 # Test suite
├── user_data/             # Your data
│   ├── conversations.db   # Chat history
│   └── notes/             # Your notes
├── docs/                  # Documentation
├── .env                   # Your config (create this)
├── .env.example           # Example config
├── requirements.txt       # Dependencies
└── README.md              # Overview
```

---

## Next Steps

Once JARVIS is running:

1. **Explore tools:** Type `What tools do you have?`
2. **Try examples:** See "Usage Examples" above
3. **Check docs:** Read `CURRENT_STATE.md` for details
4. **Run tests:** Verify everything works
5. **Customize:** Add your own tools (see CONTRIBUTING.md)

---

## Getting Help

- **Documentation**: Read all `.md` files in the repository
- **Current State**: Check `CURRENT_STATE.md` for what works
- **Project Plan**: See `PROJECT_PLAN.md` for roadmap
- **LLM Context**: Feed `LLM_CONTEXT.md` to an AI for detailed help

---

## Quick Commands Reference

```bash
# Start JARVIS
python -m src.cli

# Run tests
python tests/test_integration.py

# Check Python version
python --version

# Install Ollama model
ollama pull llama3

# Activate virtual environment
source venv/bin/activate

# View logs
tail -f logs/jarvis.log

# Reset database
rm user_data/conversations.db
```

---

## Success Checklist

✅ Python 3.14+ installed  
✅ Virtual environment created  
✅ Dependencies installed  
✅ `.env` file configured  
✅ LLM provider working (OpenAI or Ollama)  
✅ JARVIS starts successfully  
✅ Can chat with JARVIS  
✅ Tools execute correctly  
✅ Memory saves conversations  

If all checked, you're ready to go! 🚀

---

*Need more help? Check other documentation files or the PROJECT_PLAN.md for details.*
