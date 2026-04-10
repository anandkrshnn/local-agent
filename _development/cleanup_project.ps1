# cleanup_project.ps1 - Project Hygiene Script

Write-Host "?? Cleaning up project structure..." -ForegroundColor Cyan
Write-Host "=" -ForegroundColor Cyan -Repeat 60

# Create data directory
if (-not (Test-Path "data")) {
    New-Item -ItemType Directory -Path "data" | Out-Null
    Write-Host "?? Created data/ directory"
}

# Move database files
$dbFiles = @("*.db", "*.duckdb", "*.bak", "*.wal", "*.journal")
foreach ($pattern in $dbFiles) {
    Get-ChildItem -Path "." -Filter $pattern | ForEach-Object {
        $dest = Join-Path "data" $_.Name
        Move-Item -Path $_.FullName -Destination $dest -Force
        Write-Host "   Moved: $($_.Name) -> data/"
    }
}

# Create tests/results directory
if (-not (Test-Path "tests/results")) {
    New-Item -ItemType Directory -Path "tests/results" -Force | Out-Null
    Write-Host "?? Created tests/results/ directory"
}

# Move test results
Get-ChildItem -Path "." -Filter "test_results_*.json" | ForEach-Object {
    $dest = Join-Path "tests/results" $_.Name
    Move-Item -Path $_.FullName -Destination $dest -Force
    Write-Host "   Moved: $($_.Name) -> tests/results/"
}

# Remove old sprint test files (keep latest)
$oldTestFiles = @("test_sprint1.py", "test_sprint2.py", "test_sprint3.py", 
                  "test_sprint4.py", "test_sprint5.py", "test_sprint6.py",
                  "test_sprint7.py", "test_sprint8.py")
foreach ($file in $oldTestFiles) {
    if (Test-Path $file) {
        Remove-Item $file -Force
        Write-Host "   Removed: $file"
    }
}

Write-Host "`n?? Project cleanup complete!" -ForegroundColor Green
