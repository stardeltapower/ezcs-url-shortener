# Deployment Guide for ezcs URL Shortener

This directory contains deployment configurations for the ezcs URL Shortener application.

## Files

- `nginx-site.conf` - Nginx configuration template
- `url-shortener.service` - Systemd service file
- `README.md` - This file

## Configuration

### 1. Environment Variables

Create a `.env` file in the project root with your configuration:

```bash
# Database Configuration
DATABASE_URL=mysql+pymysql://username:password@localhost/url_shortener_db

# Security (Generate strong random strings)
SECRET_KEY=your-secret-key-here-use-a-long-random-string
ADMIN_TOKEN=your-admin-token-here-use-a-long-random-string

# URL Shortener Configuration
SHORT_URL_LENGTH=6
BASE_URL=https://yourdomain.com
REDIRECT_URL=https://yourcompany.com

# Deployment Configuration
DOMAIN=yourdomain.com

# Optional
ENVIRONMENT=production
```

### 2. Nginx Configuration

The `nginx-site.conf` file contains placeholders that need to be replaced with your actual domain:

- Replace `YOUR_DOMAIN` with your actual domain name (e.g., `ezcs.to`)
- Update SSL certificate paths if using HTTPS

**Option A: Manual replacement**
```bash
# Copy and customize the nginx config
cp deployment/nginx-site.conf /etc/nginx/sites-available/your-domain
sed -i 's/YOUR_DOMAIN/yourdomain.com/g' /etc/nginx/sites-available/your-domain
```

**Option B: Using environment variable**
```bash
# Use the DOMAIN from .env file
source .env
envsubst '${DOMAIN}' < deployment/nginx-site.conf > /etc/nginx/sites-available/${DOMAIN}
```

### 3. SystemD Service

The `url-shortener.service` file can be used as-is:

```bash
# Copy service file
sudo cp deployment/url-shortener.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable url-shortener
sudo systemctl start url-shortener
```

### 4. Complete Manual Deployment

```bash
# 1. Clone/copy project files
git clone https://github.com/rsmith/ezcs-url-shortener.git /var/www/url-shortener
cd /var/www/url-shortener

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Configure environment
cp env.example .env
# Edit .env with your actual values

# 4. Set up database
alembic upgrade head

# 5. Configure nginx
source .env
envsubst '${DOMAIN}' < deployment/nginx-site.conf > /etc/nginx/sites-available/${DOMAIN}
ln -s /etc/nginx/sites-available/${DOMAIN} /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

# 6. Set up systemd service
sudo cp deployment/url-shortener.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable url-shortener
sudo systemctl start url-shortener
```

### 5. GitHub Actions (Optional)

If you want to use automated deployment, the GitHub Actions workflow will use these secrets:
- `VPS_HOST` - Your server IP/hostname
- `VPS_USER` - SSH username
- `VPS_SSH_KEY` - SSH private key
- `VPS_PORT` - SSH port (usually 22)

The workflow will automatically deploy to `/var/www/url-shortener` and can use the DOMAIN variable from your server's `.env` file.

## SSL Configuration

For HTTPS, you'll need SSL certificates. With Let's Encrypt:

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificates (replace with your domain)
sudo certbot --nginx -d yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## Security Notes

- Always use strong, unique values for `SECRET_KEY` and `ADMIN_TOKEN`
- Keep your `.env` file secure and never commit it to version control
- Regularly update dependencies: `pip install -r requirements.txt --upgrade`
- Monitor logs: `journalctl -u url-shortener -f`
