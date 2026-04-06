# 🤖 JARVIS 2.0 - Complete Project Context for LLMs

**This document provides complete context about the JARVIS 2.0 project for AI assistants to understand the entire system, architecture, implementation details, and current state.**

---

## 📋 PROJECT OVERVIEW

**Name**: JARVIS 2.0 - AI-Powered Personal Assistant  
**Location**: `/home/uday/jarvis-2.0`  
**Language**: Python 3.11+  
**Status**: Phase 1 Development (40% complete)  
**Start Date**: April 6, 2026

### Vision
Build an intelligent AI-powered personal assistant that understands natural language, has context-aware memory, supports multiple AI agents for complex tasks, automates repetitive work, and provides multi-modal interfaces (CLI, GUI, Voice, Web, Mobile) with privacy-first local LLM support.

### Key Differentiators from Original Jarvis
- **Natural Language**: Not command-based, understands conversational input
- **LLM-Powered**: Uses GPT-4, Claude, or local LLMs (Ollama)
- **Context Memory**: Remembers conversations and learns preferences
- **Multi-Agent**: Specialized agents for planning, research, coding, tasks
- **Multi-Modal**: CLI, Desktop GUI, Web, Voice, Mobile
- **Extensible**: Plugin SDK with AI-enhanced tools
- **Privacy-First**: Can run entirely local with Ollama

---

## 🏗️ ARCHITECTURE

### High-Level System Design

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interfaces                          │
│    [CLI/TUI]  [Desktop GUI]  [Web]  [Voice]  [Mobile]      │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                 Core AI Engine                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ LLM Manager  │  │ Agent System │  │ Memory Mgr   │     │
│  │ - OpenAI     │  │ - Planning   │  │ - Short-term │     │
│  │ - Claude     │  │ - Research   │  │ - Long-term  │     │
│  │ - Ollama     │  │ - Code       │  │ - Vector DB  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│              Tools & Plugins Layer                          │
│  [System Info] [File Ops] [Web Search] [Weather]           │
│  [Calculator] [Timer] [Notes] [Process Mgr] [Custom...]    │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                Data & Storage Layer                         │
│  [SQLite]  [Redis]  [ChromaDB]  [File System]              │
└─────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
jarvis-2.0/
├── src/                          # Source code
│   ├── core/                     # Core systems
│   │   ├── config.py            # Configuration management (Pydantic settings)
│   │   ├── logger.py            # Logging setup (Rich + file)
│   │   ├── llm/                 # LLM providers
│   │   │   ├── base.py         # Abstract LLM interface
│   │   │   ├── openai_provider.py    # OpenAI GPT integration
│   │   │   ├── ollama_provider.py    # Ollama local LLM
│   │   │   └── manager.py      # LLM factory/manager
│   │   ├── tools/               # Tool/function calling system
│   │   │   ├── base.py         # Tool base class
│   │   │   ├── registry.py     # Tool registration
│   │   │   └── executor.py     # Tool execution engine
│   │   └── memory/              # Memory systems
│   │       ├── conversation.py  # Conversation history
│   │       ├── session.py      # Session management
│   │       └── vector.py       # Vector store interface
│   ├── plugins/                 # Tool plugins
│   │   ├── system_info.py      # CPU, RAM, disk
│   │   ├── file_ops.py         # File operations
│   │   ├── web_search.py       # Web search
│   │   ├── weather.py          # Weather info
│   │   ├── calculator.py       # Math operations
│   │   └── ...
│   ├── agents/                  # AI agents
│   │   ├── base.py             # Base agent class
│   │   ├── planning.py         # Planning agent
│   │   ├── research.py         # Research agent
│   │   └── code.py             # Code agent
│   ├── cli/                     # Command-line interface
│   │   ├── repl.py             # REPL implementation (WORKING ✅)
│   │   ├── setup_wizard.py     # First-time setup TUI
│   │   └── __main__.py         # Entry point
│   ├── api/                     # REST API (Phase 3)
│   └── gui/                     # Desktop GUI (Phase 3)
├── tests/                       # Test suite
├── docs/                        # Documentation
├── config/                      # Config files
├── user_data/                   # User data (created at runtime)
│   ├── conversations/          # Conversation history
│   └── memory/                 # Memory store
├── PROJECT_PLAN.md             # Complete roadmap (548 lines, 8 phases)
├── PROGRESS.md                 # Current session progress
├── README.md                   # Project overview
├── requirements.txt            # Python dependencies
├── .env                        # Environment configuration
└── Makefile                    # Common commands
```

---

## 🔧 TECHNICAL STACK

### Backend
- **Python**: 3.11+ (using 3.14.3)
- **Framework**: AsyncIO for async operations
- **LLM Integration**: LangChain patterns (custom implementation)
- **API**: FastAPI (planned for Phase 3)

### AI/ML
- **LLMs**: 
  - OpenAI GPT-4 (cloud, primary)
  - Anthropic Claude (cloud, alternative)
  - Ollama with Llama 3 (local, fallback)
- **Embeddings**: sentence-transformers
- **Vector DB**: ChromaDB for semantic memory
- **Speech**: Whisper (STT), pyttsx3/ElevenLabs (TTS)

### Data Storage
- **Primary DB**: SQLite (conversation history, sessions)
- **Cache**: Redis (optional)
- **Vector Store**: ChromaDB (semantic memory)
- **Files**: JSON/SQLite for structured data

### UI Libraries
- **CLI**: 
  - Rich (colorized output, panels, markdown)
  - prompt-toolkit (REPL, history, autocomplete)
- **Desktop GUI**: Tauri + React (Phase 3)
- **Web**: Next.js + FastAPI (Phase 3)

### Configuration
- **Settings**: Pydantic Settings (type-safe, env-based)
- **Env**: python-dotenv for .env files
- **Validation**: Pydantic models

---

## 📦 DEPENDENCIES

### Currently Installed
```python
# Core
rich>=13.7.0              # CLI formatting
prompt-toolkit>=3.0.43    # REPL interface
pydantic>=2.6.0           # Settings & validation
pydantic-settings>=2.1.0  # Environment-based config
python-dotenv>=1.0.1      # .env file support

# Planned Next
openai>=1.12.0            # OpenAI API
tiktoken>=0.6.0           # Token counting
httpx>=0.26.0             # Ollama API client
```

### Full Dependencies (requirements.txt)
- LangChain ecosystem (langchain, langchain-openai, langchain-community)
- Vector DB (chromadb, sentence-transformers)
- API framework (fastapi, uvicorn, websockets)
- Database (sqlalchemy, redis, psycopg2-binary)
- Task queue (celery, apscheduler)
- Voice (openai-whisper, pyttsx3, pyaudio)
- Utilities (requests, httpx, aiohttp)
- File processing (pypdf, pillow, opencv-python-headless)
- Data (pandas, numpy)
- System (psutil, watchdog)

---

## ⚙️ CONFIGURATION SYSTEM

### Environment Variables (.env)

```bash
# LLM Configuration
OPENAI_API_KEY=sk-...                # OpenAI API key
ANTHROPIC_API_KEY=sk-ant-...         # Claude API key
DEFAULT_LLM=openai                   # openai|anthropic|ollama
OPENAI_MODEL=gpt-4-turbo-preview
OLLAMA_MODEL=llama3
OLLAMA_BASE_URL=http://localhost:11434

# Database
DATABASE_URL=sqlite:///./jarvis_data.db
REDIS_URL=redis://localhost:6379/0

# Vector Database
CHROMA_HOST=localhost
CHROMA_PORT=8000

# Features
ENABLE_MEMORY=true
ENABLE_WEB_SEARCH=true
ENABLE_VOICE=false
ENABLE_PLUGINS=true

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/jarvis.log
DEBUG=false

# User Data
USER_DATA_DIR=./user_data
```

### Settings Class (src/core/config.py)
- Pydantic-based settings loaded from .env
- Type-safe configuration
- Auto-creates necessary directories
- Provides helper methods (has_openai_key, can_use_cloud_llm)

---

## 🎯 CURRENT IMPLEMENTATION STATUS

### ✅ Phase 0: Foundation (100% Complete)
**What's Done:**
- Complete project structure
- All planning documents (2,500+ lines)
- Configuration files (requirements.txt, .env, Makefile, docker-compose.yml)
- Virtual environment with dependencies
- Git-ready structure

**Files Created:**
- PROJECT_PLAN.md (548 lines) - Complete 8-phase roadmap with 200+ tasks
- STATUS.md - Current progress tracker
- TODO.md - Immediate next steps
- QUICKSTART.md - Quick reference guide
- PROGRESS.md - Session progress
- README.md - Project overview
- CONTRIBUTING.md - Development guidelines

### ✅ Phase 1.1: Basic CLI Interface (100% Complete)
**What's Done:**
- Configuration system with Pydantic
- Logging system with Rich formatting
- Full REPL implementation (225 lines)
- Command history persistence
- Built-in commands (help, status, clear, exit)
- Colorized output
- **CLI is fully working! ✅**

**Key Files:**
- `src/core/config.py` (115 lines) - Configuration management
- `src/core/logger.py` (60 lines) - Logging setup
- `src/cli/repl.py` (225 lines) - Main REPL loop
- `src/cli/__main__.py` - Entry point

**Working Commands:**
```bash
cd /home/uday/jarvis-2.0
source venv/bin/activate
python -m src.cli

# Commands: help, status, clear, exit
```

### ⏳ Phase 1.2: LLM Integration (20% Complete)
**What's Done:**
- LLM base interface with abstract provider pattern
- Message class for chat messages
- Abstract methods for generate, stream, function calling

**In Progress:**
- OpenAI provider implementation
- Ollama provider implementation
- LLM manager/factory
- Integration with CLI

**Key Files:**
- `src/core/llm/base.py` (125 lines) - Abstract LLM interface

### ⏸️ Phase 1.3-1.6: Not Started
- Function calling system
- Memory system
- Core plugins (8 tools)
- Testing & documentation

---

## 🔄 USER WORKFLOWS

### First-Time Setup (Planned - To Be Implemented)
1. User runs: `python -m src.cli`
2. System detects no .env file or missing API keys
3. **Setup Wizard Launches** (TUI):
   ```
   ╔══════════════════════════════════════════════╗
   ║    🤖 Welcome to JARVIS 2.0 Setup           ║
   ╚══════════════════════════════════════════════╝
   
   Choose your LLM provider:
   > [*] OpenAI GPT-4 (requires API key)
   > [ ] Anthropic Claude (requires API key)
   > [ ] Ollama (free, runs locally)
   
   [Next] [Skip] [Exit]
   ```
4. User selects provider and enters API key
5. Configuration saved to .env
6. Optional: Test connection
7. Launch main interface

### Normal Usage
1. Run: `python -m src.cli`
2. See welcome screen with status
3. Type naturally: "What's the weather?"
4. JARVIS responds using LLM
5. Memory persists across sessions

### Developer Workflow
```bash
# Setup
make setup               # Create venv
source venv/bin/activate
make install             # Install deps

# Development
make dev                 # Run in dev mode
make test                # Run tests
make format              # Format code
make lint                # Run linters

# Run
make run                 # Run CLI
python -m src.cli        # Direct run
```

---

## 🧩 CORE COMPONENTS DETAILED

### 1. Configuration System (src/core/config.py)

**Purpose**: Centralized configuration management

**Key Features:**
- Pydantic Settings for type-safe config
- Loads from .env file
- Auto-creates directories
- Validation of settings
- Helper methods

**Usage:**
```python
from src.core.config import settings

if settings.has_openai_key:
    # Use OpenAI
    model = settings.openai_model
```

### 2. Logging System (src/core/logger.py)

**Purpose**: Unified logging across the application

**Key Features:**
- Rich console formatting
- File logging
- Configurable log levels
- Tracebacks with locals in debug mode

**Usage:**
```python
from src.core.logger import logger

logger.info("Starting JARVIS")
logger.error("Error occurred", exc_info=True)
```

### 3. CLI REPL (src/cli/repl.py)

**Purpose**: Interactive command-line interface

**Key Features:**
- Async REPL loop
- Command history (saved to file)
- Built-in commands
- Rich formatting (panels, markdown)
- Graceful error handling

**Class Structure:**
```python
class REPL:
    def __init__(self): ...
    def print_welcome(self): ...
    def print_help(self): ...
    def print_status(self): ...
    def handle_builtin_command(self, input: str) -> bool: ...
    async def process_input(self, input: str): ...
    async def run(self): ...
```

**Current Built-in Commands:**
- `help` - Show help
- `status` - System status
- `clear` - Clear screen
- `exit/quit` - Exit JARVIS
- `history` - View history (planned)

### 4. LLM Base Interface (src/core/llm/base.py)

**Purpose**: Abstract interface for LLM providers

**Key Classes:**
```python
class Message:
    role: str  # system, user, assistant, function
    content: str
    
    def to_dict(self) -> Dict[str, str]

class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate(messages, temperature, max_tokens, stream) -> str
    
    @abstractmethod
    async def generate_stream(messages) -> AsyncIterator[str]
    
    @abstractmethod
    async def generate_with_functions(messages, functions) -> Dict
    
    @abstractmethod
    def count_tokens(text: str) -> int
    
    @abstractmethod
    async def is_available() -> bool
```

**Planned Implementations:**
- OpenAIProvider (GPT-4, streaming, function calling)
- OllamaProvider (local Llama 3, streaming)
- ClaudeProvider (Claude 3 Opus)

---

## 🎨 UI/UX DESIGN

### CLI Welcome Screen (Current)
```
╭──────────────────────────────────────────────────╮
│      🤖 JARVIS 2.0 - AI Personal Assistant      │
│                                                  │
│ Welcome! I'm JARVIS, your AI assistant.         │
│                                                  │
│ Available Commands:                             │
│ • Type naturally - no commands needed!          │
│ • help - Show commands                          │
│ • status - System status                        │
│ • exit - Exit JARVIS                            │
╰──────────────────────────────────────────────────╯

✅ OpenAI API configured (using GPT-4)

❯ 
```

### Setup Wizard TUI (Planned)
- Multi-step form using prompt-toolkit or Textual
- Interactive LLM provider selection
- API key input with masking
- Connection testing
- Settings summary and confirmation

### Conversation Flow (Planned)
```
❯ What's the weather in Tokyo?

🤖 Processing...

The current weather in Tokyo is:
• Temperature: 24°C (75°F)
• Conditions: Partly cloudy
• Humidity: 65%
• Wind: 12 km/h NE

Would you like a forecast for the week?

❯ 
```

---

## 🔌 PLUGIN SYSTEM (Planned Phase 1.5)

### Plugin Architecture
```python
class BaseTool:
    name: str
    description: str
    parameters: Dict[str, Any]
    
    async def execute(self, **kwargs) -> Any
    
    def to_function_schema(self) -> Dict
```

### Example Plugin: System Info
```python
@tool("system_info")
class SystemInfoTool(BaseTool):
    """Get CPU, RAM, and disk usage."""
    
    async def execute(self):
        return {
            "cpu_percent": psutil.cpu_percent(),
            "memory": psutil.virtual_memory()._asdict(),
            "disk": psutil.disk_usage('/')._asdict()
        }
```

### Planned Core Plugins
1. **system_info** - CPU, RAM, disk
2. **file_ops** - read, write, list files
3. **web_search** - DuckDuckGo/Google
4. **weather** - OpenWeatherMap
5. **calculator** - Math expressions
6. **timer** - Reminders, alarms
7. **notes** - Note taking
8. **process_manager** - List/kill processes

---

## 💾 DATA MODELS

### Conversation History
```python
class Message:
    id: str
    session_id: str
    role: str  # system, user, assistant, function
    content: str
    timestamp: datetime
    metadata: Dict[str, Any]

class Session:
    id: str
    user_id: str
    started_at: datetime
    ended_at: Optional[datetime]
    messages: List[Message]
    metadata: Dict[str, Any]
```

### Memory Store
```python
class MemoryEntry:
    id: str
    session_id: str
    content: str
    embedding: List[float]  # Vector embedding
    importance: float
    timestamp: datetime
    tags: List[str]
```

---

## 🚀 DEVELOPMENT PHASES (8 Total)

### Phase 0: Foundation ✅ (100%)
- Project structure, docs, config

### Phase 1: Core AI Engine ⏳ (40%)
- CLI interface ✅
- LLM integration ⏳ (20%)
- Function calling ⏸️
- Memory system ⏸️
- Core plugins ⏸️
- Testing ⏸️

### Phase 2: Advanced Intelligence (0%)
- Vector DB & semantic memory
- Multi-agent system
- Task automation
- Learning from behavior

### Phase 3: Multi-Modal (0%)
- Voice interface
- Desktop GUI (Tauri)
- Web dashboard
- API server

### Phase 4: Plugin Ecosystem (0%)
- Plugin SDK
- Plugin marketplace
- Advanced plugins

### Phase 5: Mobile (0%)
- React Native app
- Cross-device sync

### Phase 6: Security (0%)
- Encryption
- Privacy compliance

### Phase 7: Deployment (0%)
- Installers
- Auto-updates

### Phase 8: Advanced Features (0%)
- Enterprise features
- Advanced AI

---

## 📝 CODING STANDARDS

### Python Style
- PEP 8 compliant
- Type hints everywhere
- Docstrings (Google style)
- Max line length: 100
- Use `black` for formatting
- Use `ruff` for linting

### Project Conventions
- Async/await for I/O operations
- Pydantic for data validation
- Rich for CLI output
- Logging instead of print()
- Configuration via environment
- No hardcoded values

### Error Handling
```python
try:
    result = await llm.generate(messages)
except Exception as e:
    logger.error(f"LLM error: {e}", exc_info=True)
    raise
```

---

## 🧪 TESTING STRATEGY

### Test Structure (Planned)
```
tests/
├── unit/
│   ├── test_config.py
│   ├── test_llm_providers.py
│   └── test_tools.py
├── integration/
│   ├── test_cli.py
│   └── test_llm_integration.py
└── e2e/
    └── test_full_workflow.py
```

### Testing Tools
- pytest for test framework
- pytest-asyncio for async tests
- pytest-cov for coverage
- pytest-mock for mocking

---

## 📊 CURRENT FILE STATISTICS

**Total Files Created**: 35+  
**Total Lines of Code**: ~800+  
**Total Documentation**: ~2,500+  
**Languages**: Python, Markdown, YAML, Makefile

**Key Metrics:**
- PROJECT_PLAN.md: 548 lines
- src/cli/repl.py: 225 lines
- src/core/config.py: 115 lines
- src/core/llm/base.py: 125 lines

---

## 🎯 IMMEDIATE NEXT STEPS

### To Complete Phase 1.2 (LLM Integration)
1. Finish OpenAI provider implementation
2. Create Ollama provider for local LLM
3. Create LLM manager/factory
4. Add streaming response support
5. Integrate with CLI REPL
6. Test end-to-end conversation

### To Add Setup Wizard
1. Create `src/cli/setup_wizard.py`
2. Build interactive TUI with prompt-toolkit
3. API key input and validation
4. Test LLM connection
5. Save configuration to .env
6. Launch main CLI after setup

### To Complete Phase 1.3 (Function Calling)
1. Implement tool registry
2. Create tool executor
3. Add function schema generation
4. Integrate with LLM
5. Build first 2-3 plugins

---

## 🔗 KEY RESOURCES

### Documentation Files
- `PROJECT_PLAN.md` - Complete roadmap
- `PROGRESS.md` - Current session work
- `TODO.md` - Immediate tasks
- `QUICKSTART.md` - Quick start guide
- `README.md` - Project overview
- `LLM_CONTEXT.md` - This file

### External Resources
- LangChain: https://python.langchain.com/
- OpenAI API: https://platform.openai.com/docs
- Ollama: https://ollama.ai/
- Rich: https://rich.readthedocs.io/
- Pydantic: https://docs.pydantic.dev/

---

## 🎓 LEARNING NOTES

### Design Decisions
1. **Async-first**: All I/O is async for better performance
2. **Provider pattern**: Abstract LLM interface for easy switching
3. **Pydantic everywhere**: Type safety and validation
4. **Rich CLI**: Better UX than plain terminal
5. **Local-first**: Support offline operation with Ollama

### Challenges Solved
- ✅ Configuration management with type safety
- ✅ Beautiful CLI with minimal dependencies
- ✅ Command history persistence
- ✅ Graceful error handling

### Challenges Ahead
- ⏳ LLM streaming in CLI
- ⏳ Function calling integration
- ⏳ Memory management at scale
- ⏳ Multi-agent coordination

---

## 💡 USAGE EXAMPLES (When Complete)

### Basic Chat
```bash
❯ What's 25 * 48?
🤖 25 × 48 = 1,200

❯ Write a Python function to reverse a string
🤖 Here's a function to reverse a string:

def reverse_string(s: str) -> str:
    return s[::-1]

# Example usage:
result = reverse_string("hello")  # Returns: "olleh"
```

### Using Tools
```bash
❯ What's my CPU usage?
🤖 Let me check that for you...
[Calling system_info tool]

Your current system stats:
• CPU Usage: 23.5%
• Memory: 8.2 GB / 16 GB (51%)
• Disk: 245 GB / 512 GB (48%)
```

### Complex Tasks
```bash
❯ Find the latest Python releases and create a markdown table
🤖 I'll search for that information...
[Calling web_search tool]
[Processing results]

Here's a table of recent Python releases:

| Version | Release Date | Status |
|---------|--------------|--------|
| 3.12.1  | Dec 2023    | Latest |
| 3.11.7  | Dec 2023    | Stable |
| 3.10.13 | Nov 2023    | Stable |
```

---

## 🎉 PROJECT HIGHLIGHTS

### What Makes JARVIS 2.0 Special
1. **Natural Conversation**: No commands, just talk
2. **Memory**: Remembers context across sessions
3. **Local Option**: Run 100% offline with Ollama
4. **Extensible**: Easy plugin system
5. **Multi-Modal**: CLI today, GUI/Voice/Web later
6. **Privacy-First**: Your data stays local
7. **Open Source**: MIT licensed

### Success Metrics
- Response time < 2s for simple queries
- 95%+ uptime
- 80%+ test coverage
- Active community contributions

---

## 🤝 FOR AI ASSISTANTS READING THIS

**Context for you:**
- This is a from-scratch AI assistant project
- User wants to build it step-by-step
- Currently in Phase 1 (40% complete)
- CLI is working, LLM integration in progress
- Need to add: setup wizard, complete LLM, add tools
- User values: detailed docs, working code, good UX

**When helping:**
- Reference existing code in src/
- Follow the architecture outlined here
- Match coding style (async, type hints, pydantic)
- Update PROGRESS.md when making changes
- Think about the full system context
- Suggest improvements but respect the plan

**Current Priority:**
1. Add setup wizard for first-time config
2. Complete LLM integration (OpenAI + Ollama)
3. Add function calling system
4. Create first few plugins

---

**Last Updated**: April 6, 2026  
**Document Version**: 1.0  
**Maintained By**: Development team

---

*This document should give you complete context to understand and work with JARVIS 2.0!* 🚀
