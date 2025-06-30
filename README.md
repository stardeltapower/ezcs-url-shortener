# ezcs URL Shortener

A simple, fast URL shortener service built with FastAPI and MySQL/MariaDB. Features API key authentication, custom short URLs, expiration dates, and comprehensive API documentation.

**GitHub Repository**: [ezcs url shortener](https://github.com/rsmith/ezcs-url-shortener)

## Features

- 🔗 **URL Shortening**: Create short URLs with custom or auto-generated codes
- 🔐 **API Key Authentication**: Secure API access with encrypted key storage
- ⏰ **Expiration Support**: Set expiration dates for short URLs
- 📊 **Full CRUD Operations**: Create, read, update, and delete URLs
- 🔄 **Key Management**: Generate, revoke, and reactivate API keys (admin-protected)
- 📖 **Auto-generated Documentation**: Swagger UI and ReDoc interfaces
- 🗄️ **Database Migrations**: Alembic integration for schema management
- 🧪 **Comprehensive Tests**: Full test suite with pytest
- 🔧 **Pre-commit Hooks**: Code quality enforcement with Black and Ruff
- 🌍 **Environment-Aware**: Different behaviors for development vs production

## Quick Start

### 1. Clone and Setup
```bash
git clone <your-repo-url>
cd url-shortener
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp env.example .env
# Edit .env with your configuration
```

### 3. Database Setup
```bash
# Run migrations
alembic upgrade head
```

### 4. Start Development Server
```bash
# Development mode (auto-reload, debug logging, docs enabled)
python run.py

# Or with uvicorn directly
uvicorn app.main:app --reload
```

## Environment Configuration

The `ENVIRONMENT` variable controls different application behaviors:

### 🛠️ **Development Mode** (`ENVIRONMENT=development`)

**Features:**
- ✅ **API Documentation**: Swagger UI at `/docs` and ReDoc at `/redoc`
- ✅ **Debug Mode**: Detailed error messages and stack traces
- ✅ **Verbose Logging**: DEBUG level logging with detailed request info
- ✅ **Auto-reload**: Server restarts automatically on code changes
- ✅ **Permissive CORS**: Allows all origins (`*`) for easy frontend development
- ✅ **OpenAPI Schema**: Available at `/openapi.json`

**Security:**
- ⚠️ **Less Secure**: Error details exposed, CORS wide open
- ⚠️ **Not for Production**: Intended for development only

**Example .env:**
```bash
ENVIRONMENT=development
BASE_URL=http://localhost:8000
DATABASE_URL=sqlite:///./shortener.db  # Simple SQLite for dev
SECRET_KEY=dev-secret-key
ADMIN_TOKEN=dev-admin-token
```

### 🚀 **Production Mode** (`ENVIRONMENT=production`)

**Features:**
- 🔒 **Security First**: API docs disabled, minimal error details
- 📊 **Optimized Logging**: INFO level logging, structured for monitoring
- 🌐 **Strict CORS**: Only allows configured domains
- ⚡ **Performance**: No auto-reload, optimized for stability
- 🛡️ **Hardened**: OpenAPI schema disabled publicly

**Security:**
- ✅ **API Docs Disabled**: `/docs` and `/redoc` return 404
- ✅ **Restricted CORS**: Only allows `BASE_URL` and localhost
- ✅ **Minimal Error Info**: Generic error messages
- ✅ **Structured Logging**: Suitable for log aggregation systems

**Example .env:**
```bash
ENVIRONMENT=production
BASE_URL=https://yourdomain.com
DATABASE_URL=mysql+pymysql://user:pass@localhost/shortener_db
SECRET_KEY=super-secure-random-key-256-bits
ADMIN_TOKEN=admin-token-also-very-secure
DOMAIN=yourdomain.com
```

### 📊 **Environment Comparison**

| Feature | Development | Production |
|---------|-------------|------------|
| **API Documentation** | ✅ Available at `/docs` | ❌ Disabled (404) |
| **Debug Mode** | ✅ Enabled | ❌ Disabled |
| **Logging Level** | `DEBUG` | `INFO` |
| **Auto-reload** | ✅ Enabled | ❌ Disabled |
| **CORS Origins** | `*` (all) | Restricted to domain |
| **Error Details** | ✅ Full stack traces | ❌ Generic messages |
| **OpenAPI Schema** | ✅ Public | ❌ Disabled |
| **Performance** | Slower (dev features) | Optimized |

### 🔧 **Switching Environments**

**Development to Production:**
```bash
# 1. Update .env file
sed -i 's/ENVIRONMENT=development/ENVIRONMENT=production/' .env

# 2. Restart application
systemctl restart url-shortener  # or your process manager
```

**Testing Environment Detection:**
```bash
# Check current environment
curl http://localhost:8000/api/health

# Response includes:
{
  "status": "healthy",
  "environment": "development",  # or "production"
  "debug": true                  # or false
}
```

## Configuration Variables

All configuration is handled through environment variables:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | Database connection string | SQLite file | ✅ |
| `SECRET_KEY` | JWT/session encryption key | Random string | ✅ |
| `ADMIN_TOKEN` | Admin API authentication | Random string | ✅ |
| `BASE_URL` | Your domain (forms short URLs) | `http://localhost:8000` | ✅ |
| `REDIRECT_URL` | Where root path redirects | `https://easycablesizing.com` | ❌ |
| `SHORT_URL_LENGTH` | Length of generated codes | `6` | ❌ |
| `ENVIRONMENT` | Environment (development/production) | `development` | ❌ |
| `DOMAIN` | Domain name for deployment | `localhost` | ❌ |

## Development Workflow

### 🧪 **Testing**
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_urls.py -v
```

### 🔧 **Code Quality**
```bash
# Install pre-commit hooks
pre-commit install

# Run code formatting
black app/ tests/
ruff check app/ tests/

# Manual pre-commit run
pre-commit run --all-files
```

### 📊 **Database Management**
```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Check migration status
alembic current
```

## API Usage

### 🔑 **Admin Operations** (require `X-Admin-Token`)
```bash
# Create API key
curl -X POST http://localhost:8000/api/admin/keys/ \
  -H "X-Admin-Token: your-admin-token" \
  -H "Content-Type: application/json" \
  -d '{"name": "My API Key"}'

# List all API keys
curl -H "X-Admin-Token: your-admin-token" \
  http://localhost:8000/api/admin/keys/
```

### 🌐 **URL Operations** (require `X-API-Key`)
```bash
# Create short URL
curl -X POST http://localhost:8000/api/urls/ \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"original_url": "https://example.com"}'

# Get URL info
curl -H "X-API-Key: your-api-key" \
  http://localhost:8000/api/urls/abc123
```

## Deployment

Choose your deployment method:

### 🚀 **Automated (Linux/macOS)**
```bash
./scripts/deploy.sh
```

### 🖥️ **Manual (Windows)**
```powershell
.\scripts\deploy.ps1
```

### 📋 **Manual Steps**
See [deployment/README.md](deployment/README.md) for detailed instructions.

## Security Considerations

### 🔒 **Production Security**
- Always use `ENVIRONMENT=production` in production
- Generate strong, unique `SECRET_KEY` and `ADMIN_TOKEN`
- Use HTTPS for `BASE_URL` in production
- Regularly rotate API keys
- Monitor logs for suspicious activity
- Keep dependencies updated

### 🛡️ **API Key Management**
- API keys are bcrypt-hashed in database
- Admin token required for key management
- Keys can be revoked/reactivated without deletion
- Each key tracks creation/modification dates

## Monitoring and Logs

### 📊 **Health Check**
```bash
curl http://localhost:8000/api/health
```

### 📋 **Log Monitoring**
```bash
# Development (verbose)
tail -f uvicorn.log

# Production (systemd)
journalctl -u url-shortener -f
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest`
5. Check code quality: `pre-commit run --all-files`
6. Submit a pull request

## License

MIT License - see LICENSE file for details.

---

**Need Help?** Check the [deployment guide](deployment/README.md) or open an issue!
