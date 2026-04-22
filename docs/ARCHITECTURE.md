# JARVIS 2.0 Architecture (TUI-first)

## System Overview

JARVIS 2.0 is currently optimized for terminal and voice usage, with optional API integration.

```
┌─────────────────────────────────────────────────────────────┐
│                    Interfaces                               │
│   CLI/TUI (primary)  │  Voice  │  API Clients              │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    Core AI Engine                            │
│  LLM manager │ tool registry/executor │ memory manager      │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    Plugin Layer                              │
│  system, file ops, web search, github, docker, etc.        │
└─────────────────────────────────────────────────────────────┘
```

## Key modules

- `src/cli/` - launcher, setup wizard, REPL
- `src/core/` - config, LLM layer, tools, memory
- `src/plugins/` - built-in plugin integrations
- `src/api/` - optional FastAPI service
- `src/voice/` - wake word/STT/TTS stack

## Roadmap focus

- Voice enhancements (wake word, safety confirmation, multilingual)
- TUI reliability and ergonomics
- API compatibility for integrations
- Web UI is intentionally paused
