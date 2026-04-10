# install.ps1 - Windows PowerShell script for Local Agent v4.0

Write-Host "🚀 Installing Local Agent v4.0..." -ForegroundColor Cyan

# Check for Python
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "❌ Python not found. Please install Python 3.10+."
    exit
}

# Check for Node.js (required for frontend)
if (!(Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Warning "⚠️ npm not found. Frontend will not be built automatically."
}

# Create virtual environment
Write-Host "📦 Creating virtual environment..." -ForegroundColor Yellow
python -m venv venv
.\venv\Scripts\activate

# Install Python dependencies
Write-Host "📦 Installing Python dependencies..." -ForegroundColor Yellow
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Install frontend dependencies (if npm available)
if (Get-Command npm -ErrorAction SilentlyContinue) {
    Write-Host "📦 Installing frontend dependencies..." -ForegroundColor Yellow
    cd frontend
    npm install
    npm run build
    cd ..

    # Copy frontend build to static directory
    Write-Host "📁 Copying frontend build..." -ForegroundColor Yellow
    if (!(Test-Path local_agent/web/static)) {
        New-Item -ItemType Directory -Path local_agent/web/static -Force
    }
    Copy-Item -Path frontend/dist/* -Destination local_agent/web/static/ -Recurse -Force
}

# Create .env file
Write-Host "📝 Creating .env file..." -ForegroundColor Yellow
if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
}

Write-Host "`n✅ Installation complete!" -ForegroundColor Green
Write-Host "`n🚀 Start the agent with:" -ForegroundColor Cyan
Write-Host "   .\venv\Scripts\activate" -ForegroundColor White
Write-Host "   python -m local_agent.web.app" -ForegroundColor White
Write-Host "`n🌐 Open browser to: http://localhost:8000" -ForegroundColor White
