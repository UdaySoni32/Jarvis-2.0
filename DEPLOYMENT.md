# JARVIS 2.0 Deployment Guide (TUI/API)

## Local deployment

```bash
git clone https://github.com/UdaySoni32/Jarvis-2.0.git
cd Jarvis-2.0
./jarvis setup
jarvis
```

## API deployment (optional)

```bash
source venv/bin/activate
python3 -m src.api.main
```

Set production env in `.env`:

```env
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=change-me
DATABASE_URL=postgresql://user:pass@host/db
```

## Docker-compose dependencies

`docker-compose.yml` provides optional backing services (Postgres, Redis, ChromaDB, Ollama).

## Production checklist

- Set strong secrets
- Use managed PostgreSQL
- Restrict CORS origins
- Enable HTTPS at reverse proxy
- Centralize logs and backups
