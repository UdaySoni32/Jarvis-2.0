# JARVIS 2.0 API Server Guide

Complete guide for using the JARVIS 2.0 API Server - remote access to your AI assistant.

## Table of Contents

- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Authentication](#authentication)
- [API Endpoints](#api-endpoints)
- [WebSocket Support](#websocket-support)
- [Rate Limiting](#rate-limiting)
- [Examples](#examples)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start the server
python3 -m src.api.main

# 3. Access API documentation
open http://localhost:8000/docs
```

The server will start on `http://localhost:8000` by default.

---

## Installation

### Requirements

- Python 3.10+
- FastAPI 0.109+
- SQLAlchemy (database)
- Python-JOSE (JWT tokens)
- Passlib (password hashing)

### Install Dependencies

```bash
pip install fastapi uvicorn python-jose[cryptography] passlib[bcrypt] \
    python-multipart websockets sqlalchemy email-validator aiohttp psutil
```

Or use the provided requirements.txt:

```bash
pip install -r requirements.txt
```

---

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Server
API_HOST=0.0.0.0
API_PORT=8000
ENVIRONMENT=production
DEBUG=false

# Security
API_SECRET_KEY=your-super-secret-key-change-this
ACCESS_TOKEN_EXPIRE=60  # minutes
REFRESH_TOKEN_EXPIRE=7  # days

# Database
DATABASE_URL=sqlite:///./jarvis_api.db
# Or PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost/jarvis

# CORS
CORS_ENABLED=true
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=60  # seconds

# LLM
DEFAULT_LLM=ollama
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=AI...
```

### Database Setup

The API server uses SQLite by default. For production, use PostgreSQL:

```bash
# Install PostgreSQL driver
pip install psycopg2-binary

# Update DATABASE_URL in .env
DATABASE_URL=postgresql://user:password@localhost/jarvis
```

Tables are created automatically on first run.

---

## Authentication

The API supports two authentication methods:

### 1. JWT Tokens (Recommended)

**Register a new user:**

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john",
    "email": "john@example.com",
    "password": "securepassword123",
    "full_name": "John Doe"
  }'
```

Response:

```json
{
  "id": "uuid-here",
  "username": "john",
  "email": "john@example.com",
  "full_name": "John Doe",
  "created_at": "2024-04-08T10:00:00"
}
```

**Login:**

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john",
    "password": "securepassword123"
  }'
```

Response:

```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Use the token:**

```bash
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer eyJ..."
```

### 2. API Keys

**Create an API key:**

```bash
curl -X POST http://localhost:8000/api/v1/auth/api-key \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Desktop App",
    "rate_limit": 1000
  }'
```

Response:

```json
{
  "id": "uuid-here",
  "name": "My Desktop App",
  "key": "jarvis_abc123...",
  "created_at": "2024-04-08T10:00:00"
}
```

**Use the API key:**

```bash
curl -X GET http://localhost:8000/api/v1/chat/conversations \
  -H "X-API-Key: jarvis_abc123..."
```

---

## API Endpoints

### Authentication (`/api/v1/auth`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register` | Register new user |
| POST | `/login` | Login and get tokens |
| POST | `/refresh` | Refresh access token |
| GET | `/me` | Get current user info |
| POST | `/api-key` | Create API key |

### Chat (`/api/v1/chat`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/completions` | Send message, get response |
| POST | `/completions/stream` | Stream LLM response |
| GET | `/conversations` | List all conversations |
| GET | `/conversations/{id}` | Get conversation history |

### System (`/api/v1/system`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/status` | System status and metrics |
| GET | `/models` | List available LLM models |
| POST | `/models/{name}` | Switch active model |
| GET | `/plugins` | List available plugins |

### WebSocket (`/api/v1/ws`)

| Endpoint | Description |
|----------|-------------|
| `/chat` | Real-time chat WebSocket |

---

## WebSocket Support

Connect to the WebSocket endpoint for real-time chat:

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/chat');

// Send authentication
ws.send(JSON.stringify({
  type: 'auth',
  token: 'your-jwt-token'
}));

// Send message
ws.send(JSON.stringify({
  type: 'message',
  message: 'Hello JARVIS!'
}));

// Receive messages
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};
```

---

## Rate Limiting

Rate limiting protects the API from abuse:

- **Default**: 100 requests per 60 seconds
- **Per user/API key**: Configurable per API key
- **Response headers**:
  - `X-RateLimit-Limit`: Total requests allowed
  - `X-RateLimit-Remaining`: Requests remaining
  - `X-RateLimit-Reset`: Unix timestamp when limit resets

**Error response:**

```json
{
  "detail": "Rate limit exceeded. Max 100 requests per 60 seconds."
}
```

---

## Examples

### Send a Chat Message

```python
import requests

url = "http://localhost:8000/api/v1/chat/completions"
headers = {
    "Authorization": "Bearer your-token-here",
    "Content-Type": "application/json"
}
data = {
    "message": "What's the weather like?",
    "model": "gpt-4"
}

response = requests.post(url, json=data, headers=headers)
result = response.json()
print(result["message"])
```

### Stream Chat Response

```python
import requests

url = "http://localhost:8000/api/v1/chat/completions/stream"
headers = {
    "Authorization": "Bearer your-token-here",
    "Content-Type": "application/json"
}
data = {
    "message": "Tell me a story"
}

with requests.post(url, json=data, headers=headers, stream=True) as r:
    for line in r.iter_lines():
        if line:
            print(line.decode())
```

### Get System Status

```python
import requests

url = "http://localhost:8000/api/v1/system/status"
headers = {"Authorization": "Bearer your-token-here"}

response = requests.get(url, headers=headers)
status = response.json()

print(f"Platform: {status['system']['platform']}")
print(f"CPU: {status['resources']['cpu_percent']}%")
print(f"Memory: {status['resources']['memory_percent']}%")
print(f"LLM: {status['config']['llm_provider']}")
```

### List Conversations

```python
import requests

url = "http://localhost:8000/api/v1/chat/conversations"
headers = {"Authorization": "Bearer your-token-here"}

response = requests.get(url, headers=headers)
conversations = response.json()

for conv in conversations["conversations"]:
    print(f"ID: {conv['conversation_id']}")
    print(f"Messages: {conv['message_count']}")
    print(f"Last: {conv['last_message']}\n")
```

---

## Deployment

### Development

```bash
# Auto-reload on code changes
python3 -m src.api.main
```

### Production with Gunicorn

```bash
# Install gunicorn
pip install gunicorn

# Run with 4 workers
gunicorn src.api.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

### Production with Uvicorn

```bash
# Run with production settings
uvicorn src.api.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --no-access-log \
  --log-level warning
```

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Build and run
docker build -t jarvis-api .
docker run -p 8000:8000 -e API_SECRET_KEY=your-secret jarvis-api
```

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Troubleshooting

### Server Won't Start

**Error**: `ModuleNotFoundError: No module named 'fastapi'`

```bash
# Install dependencies
pip install -r requirements.txt
```

**Error**: `Address already in use`

```bash
# Change port in .env
API_PORT=8001
```

### Authentication Errors

**Error**: `Invalid or expired token`

```bash
# Get a new token
curl -X POST http://localhost:8000/api/v1/auth/login ...
```

**Error**: `Authentication required`

```bash
# Make sure you're sending the token
curl -H "Authorization: Bearer your-token" ...
```

### Database Errors

**Error**: `Table 'users' does not exist`

```bash
# Database will be created on first run
# Delete and restart if corrupted
rm jarvis_api.db
python3 -m src.api.main
```

### Rate Limit Exceeded

**Error**: `429 Too Many Requests`

```bash
# Wait for rate limit reset
# Or increase limit in .env
RATE_LIMIT_REQUESTS=1000
```

### CORS Errors

**Error**: `CORS policy: No 'Access-Control-Allow-Origin'`

```bash
# Add your origin to .env
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

---

## API Documentation

Interactive API documentation is available at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These provide:
- Complete endpoint reference
- Request/response schemas
- Interactive testing
- Authentication setup

---

## Security Best Practices

1. **Change secret keys**: Never use default secret keys in production

```env
API_SECRET_KEY=$(openssl rand -hex 32)
```

2. **Use HTTPS**: Always use HTTPS in production

3. **Limit CORS origins**: Only allow trusted domains

4. **Rate limiting**: Enable and configure appropriately

5. **Keep tokens secure**: Never commit tokens to git

6. **Rotate API keys**: Regularly rotate keys for security

7. **Use environment variables**: Never hard-code credentials

8. **Update dependencies**: Keep packages up to date

```bash
pip install --upgrade pip
pip list --outdated
```

---

## Support

For issues, questions, or contributions:

- GitHub Issues: [Report bugs](https://github.com/UdaySoni32/Jarvis-2.0/issues)
- Documentation: See project README and other guides
- Examples: Check the `examples/` directory

---

**Version**: 2.0.0  
**Last Updated**: April 8, 2026

