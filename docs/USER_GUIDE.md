# 📖 JARVIS 2.0 - User Guide

**Version**: 1.0 | **Phase**: 1 Complete

---

## Table of Contents
1. [Installation](#installation)
2. [Configuration](#configuration)
3. [Running JARVIS](#running-jarvis)
4. [CLI Commands](#cli-commands)
5. [Available Tools](#available-tools)
6. [Examples](#examples)
7. [Troubleshooting](#troubleshooting)

---

## Installation

### Prerequisites
- Python 3.11+ (project uses Python 3.14)
- Git

### Steps

```bash
# 1. Clone the repo
git clone https://github.com/yourusername/jarvis-2.0.git
cd jarvis-2.0

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate      # Linux/macOS
# venv\Scripts\activate       # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy environment template
cp .env.example .env
```

---

## Configuration

Edit `.env` to set your API keys and preferences:

```ini
# Required for OpenAI GPT-4
OPENAI_API_KEY=sk-...

# OR set to use local Ollama model (no API key needed)
DEFAULT_LLM=ollama
OLLAMA_MODEL=llama3           # must have this model pulled

# Optional
OPENWEATHER_API_KEY=...       # enables weather plugin
LOG_LEVEL=INFO
ENABLE_MEMORY=true
```

### LLM Options

| Option | .env setting | Notes |
|--------|-------------|-------|
| OpenAI GPT-4 | `DEFAULT_LLM=openai` | Requires `OPENAI_API_KEY` |
| Ollama (local) | `DEFAULT_LLM=ollama` | Install from [ollama.ai](https://ollama.ai/) |

### Installing Ollama (optional)
```bash
# Install Ollama (Linux)
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a model
ollama pull llama3

# Start Ollama server (usually auto-starts)
ollama serve
```

---

## Running JARVIS

```bash
cd jarvis-2.0
source venv/bin/activate
python -m src.cli
```

On first run, the **Setup Wizard** will guide you through configuration interactively.

---

## CLI Commands

Type these at the `❯` prompt:

| Command | Description |
|---------|-------------|
| `help` | Show all commands |
| `status` | Show system status (LLM, memory, tools) |
| `tools` | List all available tools/plugins |
| `memory` | Show current session info |
| `sessions` | List past conversation sessions |
| `clear` | Clear the terminal screen |
| `exit` or `quit` | Exit JARVIS |
| *anything else* | Sent to the AI as a message |

---

## Available Tools

JARVIS automatically selects the right tool based on your message.

### 🧮 Calculator
Math expressions, including functions.
> "What's 1234 * 5678?"  
> "Calculate sin(pi/2)"

### 💻 System Info
CPU, memory, disk usage.
> "How much RAM is being used?"  
> "What's my disk usage?"

### 📂 File Operations
Read files and list directories.
> "Read the file /etc/hostname"  
> "List files in my home directory"

### 📅 Date & Time
Current date, time, calendar.
> "What's today's date?"  
> "What day of the week is it?"

### 🔍 Web Search
DuckDuckGo search (no API key needed).
> "Search for Python asyncio tutorials"  
> "What is LangChain?"

### 🌤️ Weather
Real-time weather via OpenWeatherMap (API key required).
> "What's the weather in London?"  
> "Weather in New York in Fahrenheit"

### ⏱️ Timer
Set timers and reminders.
> "Set a 5 minute timer"  
> "Remind me in 10 minutes"  
> "Show my active timers"  
> "Cancel timer timer_1"

### 📝 Notes
Create, search, and manage notes.
> "Create a note: Meeting at 3pm tomorrow"  
> "Show all my notes"  
> "Search notes for 'meeting'"  
> "Delete note abc123"

### ⚙️ Process Manager
View and manage system processes.
> "What's using the most CPU?"  
> "Show top 10 processes by memory"  
> "What is PID 1234?"

---

## Examples

### Natural Conversation with Memory
```
❯ My name is Alice

JARVIS: Nice to meet you, Alice! How can I help you today?

❯ What's 25 * 48?

JARVIS: 🔧 Using tool: calculator...
        25 * 48 = 1,200

❯ What's my name?

JARVIS: Your name is Alice! You told me earlier.
```

### Working with Notes
```
❯ Create a note titled "Shopping List" with: Milk, Eggs, Bread

JARVIS: ✅ Created note "Shopping List" (ID: a1b2c3d4)

❯ Show my notes

JARVIS: You have 1 note:
        1. Shopping List - Milk, Eggs, Bread
```

### Session Management
```
❯ sessions

╭──── Sessions (3) ────╮
│ 1. CLI Session (today) │
│ 2. Debug Chat (yesterday) │
╰────────────────────────╯
```

---

## Troubleshooting

### "OpenAI API key not configured"
Set `OPENAI_API_KEY=sk-...` in `.env`, or switch to Ollama: `DEFAULT_LLM=ollama`.

### "Ollama not available"
Ensure Ollama is installed and running:
```bash
ollama serve        # start server
ollama pull llama3  # pull your chosen model
```

### Response is slow
- OpenAI: network-dependent, normal for GPT-4
- Ollama: hardware-dependent, try a smaller model like `phi3`

### Memory not persisting
Check `ENABLE_MEMORY=true` in `.env` and that `user_data/conversations.db` exists.

### Viewing raw conversation database
```bash
sqlite3 user_data/conversations.db
.tables
SELECT * FROM sessions;
SELECT role, content FROM messages ORDER BY timestamp DESC LIMIT 10;
```
