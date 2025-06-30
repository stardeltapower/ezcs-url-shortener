#!/bin/bash

# URL Shortener Deployment Script
# This script helps deploy the URL shortener using environment variables

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 URL Shortener Deployment Script${NC}"
echo "=================================="

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ Error: .env file not found!${NC}"
    echo "Please create a .env file based on env.example"
    exit 1
fi

# Load environment variables
source .env

# Check required variables
if [ -z "$DOMAIN" ]; then
    echo -e "${RED}❌ Error: DOMAIN not set in .env file${NC}"
    exit 1
fi

echo -e "${YELLOW}📋 Configuration:${NC}"
echo "Domain: $DOMAIN"
echo "Base URL: $BASE_URL"
echo "Environment: ${ENVIRONMENT:-development}"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check dependencies
echo -e "${YELLOW}🔍 Checking dependencies...${NC}"

if ! command_exists python3; then
    echo -e "${RED}❌ Python 3 not found${NC}"
    exit 1
fi

if ! command_exists nginx; then
    echo -e "${YELLOW}⚠️  Nginx not found - you'll need to install it manually${NC}"
fi

echo -e "${GREEN}✅ Dependencies check completed${NC}"
echo ""

# Setup virtual environment
echo -e "${YELLOW}🐍 Setting up Python environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt

echo -e "${GREEN}✅ Python environment ready${NC}"
echo ""

# Database migrations
echo -e "${YELLOW}🗄️  Running database migrations...${NC}"
alembic upgrade head
echo -e "${GREEN}✅ Database migrations completed${NC}"
echo ""

# Configure Nginx (if available)
if command_exists nginx; then
    echo -e "${YELLOW}🌐 Configuring Nginx...${NC}"

    # Create nginx config with domain substitution
    NGINX_CONFIG="/etc/nginx/sites-available/$DOMAIN"

    if [ -w "/etc/nginx/sites-available" ]; then
        # Replace YOUR_DOMAIN with actual domain
        sed "s/YOUR_DOMAIN/$DOMAIN/g" deployment/nginx-site.conf > "$NGINX_CONFIG"

        # Enable site
        ln -sf "$NGINX_CONFIG" "/etc/nginx/sites-enabled/$DOMAIN"

        # Test nginx config
        if nginx -t 2>/dev/null; then
            systemctl reload nginx
            echo -e "${GREEN}✅ Nginx configured successfully${NC}"
        else
            echo -e "${RED}❌ Nginx configuration error${NC}"
            echo "Please check the configuration manually"
        fi
    else
        echo -e "${YELLOW}⚠️  No write permission to /etc/nginx/sites-available${NC}"
        echo "Please run as sudo or configure nginx manually:"
        echo "sudo sed 's/YOUR_DOMAIN/$DOMAIN/g' deployment/nginx-site.conf > /etc/nginx/sites-available/$DOMAIN"
    fi
else
    echo -e "${YELLOW}⚠️  Nginx not found - skipping web server configuration${NC}"
fi

echo ""

# Setup systemd service (if possible)
if [ -w "/etc/systemd/system" ]; then
    echo -e "${YELLOW}⚙️  Setting up systemd service...${NC}"
    cp deployment/url-shortener.service /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable url-shortener
    systemctl start url-shortener
    echo -e "${GREEN}✅ Systemd service configured${NC}"
else
    echo -e "${YELLOW}⚠️  No permission to configure systemd service${NC}"
    echo "Please run as sudo or setup service manually:"
    echo "sudo cp deployment/url-shortener.service /etc/systemd/system/"
    echo "sudo systemctl daemon-reload && sudo systemctl enable url-shortener"
fi

echo ""
echo -e "${GREEN}🎉 Deployment completed!${NC}"
echo ""
echo -e "${YELLOW}📝 Next steps:${NC}"

if command_exists nginx; then
    echo "1. 🔐 Setup SSL certificate: sudo certbot --nginx -d $DOMAIN"
else
    echo "1. 🌐 Install and configure nginx"
    echo "2. 🔐 Setup SSL certificate"
fi

echo "3. 🔑 Test API key creation:"
echo "   curl -X POST http://localhost:8000/api/admin/keys/ \\"
echo "        -H 'X-Admin-Token: your-admin-token' \\"
echo "        -H 'Content-Type: application/json' \\"
echo "        -d '{\"name\": \"Test Key\"}'"

echo ""
echo "4. 📊 Monitor the service:"
echo "   sudo journalctl -u url-shortener -f"

echo ""
echo -e "${GREEN}✨ Your URL shortener should now be running at: $BASE_URL${NC}"
