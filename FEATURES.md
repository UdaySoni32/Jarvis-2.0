# JARVIS 2.0 Features (TUI-first)

## Core capabilities

- Terminal-first assistant experience (`jarvis`)
- Multi-provider LLM support (OpenAI, Claude, Gemini, Ollama)
- Plugin/tool execution framework
- Conversation memory
- Voice input/output support
- Optional FastAPI server for integrations

## Plugins

Built-in tools include:
- calculator
- system info
- file read/list
- datetime
- web search
- weather
- timer
- notes
- process manager
- email/calendar/database/github/docker integrations
- clipboard, API testing, screen capture OCR

## Security and reliability

- JWT/API-key infrastructure for API mode
- Rate limiting and middleware in API server
- Config-driven behavior via `.env`

## Current product direction

- ✅ TUI-first workflow
- ✅ Voice enhancement track
- ⏸ Web UI paused/removed
