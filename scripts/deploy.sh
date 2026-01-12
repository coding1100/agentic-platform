#!/bin/bash

# Deployment script for Agentic Platform
# This script can be run manually on the VPS or called by CI/CD

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration (can be overridden by environment variables)
DEPLOY_PATH=${DEPLOY_PATH:-/var/www/agentic-platform}
BACKEND_PORT=${BACKEND_PORT:-8009}
FRONTEND_DIST=${FRONTEND_DIST:-/var/www/agentic-platform-frontend}

echo -e "${GREEN}Starting deployment...${NC}"

# Navigate to deployment directory
cd "$DEPLOY_PATH"

# Pull latest code
echo -e "${YELLOW}Pulling latest code...${NC}"
git fetch origin
git reset --hard origin/main

# Deploy Backend
if [ -d "backend" ]; then
  echo -e "${YELLOW}Deploying backend...${NC}"
  cd backend
  
  # Create virtual environment if it doesn't exist
  if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating Python virtual environment...${NC}"
    python3 -m venv venv
  fi
  
  # Activate virtual environment
  source venv/bin/activate
  
  # Install/update dependencies
  echo -e "${YELLOW}Installing Python dependencies...${NC}"
  pip install --upgrade pip
  pip install -r requirements.txt
  
  # Ensure database is running
  echo -e "${YELLOW}Checking database container...${NC}"
  cd "$DEPLOY_PATH/docker"
  docker-compose -f docker-compose.prod.yml up -d || docker compose -f docker-compose.prod.yml up -d
  cd "$DEPLOY_PATH/backend"
  
  # Wait for database to be ready
  sleep 3
  
  # Run database migrations
  echo -e "${YELLOW}Running database migrations...${NC}"
  alembic upgrade head
  
  # Restart backend service
  echo -e "${YELLOW}Restarting backend service...${NC}"
  sudo systemctl restart agentic-platform-backend || echo -e "${RED}Warning: Could not restart backend service${NC}"
  
  cd ..
fi

# Deploy Frontend
if [ -d "frontend" ]; then
  echo -e "${YELLOW}Deploying frontend...${NC}"
  cd frontend
  
  # Install dependencies
  echo -e "${YELLOW}Installing Node.js dependencies...${NC}"
  npm ci
  
  # Build frontend (with production API URL if .env exists)
  echo -e "${YELLOW}Building frontend...${NC}"
  if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
  fi
  npm run build
  
  # Copy build to nginx directory
  echo -e "${YELLOW}Copying frontend build to web directory...${NC}"
  sudo mkdir -p "$FRONTEND_DIST"
  sudo rm -rf "$FRONTEND_DIST"/*
  sudo cp -r dist/* "$FRONTEND_DIST"/
  sudo chown -R www-data:www-data "$FRONTEND_DIST"
  
  cd ..
fi

# Reload nginx
echo -e "${YELLOW}Reloading Nginx...${NC}"
sudo systemctl reload nginx || echo -e "${RED}Warning: Could not reload Nginx${NC}"

# Health check
echo -e "${YELLOW}Running health check...${NC}"
sleep 5
if curl -f http://localhost:$BACKEND_PORT/health > /dev/null 2>&1; then
  echo -e "${GREEN}✓ Backend health check passed!${NC}"
else
  echo -e "${RED}✗ Backend health check failed!${NC}"
  exit 1
fi

echo -e "${GREEN}Deployment completed successfully!${NC}"

