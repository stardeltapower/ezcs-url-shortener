# URL Shortener Deployment Script for Windows
# This script helps deploy the URL shortener using environment variables

param(
    [switch]$SkipVenv = $false,
    [switch]$SkipInstall = $false
)

# Colors for output
function Write-ColorText {
    param(
        [string]$Text,
        [string]$Color = "White"
    )
    Write-Host $Text -ForegroundColor $Color
}

Write-ColorText "🚀 URL Shortener Deployment Script (Windows)" "Green"
Write-ColorText "=============================================" "Green"

# Check if .env file exists
if (!(Test-Path ".env")) {
    Write-ColorText "❌ Error: .env file not found!" "Red"
    Write-ColorText "Please create a .env file based on env.example" "Yellow"
    exit 1
}

# Load environment variables from .env file
Write-ColorText "📋 Loading configuration..." "Yellow"
Get-Content ".env" | Where-Object { $_ -match "^[^#].*=" } | ForEach-Object {
    $name, $value = $_ -split "=", 2
    $value = $value.Trim('"').Trim("'")
    [Environment]::SetEnvironmentVariable($name, $value, "Process")
}

$DOMAIN = $env:DOMAIN
$BASE_URL = $env:BASE_URL
$ENVIRONMENT = $env:ENVIRONMENT

if (-not $DOMAIN) {
    Write-ColorText "❌ Error: DOMAIN not set in .env file" "Red"
    exit 1
}

Write-ColorText "Configuration:" "Yellow"
Write-ColorText "Domain: $DOMAIN" "White"
Write-ColorText "Base URL: $BASE_URL" "White"
Write-ColorText "Environment: $($ENVIRONMENT ?? 'development')" "White"
Write-Host ""

# Check Python
Write-ColorText "🔍 Checking dependencies..." "Yellow"
try {
    $pythonVersion = python --version 2>&1
    Write-ColorText "✅ Python found: $pythonVersion" "Green"
} catch {
    Write-ColorText "❌ Python not found. Please install Python 3.8+" "Red"
    exit 1
}

# Setup virtual environment
if (-not $SkipVenv) {
    Write-ColorText "🐍 Setting up Python virtual environment..." "Yellow"

    if (!(Test-Path "venv")) {
        python -m venv venv
    }

    # Activate virtual environment
    if (Test-Path "venv\Scripts\Activate.ps1") {
        & "venv\Scripts\Activate.ps1"
        Write-ColorText "✅ Virtual environment activated" "Green"
    } else {
        Write-ColorText "⚠️  Could not activate virtual environment" "Yellow"
    }
}

# Install dependencies
if (-not $SkipInstall) {
    Write-ColorText "📦 Installing Python dependencies..." "Yellow"
    pip install -r requirements.txt
    Write-ColorText "✅ Dependencies installed" "Green"
}

Write-Host ""

# Database migrations
Write-ColorText "🗄️  Running database migrations..." "Yellow"
try {
    alembic upgrade head
    Write-ColorText "✅ Database migrations completed" "Green"
} catch {
    Write-ColorText "❌ Database migration failed: $_" "Red"
    Write-ColorText "Please check your DATABASE_URL in .env" "Yellow"
}

Write-Host ""

# Create nginx config template (for manual deployment)
Write-ColorText "🌐 Creating nginx configuration..." "Yellow"
if (Test-Path "deployment\nginx-site.conf") {
    $nginxContent = Get-Content "deployment\nginx-site.conf" -Raw
    $nginxConfigured = $nginxContent -replace "YOUR_DOMAIN", $DOMAIN

    $outputFile = "deployment\$DOMAIN.nginx.conf"
    $nginxConfigured | Out-File -FilePath $outputFile -Encoding UTF8

    Write-ColorText "✅ Nginx config created: $outputFile" "Green"
    Write-ColorText "   Copy this to your nginx sites-available directory" "Yellow"
} else {
    Write-ColorText "⚠️  Nginx template not found" "Yellow"
}

Write-Host ""

# Test the application
Write-ColorText "🧪 Testing application..." "Yellow"
try {
    $testResult = python -m pytest tests/ -q --tb=no 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-ColorText "✅ All tests passed" "Green"
    } else {
        Write-ColorText "⚠️  Some tests failed - check configuration" "Yellow"
    }
} catch {
    Write-ColorText "⚠️  Could not run tests" "Yellow"
}

Write-Host ""
Write-ColorText "🎉 Deployment preparation completed!" "Green"
Write-Host ""

Write-ColorText "📝 Next steps:" "Yellow"
Write-ColorText "1. 🚀 Start the development server:" "White"
Write-ColorText "   python run.py" "Cyan"
Write-Host ""

Write-ColorText "2. 🌐 For production deployment:" "White"
Write-ColorText "   - Copy files to your Linux server" "White"
Write-ColorText "   - Use the generated nginx config: deployment\$DOMAIN.nginx.conf" "White"
Write-ColorText "   - Run the Linux deployment script: ./scripts/deploy.sh" "White"
Write-Host ""

Write-ColorText "3. 🔑 Test API key creation:" "White"
Write-ColorText "   Invoke-RestMethod -Uri 'http://localhost:8000/api/admin/keys/' \" "Cyan"
Write-ColorText "     -Method POST \" "Cyan"
Write-ColorText "     -Headers @{'X-Admin-Token'='your-admin-token'; 'Content-Type'='application/json'} \" "Cyan"
Write-ColorText "     -Body '{\"name\": \"Test Key\"}'" "Cyan"
Write-Host ""

Write-ColorText "4. 📊 Open API documentation:" "White"
Write-ColorText "   http://localhost:8000/docs" "Cyan"
Write-Host ""

Write-ColorText "✨ Your URL shortener is ready!" "Green"
if ($BASE_URL) {
    Write-ColorText "🌟 Production URL will be: $BASE_URL" "Green"
}
