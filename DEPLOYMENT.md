# Deployment Guide

Complete guide for deploying Agentic Platform to your VPS using Docker Compose.

## Your Configuration

- **Subdomain:** `agentic-platform.namatechnologlies.com`
- **VPS IP:** `148.230.93.34`
- **VPS Username:** `root`
- **Frontend URL:** `https://agentic-platform.namatechnologlies.com`
- **Backend API:** `https://agentic-platform.namatechnologlies.com/api`

## Prerequisites

- Ubuntu/Debian VPS
- SSH access to your VPS
- Domain name with DNS configured
- GitHub repository

## Deployment Path

**You can deploy to any directory on your VPS.** Common choices:
- `/var/www/agentic-platform` - Traditional web directory (used in examples)
- `/opt/agentic-platform` - Application directory
- `/home/youruser/agentic-platform` - User directory
- Any other path you prefer

**Important:** With Docker Compose, the location is flexible since everything runs in containers. Just ensure you:
1. Use the same path consistently
2. Set the `DEPLOY_PATH` secret in GitHub Actions to match your chosen path
3. Have appropriate permissions for the directory

## Step 1: Initial VPS Setup

### 1.1 Connect to VPS

```bash
ssh root@148.230.93.34
```

### 1.2 Install Docker and Docker Compose

```bash
# Update system
apt-get update && apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose (if not included)
apt-get install -y docker-compose-plugin

# Or install standalone docker-compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

### 1.3 Clone Repository

You can clone the repository to any directory you prefer. Common locations:
- `/var/www/agentic-platform` (traditional web directory)
- `/opt/agentic-platform` (application directory)
- `/home/youruser/agentic-platform` (user directory)
- Any other path you prefer

**Example using `/var/www/agentic-platform`:**
```bash
cd /var/www
git clone https://github.com/yourusername/agentic-platform.git agentic-platform
cd agentic-platform
```

**Note:** With Docker Compose, the location doesn't matter much since everything runs in containers. Just make sure to use the same path consistently in your GitHub secrets and deployment scripts.

## Step 2: Environment Configuration

### 2.1 Create Environment File

```bash
# Navigate to your cloned repository directory
cd /var/www/agentic-platform  # or wherever you cloned it
cp .env.example .env
nano .env
```

Update the `.env` file with your values:

```env
# PostgreSQL
POSTGRES_USER=agentic_user
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=agentic_platform
POSTGRES_PORT=5432

# Backend
SECRET_KEY=your-super-secret-key-generate-with-python-secrets-token_urlsafe-32
GEMINI_API_KEY=your-gemini-api-key
CORS_ORIGINS=["https://agentic-platform.namatechnologlies.com"]
CORS_ORIGINS_API=["*"]
ACCESS_TOKEN_EXPIRE_MINUTES=10080
BACKEND_PORT=8010

# Frontend
VITE_API_BASE_URL=https://agentic-platform.namatechnologlies.com/api
FRONTEND_PORT=808080
BACKEND_PORT=8010
```

Generate a secure SECRET_KEY:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Step 3: Deploy with Docker Compose

### 3.1 Build and Start Containers

```bash
# Navigate to your repository directory
cd /var/www/agentic-platform  # or your chosen path

# Build and start all services
docker-compose -f docker-compose.prod.yml up -d --build

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

### 3.2 Verify Deployment

```bash
# Check if containers are running
docker ps

# Test backend health
curl http://localhost/api/v1/health

# Check frontend
curl http://localhost
```

## Step 4: Configure Nginx and SSL

### 4.1 Install Nginx (for SSL termination)

```bash
apt-get install -y nginx certbot python3-certbot-nginx
```

### 4.2 Configure Nginx

```bash
# Copy nginx config (adjust path to your repository location)
cp /root/agentic-platform/nginx/agentic-platform.conf /etc/nginx/sites-available/agentic-platform.conf
# Or if you used a different path:
# cp ~/agentic-platform/nginx/agentic-platform.conf /etc/nginx/sites-available/agentic-platform.conf

# Remove any conflicting certbot-created config
rm -f /etc/nginx/sites-enabled/agentic-platform.namatechnologlies.com

# Remove old symlink if it exists
rm -f /etc/nginx/sites-enabled/agentic-platform.conf

# Enable site (create symlink)
ln -s /etc/nginx/sites-available/agentic-platform.conf /etc/nginx/sites-enabled/agentic-platform.conf

# Test configuration
nginx -t

# If test passes, reload nginx
systemctl reload nginx
```

The nginx config file (`nginx/agentic-platform.conf`) includes:
- Complete SSL configuration (for use after certbot setup)
- HTTP to HTTPS redirect
- Proxy configuration for Docker containers

The config proxies:
- `/` → Frontend container (port 8080)
- `/api` → Backend container (port 8010)
- `/health` → Backend health endpoint

```bash
# Enable site
ln -s /etc/nginx/sites-available/agentic-platform /etc/nginx/sites-enabled/

# Test configuration
nginx -t

# Reload nginx
systemctl reload nginx
```

### 4.3 Set Up SSL Certificate (Later)

**Important:** The nginx config file has NO SSL configuration. This is intentional - certbot will add it automatically.

When you're ready to add SSL, run:
```bash
certbot --nginx -d agentic-platform.namatechnologlies.com
```

Certbot will:
1. Automatically detect your nginx configuration
2. Obtain SSL certificates from Let's Encrypt
3. Modify your nginx config to add HTTPS (port 443)
4. Add automatic HTTP to HTTPS redirect
5. Set up certificate auto-renewal

**You don't need to manually edit the nginx config for SSL** - certbot handles everything!

## Step 5: GitHub Actions Configuration

### 5.1 Configure GitHub Secrets

Go to your GitHub repository → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Add these 4 secrets:

1. **VPS_HOST**: `148.230.93.34`
2. **VPS_USER**: `root`
3. **VPS_PASSWORD**: Your VPS root password
4. **DEPLOY_PATH**: The path where you cloned the repository
   - If using `~/agentic-platform` with root user: `/root/agentic-platform`
   - Other common paths: `/var/www/agentic-platform`, `/opt/agentic-platform`

**Note:** Using password authentication is less secure than SSH keys. For better security, consider setting up SSH key authentication later.

## Step 6: Test Deployment

### 6.1 Manual Deployment Test

SSH into your VPS and run:
```bash
# Navigate to your repository directory
cd /root/agentic-platform  # or your chosen path

# Pull latest code
git fetch origin --prune
git checkout main
git pull origin main

# Deploy with Docker Compose
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
```

### 6.2 CI/CD Test

1. Make a small change to your code
2. Commit and push:
   ```bash
   git add .
   git commit -m "Test deployment"
   git push origin main
   ```
3. Go to GitHub → **Actions** tab
4. Watch the deployment workflow run

## Step 7: Verify Deployment

### 7.1 Check Services

```bash
# Check containers
docker ps

# Check logs
docker-compose -f docker-compose.prod.yml logs -f

# Test health endpoint
curl https://agentic-platform.namatechnologlies.com/api/v1/health
```

### 7.2 Visit Frontend

Open `https://agentic-platform.namatechnologlies.com` in your browser

## DNS Configuration

Ensure your DNS has an A record:
```
Type: A
Name: agentic-platform
Value: 148.230.93.34
TTL: 3600 (or default)
```

## Common Docker Commands

### View Logs
```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend
docker-compose -f docker-compose.prod.yml logs -f postgres
```

### Restart Services
```bash
# Restart all
docker-compose -f docker-compose.prod.yml restart

# Restart specific service
docker-compose -f docker-compose.prod.yml restart backend
```

### Stop/Start Services
```bash
# Stop all
docker-compose -f docker-compose.prod.yml stop

# Start all
docker-compose -f docker-compose.prod.yml start

# Stop and remove containers
docker-compose -f docker-compose.prod.yml down

# Stop, remove containers and volumes (⚠️ deletes data)
docker-compose -f docker-compose.prod.yml down -v
```

### Rebuild After Code Changes
```bash
# Rebuild and restart
docker-compose -f docker-compose.prod.yml up -d --build

# Rebuild specific service
docker-compose -f docker-compose.prod.yml build backend
docker-compose -f docker-compose.prod.yml up -d backend
```

## Troubleshooting

### Containers Not Starting

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs

# Check container status
docker ps -a

# Check Docker daemon
systemctl status docker
```

### Database Connection Issues

```bash
# Check database container
docker logs agentic_platform_db

# Test database connection
docker exec -it agentic_platform_db psql -U agentic_user -d agentic_platform

# Restart database
docker-compose -f docker-compose.prod.yml restart postgres
```

### Backend Issues

```bash
# Check backend logs
docker logs agentic_platform_backend

# Restart backend
docker-compose -f docker-compose.prod.yml restart backend

# Rebuild backend
docker-compose -f docker-compose.prod.yml build backend
docker-compose -f docker-compose.prod.yml up -d backend
```

### Frontend Issues

```bash
# Check frontend logs
docker logs agentic_platform_frontend

# Rebuild frontend
docker-compose -f docker-compose.prod.yml build frontend
docker-compose -f docker-compose.prod.yml up -d frontend
```

### Nginx Issues

```bash
# Test nginx config
nginx -t

# Check nginx logs
tail -f /var/log/nginx/error.log
tail -f /var/log/nginx/access.log

# Reload nginx
systemctl reload nginx
```

### CI/CD Deployment Fails

1. Check GitHub Actions logs in the **Actions** tab
2. Verify all secrets are set correctly
3. Test SSH connection manually:
   ```bash
   ssh -i ~/.ssh/deploy_key root@148.230.93.34
   ```
4. Check Docker is running on VPS:
   ```bash
   ssh root@148.230.93.34 "docker ps"
   ```

## Manual Deployment

If CI/CD isn't working, deploy manually:

```bash
ssh root@148.230.93.34
cd /root/agentic-platform  # or your chosen deployment path
git fetch origin --prune
git checkout main
git pull origin main
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
```

## Environment Variables Reference

### Required Variables

- `POSTGRES_USER`: PostgreSQL username
- `POSTGRES_PASSWORD`: PostgreSQL password
- `POSTGRES_DB`: Database name
- `SECRET_KEY`: JWT secret key (use a strong random string)
- `GEMINI_API_KEY`: Google Gemini API key
- `CORS_ORIGINS`: Allowed CORS origins (JSON array)
- `VITE_API_BASE_URL`: Frontend API URL

### Optional Variables

- `POSTGRES_PORT`: PostgreSQL port (default: 5432, internal only in production)
- `BACKEND_PORT`: Backend port mapped to host (default: 8010, to avoid conflict with port 8009)
- `FRONTEND_PORT`: Frontend port mapped to host (default: 8080, to avoid conflict with port 80)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: JWT token expiration (default: 10080)

## Security Checklist

- [ ] Use strong POSTGRES_PASSWORD
- [ ] Use strong SECRET_KEY
- [ ] Set up SSL/HTTPS
- [ ] Configure firewall (UFW)
- [ ] Restrict SSH access (disable password auth, use keys only)
- [ ] Keep Docker images updated
- [ ] Set up log rotation
- [ ] Configure backups

## Firewall Setup (UFW)

```bash
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw enable
```

## Backup Strategy

### Database Backup

```bash
# Manual backup
docker exec agentic_platform_db pg_dump -U agentic_user agentic_platform > backup_$(date +%Y%m%d).sql

# Automated backup (add to crontab)
0 2 * * * docker exec agentic_platform_db pg_dump -U agentic_user agentic_platform > /backups/db_$(date +\%Y\%m\%d).sql
```

### Volume Backup

```bash
# Backup Docker volumes
docker run --rm -v agentic_platform_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data
```

## Important Files

- `docker-compose.prod.yml` - Production Docker Compose configuration
- `docker-compose.yml` - Development Docker Compose configuration
- `backend/Dockerfile` - Backend container definition
- `frontend/Dockerfile` - Frontend container definition
- `.github/workflows/deploy.yml` - CI/CD workflow

## All Set!

Your platform should now be accessible at:
- **Frontend:** https://agentic-platform.namatechnologlies.com
- **Backend API:** https://agentic-platform.namatechnologlies.com/api
- **API Docs:** https://agentic-platform.namatechnologlies.com/api/docs
