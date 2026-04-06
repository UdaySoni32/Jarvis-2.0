# 🏗️ JARVIS 2.0 - Architecture Overview

**Version**: 1.0 (Phase 1 Complete)  
**Last Updated**: April 6, 2026

---

## System Overview

JARVIS 2.0 is a layered AI assistant. Each layer is independent and communicates through well-defined interfaces.

```
┌─────────────────────────────────────────────────────────────┐
│                    Interfaces (Phase 3+)                     │
│   CLI (✅ done)  │  Web UI  │  Desktop GUI  │  Voice         │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    Core AI Engine (Phase 1 ✅)               │
│                                                             │
│   ┌────────────┐   ┌─────────────┐   ┌──────────────────┐  │
│   │ LLM Layer  │   │ Tool System │   │  Memory System   │  │
│   │            │   │             │   │                  │  │
│   │ OpenAI     │   │ Registry    │   │ SQLite DB        │  │
│   │ Ollama     │   │ Executor    │   │ Session Mgr      │  │
│   │ (Anthropic │   │ BaseTool    │   │ Context Window   │  │
│   │  future)   │   │             │   │ Search           │  │
│   └────────────┘   └─────────────┘   └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    Plugin Layer (Phase 1.5 ✅)               │
│                                                             │
│  Calculator │ SystemInfo │ FileOps │ DateTime │ WebSearch   │
│  Weather    │ Timer      │ Notes   │ ProcessManager          │
└─────────────────────────────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    Data Layer                               │
│                                                             │
│  SQLite (conversations) │ JSON (notes) │ .env (config)      │
│  ChromaDB (Phase 2+)    │ Redis (Phase 3+)                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
jarvis-2.0/
├── src/
│   ├── core/                      # Core AI engine
│   │   ├── config.py              # Pydantic settings (from .env)
│   │   ├── logger.py              # Rich-based logging
│   │   ├── llm/                   # LLM abstraction layer
│   │   │   ├── base.py            # BaseLLMProvider + Message dataclass
│   │   │   ├── openai_provider.py # OpenAI GPT integration
│   │   │   ├── ollama_provider.py # Ollama local LLM
│   │   │   └── manager.py         # Provider selection & fallback
│   │   ├── tools/                 # Function calling system
│   │   │   ├── base.py            # BaseTool + ToolParameter
│   │   │   ├── registry.py        # ToolRegistry (dict + OpenAI schema)
│   │   │   └── executor.py        # Async tool executor
│   │   └── memory/                # Conversation persistence
│   │       ├── models.py          # Message + ConversationSession
│   │       ├── storage.py         # SQLite CRUD + FTS search
│   │       └── manager.py         # MemoryManager (high-level API)
│   ├── plugins/                   # Individual tool plugins
│   │   ├── __init__.py            # Auto-registers all plugins
│   │   ├── calculator.py
│   │   ├── system_info.py
│   │   ├── file_ops.py
│   │   ├── datetime_info.py
│   │   ├── web_search.py
│   │   ├── weather.py
│   │   ├── timer.py
│   │   ├── notes.py
│   │   └── process_manager.py
│   └── cli/                       # Command-line interface
│       ├── __main__.py            # Entry point
│       ├── repl.py                # REPL loop (prompt_toolkit)
│       └── setup_wizard.py        # First-time TUI setup
├── tests/                         # Test suite
│   ├── conftest.py                # pytest fixtures
│   ├── test_core.py               # Config, memory, tool tests
│   ├── test_plugins.py            # Plugin-specific tests
│   ├── test_memory.py             # Memory standalone script
│   ├── test_function_calling.py   # Tool calling standalone
│   └── test_integration.py        # End-to-end integration
├── user_data/
│   ├── conversations.db           # SQLite conversation database
│   ├── conversations/             # (reserved for export)
│   └── memory/                    # (reserved for vector memory Ph2)
├── docs/                          # Documentation
├── config/                        # Extra config files
├── scripts/                       # Utility scripts
├── logs/                          # Log files
├── .env                           # Local config (not committed)
└── requirements.txt
```

---

## Data Flow: User Message Processing

```
User types message
        │
        ▼
REPL (repl.py)
  - Add to memory (memory_manager.add_message)
  - Build context (memory_manager.get_context_messages)
        │
        ▼
LLM Manager (manager.py)
  - Select provider (OpenAI or Ollama)
  - Send [system_prompt + context + user_message + tool_schemas]
        │
        ▼
LLM Response
  ├── Plain text → stream to terminal
  └── Tool call detected
            │
            ▼
        Tool Executor (executor.py)
          - Look up tool in registry
          - Call tool.execute(**args)
          - Return result to LLM
                  │
                  ▼
              LLM formats result → stream to terminal
        │
        ▼
Save assistant reply to memory
```

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| **SQLite for memory** | Zero setup, portable, sufficient for single-user |
| **Pydantic settings** | Type-safe, validates .env on startup |
| **BaseTool ABC** | Uniform plugin interface for registry & LLM schema |
| **Ollama fallback** | Works offline without an API key |
| **prompt_toolkit REPL** | Persistent history, readline support |

---

## Phase Roadmap

| Phase | Status | Key Additions |
|---|---|---|
| 0 - Foundation | ✅ Done | Project structure, Docker, docs |
| 1 - Core AI Engine | ✅ Done | CLI, LLM, tools, memory, 10 plugins |
| 2 - Advanced Intelligence | 🔜 Next | ChromaDB, agent system, task scheduler |
| 3 - Multi-Modal | ⏸ Planned | Voice, Desktop GUI (Tauri), Web UI (Next.js) |
| 4 - Plugin Ecosystem | ⏸ Planned | Plugin SDK, marketplace |
| 5 - Mobile | ⏸ Planned | React Native app |
| 6 - Security | ⏸ Planned | E2E encryption, audit logging |
| 7 - Deployment | ⏸ Planned | Installers, distro packages |
