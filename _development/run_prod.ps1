# run_prod.ps1 - Production Startup Script

param(
    [switch]$WithPostgres,
    [switch]$Backup,
    [string]$Port = "8000"
)

Write-Host "🚀 Local Agent v4.0 - Production Startup" -ForegroundColor Cyan
Write-Host "=" -ForegroundColor Cyan -Repeat 60

# Load environment variables
if (Test-Path ".env") {
    Write-Host "📄 Loading .env configuration..." -ForegroundColor Yellow
    Get-Content .env | ForEach-Object {
        if ($_ -match '^([^#][^=]+)=(.*)$') {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
        }
    }
    Write-Host "✅ Environment loaded" -ForegroundColor Green
} else {
    Write-Host "⚠️ .env file not found, using defaults" -ForegroundColor Yellow
}

# Set database type
if ($WithPostgres) {
    [Environment]::SetEnvironmentVariable("DB_TYPE", "postgres", "Process")
    Write-Host "🐘 Using PostgreSQL database" -ForegroundColor Green
    
    # Verify PostgreSQL connection
    $postgresUrl = [Environment]::GetEnvironmentVariable("DATABASE_URL", "Process")
    if (-not $postgresUrl) {
        Write-Host "❌ DATABASE_URL not set for PostgreSQL" -ForegroundColor Red
        exit 1
    }
} else {
    [Environment]::SetEnvironmentVariable("DB_TYPE", "sqlite", "Process")
    Write-Host "📁 Using SQLite database (development mode)" -ForegroundColor Yellow
}

# Create data directories
Write-Host "`n📁 Creating data directories..." -ForegroundColor Yellow
$directories = @("data", "data/backups", "logs", "knowledge_base")
foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "   Created: $dir"
    }
}

# Run backup if requested
if ($Backup) {
    Write-Host "`n💾 Running database backup..." -ForegroundColor Yellow
    python -c "from local_agent.core.db import db_manager; db_manager.backup()"
    Write-Host "✅ Backup complete" -ForegroundColor Green
}

# Check Ollama
Write-Host "`n🤖 Checking Ollama..." -ForegroundColor Yellow
$ollamaRunning = $false
try {
    $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -UseBasicParsing -TimeoutSec 2
    if ($response.StatusCode -eq 200) {
        $ollamaRunning = $true
        Write-Host "✅ Ollama is running" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️ Ollama not running. Starting..." -ForegroundColor Yellow
    Start-Process -NoNewWindow -FilePath "ollama" -ArgumentList "serve"
    Start-Sleep -Seconds 3
}

# Start the server
Write-Host "`n🚀 Starting Local Agent v4.0 on port $Port..." -ForegroundColor Cyan
Write-Host "=" -ForegroundColor Cyan -Repeat 60

python -m local_agent.web.app --port $Port
