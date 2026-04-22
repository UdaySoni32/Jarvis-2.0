# JARVIS 2.0 Setup Guide (TUI-first)

## Prerequisites

- Python 3.10+
- pip
- Linux audio libs (for voice mode)

## One-command setup

```bash
cd ~/Jarvis-2.0
./jarvis setup
```

This installs dependencies, prepares `.env`, installs `~/.local/bin/jarvis`, and launches TUI.

## Run JARVIS

```bash
jarvis
# or ./jarvis
```

## Voice mode (local + cloud options)

```bash
# Option 1: fully local (Whisper local + pyttsx3)
jarvis voice --profile local

# Option 2: cloud-assisted (Whisper API/Google + gTTS/ElevenLabs)
jarvis voice --profile cloud
```

Optional wake-word mode:

```bash
jarvis voice --wake-word
```

## Configure provider/API keys

```bash
jarvis configure
```

Or edit manually:

```bash
cp .env.example .env
nano .env
```

Use one provider:
- `DEFAULT_LLM=openai` + `OPENAI_API_KEY=...`
- `DEFAULT_LLM=claude` + `ANTHROPIC_API_KEY=...`
- `DEFAULT_LLM=gemini` + `GEMINI_API_KEY=...`
- `DEFAULT_LLM=ollama` + `OLLAMA_BASE_URL=http://localhost:11434`

## Optional API server

```bash
source venv/bin/activate
python3 -m src.api.main
```

API docs: `http://localhost:8000/docs`

## First-time voice setup (mic + speaker)

```bash
sudo apt install -y ffmpeg libportaudio2 portaudio19-dev libasound2-dev espeak-ng
```

Enable in `.env`:

```env
VOICE_ENABLED=true
ENABLE_VOICE=true
VOICE_PROFILE=local
VOICE_STT_PROVIDER=whisper
VOICE_TTS_PROVIDER=pyttsx3
ENABLE_WAKE_WORD=true
PORCUPINE_ACCESS_KEY=your_key
WAKE_WORD_PHRASE=Jarvis Babu
# WAKE_WORD_KEYWORD_PATH=/absolute/path/to/jarvis-babu.ppn
```

Check devices:

```bash
source venv/bin/activate
python3 - <<'PY'
import sounddevice as sd
print(sd.default.device)
print(sd.query_devices())
PY
```

## Troubleshooting

- **`ModuleNotFoundError: src`**: run from project root and use `jarvis` wrapper.
- **No model configured**: run `jarvis configure`.
- **Voice device issues**: verify input/output defaults in OS sound settings and re-run device check.
