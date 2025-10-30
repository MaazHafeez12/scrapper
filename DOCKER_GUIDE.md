# 🐳 Docker Deployment Guide

Complete guide for deploying Job Scraper Platform with Docker.

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Prerequisites](#prerequisites)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Services](#services)
- [Management](#management)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

### One-Command Deploy

```bash
# Clone and start
docker-compose up -d

# Open browser
http://localhost:5000
```

### Stop All Services

```bash
docker-compose down
```

---

## Prerequisites

### Install Docker

**Windows:**
1. Download [Docker Desktop](https://www.docker.com/products/docker-desktop)
2. Install and restart
3. Verify: `docker --version`

**Linux:**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

**Mac:**
1. Download [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop)
2. Install and start
3. Verify: `docker --version`

### Install Docker Compose

Usually included with Docker Desktop. Verify:
```bash
docker-compose --version
```

---

## Configuration

### 1. Environment Setup

Create `.env` file:
```bash
# Copy example
cp .env.example .env

# Edit configuration
nano .env
```

**Required Variables:**
```env
# Flask
FLASK_SECRET_KEY=your-secret-key-here
FLASK_ENV=production

# Database
DATABASE_PATH=/app/data/jobs.db

# API Keys (optional)
OPENAI_API_KEY=your-api-key
ANTHROPIC_API_KEY=your-api-key

# Email (optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_RECIPIENT=your-email@gmail.com

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
```

### 2. Docker Compose Profiles

**Development (default):**
```bash
docker-compose up
```
Includes: app, worker, redis

**Production:**
```bash
docker-compose --profile production up
```
Includes: app, worker, redis, nginx, adminer

**Minimal:**
```bash
docker-compose up app redis
```
Only core services

---

## Deployment

### Development Mode

```bash
# Build and start
docker-compose up --build

# Or detached
docker-compose up -d --build

# View logs
docker-compose logs -f
```

**Access:**
- App: http://localhost:5000
- Redis: localhost:6379

### Production Mode

```bash
# Start with production profile
docker-compose --profile production up -d --build

# View logs
docker-compose logs -f app worker
```

**Access:**
- App: http://localhost (via Nginx)
- App Direct: http://localhost:5000
- Adminer: http://localhost:8080
- Redis: localhost:6379

### Custom Build

```bash
# Build only
docker-compose build

# Build specific service
docker-compose build app

# No cache build
docker-compose build --no-cache
```

---

## Services

### Main App (Flask)

**Container:** `job-scraper-app`
**Port:** 5000
**Purpose:** Web interface and API

**Volumes:**
- `./data:/app/data` - Database persistence
- `./logs:/app/logs` - Log files
- `./.env:/app/.env` - Configuration

**Health Check:** HTTP GET on /

### Worker (Scheduled Scraping)

**Container:** `job-scraper-worker`
**Purpose:** Automated job scraping every 6 hours

**Schedule:**
1. Scrapes Indeed, LinkedIn, RemoteOK
2. Runs AI recommendations (>75% match)
3. Sleeps 6 hours
4. Repeats

**Customize Schedule:**
Edit `docker-compose.yml`:
```yaml
command: >
  sh -c "while true; do
    python main.py --scrape 'your keywords';
    sleep 3600;  # 1 hour
  done"
```

### Redis (Caching)

**Container:** `job-scraper-redis`
**Port:** 6379
**Purpose:** Caching, rate limiting, session storage

**Configuration:**
- Max memory: 256MB
- Policy: allkeys-lru (evict oldest)
- Persistence: AOF enabled

### Adminer (Database Admin)

**Container:** `job-scraper-adminer`
**Port:** 8080
**Purpose:** SQLite database viewer

**Usage:**
1. Open http://localhost:8080
2. System: SQLite 3
3. Database: `/app/data/jobs.db`
4. No username/password needed

### Nginx (Reverse Proxy)

**Container:** `job-scraper-nginx`
**Ports:** 80, 443
**Purpose:** Load balancing, SSL termination

**Enable:**
```bash
docker-compose --profile production up nginx
```

**Custom Config:**
Create `nginx.conf` and mount it.

---

## Management

### Start/Stop

```bash
# Start all
docker-compose up -d

# Start specific
docker-compose up -d app redis

# Stop all
docker-compose stop

# Stop specific
docker-compose stop worker

# Restart
docker-compose restart app
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f app

# Last 100 lines
docker-compose logs --tail=100 app

# Since timestamp
docker-compose logs --since 2025-10-30T10:00:00
```

### Execute Commands

```bash
# Run CLI in app container
docker-compose exec app python main.py --stats

# Scrape jobs
docker-compose exec app python main.py --scrape "python" --location "Remote"

# AI recommendations
docker-compose exec app python main.py --ai-recommend

# Analytics
docker-compose exec app python main.py --analytics

# Shell access
docker-compose exec app sh

# Root shell
docker-compose exec -u root app sh
```

### Database Management

```bash
# Backup database
docker-compose exec app cp /app/data/jobs.db /app/data/jobs_backup.db

# Copy from container
docker cp job-scraper-app:/app/data/jobs.db ./backup.db

# Copy to container
docker cp ./backup.db job-scraper-app:/app/data/jobs.db

# Restore
docker-compose exec app cp /app/data/jobs_backup.db /app/data/jobs.db
docker-compose restart app
```

### Update Application

```bash
# Pull changes
git pull

# Rebuild and restart
docker-compose down
docker-compose up -d --build

# Or rolling update
docker-compose up -d --build --no-deps app
```

### Scale Workers

```bash
# Run 3 worker instances
docker-compose up -d --scale worker=3

# Back to 1
docker-compose up -d --scale worker=1
```

---

## Monitoring

### Container Status

```bash
# List containers
docker-compose ps

# Detailed info
docker-compose ps -a

# Resource usage
docker stats job-scraper-app job-scraper-worker
```

### Health Checks

```bash
# Check app health
curl http://localhost:5000/

# Check Redis
docker-compose exec redis redis-cli ping

# Full diagnostics
docker-compose exec app python -c "from database import JobDatabase; db = JobDatabase(); print(db.get_stats())"
```

### Logs Analysis

```bash
# Error logs only
docker-compose logs app | grep ERROR

# Access patterns
docker-compose logs app | grep "GET /"

# Worker activity
docker-compose logs worker | grep "Found.*jobs"
```

---

## Backup & Restore

### Full Backup

```bash
# Create backup script
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./backups/$DATE"

mkdir -p "$BACKUP_DIR"

# Backup database
docker cp job-scraper-app:/app/data/jobs.db "$BACKUP_DIR/jobs.db"

# Backup logs
docker cp job-scraper-app:/app/logs "$BACKUP_DIR/logs"

# Backup .env
cp .env "$BACKUP_DIR/.env"

echo "Backup created: $BACKUP_DIR"
EOF

chmod +x backup.sh
./backup.sh
```

### Restore

```bash
# Restore database
docker cp ./backups/20251030_120000/jobs.db job-scraper-app:/app/data/jobs.db

# Restart app
docker-compose restart app
```

### Automated Backups

Add to crontab:
```bash
# Backup daily at 2 AM
0 2 * * * cd /path/to/job-scraper && ./backup.sh
```

---

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 5000
netstat -ano | findstr :5000  # Windows
lsof -i :5000                 # Linux/Mac

# Use different port
docker-compose up -p 5001:5000
```

### Container Won't Start

```bash
# Check logs
docker-compose logs app

# Check configuration
docker-compose config

# Rebuild from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up
```

### Database Locked

```bash
# Stop all containers
docker-compose down

# Remove database lock
rm ./data/jobs.db-journal

# Restart
docker-compose up -d
```

### Out of Memory

```bash
# Check usage
docker stats

# Increase Redis memory
# Edit docker-compose.yml
command: redis-server --maxmemory 512mb

# Restart
docker-compose restart redis
```

### Slow Performance

```bash
# Check resources
docker stats

# Scale down worker
docker-compose stop worker

# Clear Redis cache
docker-compose exec redis redis-cli FLUSHALL

# Vacuum database
docker-compose exec app python -c "from database import JobDatabase; db = JobDatabase(); db.conn.execute('VACUUM')"
```

### Network Issues

```bash
# Check network
docker network ls
docker network inspect job-scraper_job-scraper-network

# Recreate network
docker-compose down
docker network prune
docker-compose up
```

### Can't Connect to Services

```bash
# Check if running
docker-compose ps

# Check ports
docker-compose port app 5000
docker-compose port redis 6379

# Test connectivity
docker-compose exec app ping redis
```

---

## Production Deployment

### SSL with Let's Encrypt

1. **Install Certbot:**
```bash
sudo apt-get install certbot
```

2. **Get Certificate:**
```bash
sudo certbot certonly --standalone -d yourdomain.com
```

3. **Mount in Nginx:**
```yaml
volumes:
  - /etc/letsencrypt:/etc/letsencrypt:ro
```

4. **Auto-renewal:**
```bash
# Add to crontab
0 0 * * * certbot renew --quiet
```

### Environment Variables

Use Docker secrets for production:
```yaml
secrets:
  openai_key:
    external: true

services:
  app:
    secrets:
      - openai_key
```

### Monitoring

Add Prometheus & Grafana:
```yaml
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
```

---

## Cleanup

### Remove Containers

```bash
# Stop and remove
docker-compose down

# Remove volumes too
docker-compose down -v

# Remove images
docker-compose down --rmi all
```

### Prune System

```bash
# Remove unused containers
docker container prune

# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Full cleanup
docker system prune -a --volumes
```

---

## Summary

✅ **Quick Commands:**
```bash
# Start
docker-compose up -d

# Logs
docker-compose logs -f app

# Execute command
docker-compose exec app python main.py --stats

# Stop
docker-compose down
```

🔥 **Production:**
```bash
docker-compose --profile production up -d
```

📊 **Monitor:**
```bash
docker stats
docker-compose logs -f
```

🔧 **Troubleshoot:**
```bash
docker-compose logs app
docker-compose exec app sh
```

---

**Happy Docker deployment! 🐳✨**
