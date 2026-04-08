# 🚀 JARVIS 2.0 Deployment Guide

This guide covers deploying JARVIS 2.0 in different environments.

## Quick Deployment Checklist

- [ ] Clone repository
- [ ] Run setup: `bash quick_setup.sh`
- [ ] Configure: `cp .env.example .env`
- [ ] Verify: `bash quick_test.sh`
- [ ] Test system: `bash test_complete_system.sh`

## Local Deployment

### Development Setup

```bash
# Clone and setup
git clone https://github.com/UdaySoni32/Jarvis-2.0.git
cd Jarvis-2.0
bash quick_setup.sh

# Configure
cp .env.example .env
nano .env  # Add your API keys
```

### Running Locally

**Terminal 1: Start API Server**
```bash
source venv/bin/activate
python3 -m src.api.main
```

**Terminal 2: Start Web Interface**
```bash
cd web
npm run dev
```

**Access:** http://localhost:3000

## Docker Deployment

```bash
# Build image
docker build -t jarvis:2.0 .

# Run container
docker run -p 8000:8000 -p 3000:3000 \
  -e ENVIRONMENT=production \
  -e OPENAI_API_KEY=your-key \
  jarvis:2.0
```

## Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

## Cloud Platforms

### Heroku
```bash
heroku create jarvis-2-0
git push heroku main
```

### Railway
- Connect your GitHub repository
- Auto-deploy on push

## Production Configuration

### Environment Variables
```bash
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=postgresql://user:pass@host/db
SECRET_KEY=your-strong-secret-key
CORS_ORIGINS=["https://your-domain.com"]
```

### PostgreSQL Setup
```bash
# Install
sudo apt-get install postgresql

# Create database
sudo -u postgres createdb jarvis
```

### Nginx Reverse Proxy
Configure Nginx to forward requests to the API and web servers.

## Security

- [ ] Use strong SECRET_KEY
- [ ] Enable HTTPS/SSL
- [ ] Configure firewall
- [ ] Set rate limiting
- [ ] Enable audit logging
- [ ] Regular backups
- [ ] Monitor logs
- [ ] Update dependencies

## Monitoring

```bash
# Check logs
tail -f logs/api.log

# Monitor resources
htop

# Database backup
pg_dump jarvis > backup.sql
```

## Support

- **Questions**: Check README.md
- **Issues**: GitHub issues
- **Deployment help**: See DEPLOYMENT.md

---

**Version**: 2.0.0 | **Status**: ✅ Production Ready
