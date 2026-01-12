#!/bin/bash

# Docker-based deployment script for Agentic Platform
# This script can be run manually on the VPS or called by CI/CD

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration (can be overridden by environment variables)
DEPLOY_PATH=${DEPLOY_PATH:-/var/www/agentic-platform}
COMPOSE_FILE=${COMPOSE_FILE:-docker-compose.prod.yml}

echo -e "${GREEN}Starting Docker-based deployment...${NC}"

# Navigate to deployment directory
cd "$DEPLOY_PATH"

# Pull latest code
echo -e "${YELLOW}Pulling latest code...${NC}"
git fetch origin
git reset --hard origin/main

# Note: .env file will be automatically loaded by docker-compose
# No need to export it here

# Build and start containers
echo -e "${YELLOW}Building and starting containers...${NC}"
docker-compose -f "$COMPOSE_FILE" down
docker-compose -f "$COMPOSE_FILE" build --no-cache
docker-compose -f "$COMPOSE_FILE" up -d

# Wait for services to be ready
echo -e "${YELLOW}Waiting for services to start...${NC}"
sleep 10

# Health check
echo -e "${YELLOW}Running health check...${NC}"
if curl -f http://localhost/health > /dev/null 2>&1 || curl -f http://localhost/api/v1/health > /dev/null 2>&1; then
  echo -e "${GREEN}✓ Health check passed!${NC}"
else
  echo -e "${RED}✗ Health check failed!${NC}"
  echo -e "${YELLOW}Checking container logs...${NC}"
  docker-compose -f "$COMPOSE_FILE" logs --tail=50
  exit 1
fi

# Show running containers
echo -e "${YELLOW}Running containers:${NC}"
docker-compose -f "$COMPOSE_FILE" ps

echo -e "${GREEN}Deployment completed successfully!${NC}"

