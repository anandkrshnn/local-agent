# build_production.ps1 - Complete Production Build Script

param(
    [switch]$SkipFrontend,
    [switch]$SkipDesktop,
    [switch]$SkipMobile
)

Write-Host "🚀 Building Local Agent v4.0 for Production" -ForegroundColor Cyan
Write-Host "=" * 60

# Error handling
$ErrorActionPreference = "Stop"

# 1. Build Frontend
if (-not $SkipFrontend) {
    Write-Host "`n📦 Building React Frontend..." -ForegroundColor Yellow
    
    if (Test-Path "frontend") {
        Push-Location frontend
        
        # Install dependencies if node_modules missing
        if (-not (Test-Path "node_modules")) {
            Write-Host "   Installing npm dependencies..." -ForegroundColor Yellow
            npm install
        }
        
        # Build frontend
        Write-Host "   Running npm run build..." -ForegroundColor Yellow
        npm run build
        
        if (Test-Path "dist") {
            Write-Host "✅ Frontend built: frontend/dist/ ($(Get-ChildItem dist -Recurse | Measure-Object -Property Length -Sum | Select-Object -ExpandProperty Sum) bytes)" -ForegroundColor Green
        } else {
            throw "Frontend build failed - dist folder not created"
        }
        
        Pop-Location
    } else {
        Write-Host "⚠️ Frontend directory not found, skipping..." -ForegroundColor Yellow
    }
}

# 2. Build Desktop App
if (-not $SkipDesktop) {
    Write-Host "`n💻 Building Desktop App..." -ForegroundColor Yellow
    
    if (Test-Path "desktop") {
        Push-Location desktop
        
        # Install dependencies if node_modules missing
        if (-not (Test-Path "node_modules")) {
            Write-Host "   Installing npm dependencies..." -ForegroundColor Yellow
            npm install
        }
        
        # Build for Windows
        Write-Host "   Building for Windows..." -ForegroundColor Yellow
        npm run build:win
        
        if (Test-Path "dist") {
            $exeFiles = Get-ChildItem dist -Filter "*.exe"
            foreach ($exe in $exeFiles) {
                Write-Host "✅ Built: desktop/dist/$($exe.Name) ($([math]::Round($exe.Length/1MB, 2)) MB)" -ForegroundColor Green
            }
        }
        
        Pop-Location
    } else {
        Write-Host "⚠️ Desktop directory not found, skipping..." -ForegroundColor Yellow
    }
}

# 3. Build Mobile (Android)
if (-not $SkipMobile) {
    Write-Host "`n📱 Building Android APK..." -ForegroundColor Yellow
    
    if (Test-Path "mobile/android") {
        Push-Location mobile/android
        
        Write-Host "   Running Gradle assembleRelease..." -ForegroundColor Yellow
        
        # Check if gradlew exists
        if (Test-Path "gradlew.bat") {
            .\gradlew.bat assembleRelease
        } elseif (Test-Path "gradlew") {
            chmod +x gradlew
            ./gradlew assembleRelease
        } else {
            Write-Host "⚠️ Gradle wrapper not found, skipping..." -ForegroundColor Yellow
            Pop-Location
        }
        
        $apkPath = "app/build/outputs/apk/release"
        if (Test-Path $apkPath) {
            $apkFiles = Get-ChildItem $apkPath -Filter "*.apk"
            foreach ($apk in $apkFiles) {
                Write-Host "✅ Built: mobile/android/$apkPath/$($apk.Name) ($([math]::Round($apk.Length/1MB, 2)) MB)" -ForegroundColor Green
            }
        }
        
        Pop-Location
    } else {
        Write-Host "⚠️ Mobile Android directory not found, skipping..." -ForegroundColor Yellow
    }
}

Write-Host "`n" + "=" * 60
Write-Host "✅ Production build complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📁 Build Outputs:" -ForegroundColor Cyan
Write-Host "   Frontend: frontend/dist/"
Write-Host "   Desktop:  desktop/dist/"
Write-Host "   Mobile:   mobile/android/app/build/outputs/apk/release/"
Write-Host ""
Write-Host "🚀 To start production server:" -ForegroundColor Cyan
Write-Host "   python -m local_agent.web.app"
Write-Host ""
Write-Host "🌐 Then open: http://localhost:8000"
