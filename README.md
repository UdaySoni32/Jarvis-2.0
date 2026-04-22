# 🤖 JARVIS 2.0 (TUI-first)

JARVIS 2.0 is an AI assistant focused on a terminal-first workflow with optional voice and API support.

## Quick start

```bash
git clone https://github.com/UdaySoni32/Jarvis-2.0.git
cd Jarvis-2.0
./jarvis setup
jarvis
```

`jarvis setup` bootstraps dependencies, runs configuration, and prepares the local `jarvis` command.

## Interfaces currently supported

- **TUI (primary):** `jarvis`
- **Voice (optional):** `jarvis voice`
- **API (optional):** `python3 -m src.api.main`

### Voice profiles

- **Local/offline pipeline:** `jarvis voice --profile local`
- **Cloud-assisted pipeline:** `jarvis voice --profile cloud`
- **Wake word mode:** `jarvis voice --wake-word`

## Supported model providers

- OpenAI
- Anthropic Claude
- Google Gemini
- Ollama (local)

## Documentation

- [SETUP.md](SETUP.md)
- [TESTING.md](TESTING.md)
- [FEATURES.md](FEATURES.md)
- [DEPLOYMENT.md](DEPLOYMENT.md)

## Status

- ✅ TUI-first command flow (`jarvis`, `jarvis setup`, `jarvis configure`)
- ✅ Voice stack available
- ✅ API server available
- ⏸ Web UI paused/removed for now
