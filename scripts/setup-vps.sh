#!/bin/bash

# Initial VPS setup script
# Run this once on your VPS to set up the environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Setting up VPS for Agentic Platform deployment...${NC}"

# Update system
echo -e "${YELLOW}Updating system packages...${NC}"
sudo apt-get update
sudo apt-get upgrade -y

# Install required packages
echo -e "${YELLOW}Installing required packages...${NC}"
sudo apt-get install -y \
  python3 \
  python3-pip \
  python3-venv \
  nodejs \
  npm \
  nginx \
  docker.io \
  docker-compose \
  git \
  curl \
  certbot \
  python3-certbot-nginx

# Start Docker service
echo -e "${YELLOW}Starting Docker service...${NC}"
sudo systemctl start docker
sudo systemctl enable docker

# Install Node.js 18+ if not available
if ! command -v node &> /dev/null || [ "$(node -v | cut -d'v' -f2 | cut -d'.' -f1)" -lt 18 ]; then
  echo -e "${YELLOW}Installing Node.js 18...${NC}"
  curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
  sudo apt-get install -y nodejs
fi

# Create deployment directory
DEPLOY_PATH=${DEPLOY_PATH:-/var/www/agentic-platform}
echo -e "${YELLOW}Creating deployment directory at $DEPLOY_PATH...${NC}"
sudo mkdir -p "$DEPLOY_PATH"
sudo chown -R $USER:$USER "$DEPLOY_PATH"

# Create frontend web directory
FRONTEND_DIST=${FRONTEND_DIST:-/var/www/agentic-platform-frontend}
echo -e "${YELLOW}Creating frontend web directory at $FRONTEND_DIST...${NC}"
sudo mkdir -p "$FRONTEND_DIST"
sudo chown -R www-data:www-data "$FRONTEND_DIST"

# Clone repository (if not already cloned)
if [ ! -d "$DEPLOY_PATH/.git" ]; then
  echo -e "${YELLOW}Please clone your repository to $DEPLOY_PATH${NC}"
  echo -e "${YELLOW}Example: git clone https://github.com/yourusername/agentic-platform.git $DEPLOY_PATH${NC}"
fi

# Setup PostgreSQL with Docker
echo -e "${YELLOW}PostgreSQL will be set up using Docker Compose${NC}"
echo -e "${YELLOW}After cloning the repository, run:${NC}"
echo -e "${YELLOW}cd docker && docker-compose -f docker-compose.prod.yml up -d${NC}"

# Create systemd service file
echo -e "${YELLOW}Creating systemd service file...${NC}"
sudo tee /etc/systemd/system/agentic-platform-backend.service > /dev/null <<EOF
[Unit]
Description=Agentic Platform Backend API
After=network.target postgresql.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$DEPLOY_PATH/backend
Environment="PATH=$DEPLOY_PATH/backend/venv/bin"
ExecStart=$DEPLOY_PATH/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8009
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
sudo systemctl daemon-reload

echo -e "${GREEN}VPS setup completed!${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo -e "1. Clone your repository to $DEPLOY_PATH"
echo -e "2. Create PostgreSQL database and user"
echo -e "3. Create .env file in backend directory with your configuration"
echo -e "4. Run: sudo systemctl enable agentic-platform-backend"
echo -e "5. Run: sudo systemctl start agentic-platform-backend"
echo -e "6. Configure Nginx (see nginx/agentic-platform.conf)"
echo -e "7. Set up SSL with certbot: sudo certbot --nginx -d agentic-platform.namatechnologlies.com"

