# 🚀 JARVIS 2.0 - Fresh Machine Setup Guide

## ⚡ Quick Start on Fresh Ubuntu Machine

This guide helps you get JARVIS 2.0 running on a fresh Ubuntu clone.

---

## 🔴 Common Issue: PostgreSQL Connection Error

If you see this error:
```
❌ Database initialization failed: (psycopg2.OperationalError) connection to server at "localhost" (127.0.0.1), port 5432 failed: Connection refused
```

**It means**: The `.env` file is configured for PostgreSQL, but PostgreSQL isn't running on your machine.

**Solution**: Use SQLite instead (perfect for development and testing).

---

## ✅ Step-by-Step Fix

### Option 1: Automated (Recommended)

Run this one command:
```bash
cd ~/Jarvis-2.0
sed -i 's/DATABASE_URL=postgresql.*/DATABASE_URL=sqlite:\/\/\/jarvis.db/' .env
```

Then verify:
```bash
grep DATABASE_URL .env
# Should output: DATABASE_URL=sqlite:///jarvis.db
```

### Option 2: Manual Edit

```bash
cd ~/Jarvis-2.0
nano .env
```

Find this line:
```
DATABASE_URL=postgresql://user:password@localhost:5432/jarvis2
```

Replace with:
```
DATABASE_URL=sqlite:///jarvis.db
```

Save with: `Ctrl+X`, then `Y`, then `Enter`

---

## 🚀 Start the API

Once the `.env` is fixed:

```bash
cd ~/Jarvis-2.0
source venv/bin/activate
python3 -m src.api.main
```

### Expected Output
```
[18:23:26] INFO     LLM Manager initialized
           INFO     Tool registry initialized
           ...
           INFO     Registered 18 plugins
✅ Database initialized successfully
✅ API Server started successfully

Uvicorn running on http://0.0.0.0:8000
```

---

## 🧪 Test the API

Open another terminal:

```bash
# Health check
curl http://localhost:8000/health

# Create user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "TestPass123!"
  }'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "TestPass123!"
  }'
```

---

## 🎨 Start Web Interface

In another terminal:

```bash
cd ~/Jarvis-2.0/web
npm run dev
```

Then visit: **http://localhost:3000**

---

## 📊 Database Options

### SQLite (Development/Testing) ✅
- **Pros**: No installation needed, works everywhere, perfect for testing
- **Cons**: Single-user only
- **Config**: `DATABASE_URL=sqlite:///jarvis.db`

### PostgreSQL (Production)
- **Pros**: Multi-user, high performance, scalable
- **Cons**: Needs separate installation
- **Config**: `DATABASE_URL=postgresql://user:password@localhost:5432/db_name`

To use PostgreSQL:
```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Start service
sudo systemctl start postgresql

# Create database (as postgres user)
sudo -u postgres createdb jarvis2

# Update .env
DATABASE_URL=postgresql://postgres:password@localhost:5432/jarvis2
```

---

## 🆘 Troubleshooting

### "Port 8000 already in use"
```bash
lsof -i :8000
# Then kill the process:
kill -9 <PID>
```

### "venv not found"
```bash
# Create it:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### "ModuleNotFoundError"
```bash
# Make sure you're in the right directory
cd ~/Jarvis-2.0
# And venv is activated
source venv/bin/activate
```

### "Port 3000 already in use"
```bash
lsof -i :3000
kill -9 <PID>
```

---

## ✅ What Works

Once running:
- ✅ User registration
- ✅ User login  
- ✅ JWT authentication
- ✅ Health checks
- ✅ All 18 plugins loaded
- ✅ Web interface
- ✅ API documentation at `/docs`

---

## 📝 .env Configuration

After the fix, your `.env` should have:

```env
# Database (FIXED)
DATABASE_URL=sqlite:///jarvis.db

# API Server
API_HOST=0.0.0.0
API_PORT=8000
API_SECRET_KEY=change_this_to_a_random_secret_key

# Other settings
DEBUG=false
ENVIRONMENT=development
```

---

## 🎯 Quick Reference

| Command | Purpose |
|---------|---------|
| `cd ~/Jarvis-2.0` | Go to project |
| `source venv/bin/activate` | Activate Python env |
| `python3 -m src.api.main` | Start API |
| `npm run dev` | Start web UI |
| `curl http://localhost:8000/health` | Test API |
| `http://localhost:3000` | Web UI |

---

## 📖 More Help

- See **README.md** for overview
- See **SETUP.md** for full installation
- See **JARVIS-QUICK-START.md** for quick reference
- See **FEATURES.md** for feature list

---

**Status**: ✅ Ready to use  
**Last Updated**: April 8, 2026  
**For**: Fresh Ubuntu machine setup
