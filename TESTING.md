# JARVIS 2.0 Testing Guide (TUI-first)

## Quick verification

```bash
cd ~/Jarvis-2.0
./quick_test.sh
```

## TUI smoke test

```bash
jarvis
```

Try:
- `hello`
- `status`
- `how is the cpu usage like`
- `exit`

## API smoke test (optional)

```bash
source venv/bin/activate
python3 -m src.api.main
```

In another terminal:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/docs
```

## Voice smoke test (optional)

```bash
jarvis voice --profile local
```

Check:
- wake word detection
- transcription
- spoken response playback

Cloud-assisted voice test:

```bash
jarvis voice --profile cloud
```

## Full test suite

```bash
source venv/bin/activate
pytest tests/ -v
```
