# Testing on a Fresh Ubuntu Machine (TUI-first)

## Setup

```bash
cd ~
git clone https://github.com/UdaySoni32/Jarvis-2.0.git
cd Jarvis-2.0
./jarvis setup
```

## Validate core flows

```bash
./quick_test.sh
jarvis
```

Inside TUI, test:
- `hello`
- `status`
- `how is the cpu usage like`

## Optional API validation

```bash
source venv/bin/activate
python3 -m src.api.main
curl http://localhost:8000/health
```
