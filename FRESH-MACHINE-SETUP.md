# Fresh Machine Setup (Ubuntu, TUI-first)

## 1. Clone and bootstrap

```bash
cd ~
git clone https://github.com/UdaySoni32/Jarvis-2.0.git
cd Jarvis-2.0
./jarvis setup
```

## 2. Configure model provider

```bash
jarvis configure
```

## 3. Run

```bash
jarvis
```

## 4. Optional API

```bash
source venv/bin/activate
python3 -m src.api.main
curl http://localhost:8000/health
```

## Common fix: database connection

For local development, keep:

```env
DATABASE_URL=sqlite:///jarvis.db
```
