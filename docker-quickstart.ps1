# Quick start script for Docker setup with stage/prod workflow (Windows PowerShell)

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "SDOHPlace Metadata Manager - Docker Setup" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
try {
    docker info | Out-Null
} catch {
    Write-Host "Error: Docker is not running. Please start Docker Desktop and try again." -ForegroundColor Red
    exit 1
}

# Check if .env.docker exists
if (-not (Test-Path .env.docker)) {
    Write-Host "Creating .env.docker..."
    
    $envContent = @"
# Flask Configuration
SECRET_KEY=change-me-to-a-random-secret-key
FLASK_APP=manager/app.py

# Solr Configuration
# Note: Inside Docker, use the service name 'solr' not 'localhost'
SOLR_HOST=http://solr:8983/solr
SOLR_CORE_STAGE=blacklight-core-stage
SOLR_CORE_PROD=blacklight-core-prod
SOLR_USERNAME=
SOLR_PASSWORD=

# GeoBlacklight (if using)
GBL_HOST=http://localhost:3000

# Data Discovery App URL (if using)
DISCOVERY_APP_URL=http://localhost:3001

# Port (internal to container)
PORT=8000
"@
    
    $envContent | Out-File -FilePath .env.docker -Encoding UTF8
    Write-Host "[OK] Created .env.docker" -ForegroundColor Green
    Write-Host "[WARNING] Please edit .env.docker and set a secure SECRET_KEY" -ForegroundColor Yellow
    Write-Host ""
}

# Start Docker Compose
Write-Host "Starting Docker containers..."
docker compose up -d --build

Write-Host ""
Write-Host "Waiting for services to be ready..."
Start-Sleep -Seconds 10

# Check if containers are running
$managerRunning = docker ps | Select-String "sdoh-manager"
$solrRunning = docker ps | Select-String "sdoh-solr"

if (-not $managerRunning) {
    Write-Host "Error: Manager container failed to start" -ForegroundColor Red
    Write-Host "Check logs with: docker compose logs manager" -ForegroundColor Yellow
    exit 1
}

if (-not $solrRunning) {
    Write-Host "Error: Solr container failed to start" -ForegroundColor Red
    Write-Host "Check logs with: docker compose logs solr" -ForegroundColor Yellow
    exit 1
}

Write-Host "[OK] Containers are running" -ForegroundColor Green
Write-Host ""

# Create Solr cores
Write-Host "Creating Solr cores..."

# Wait for Solr to be fully ready
Start-Sleep -Seconds 5

# Create staging core
Write-Host "Creating staging core (blacklight-core-stage)..."
try {
    Invoke-WebRequest -Uri "http://localhost:8983/solr/admin/cores?action=CREATE&name=blacklight-core-stage&configSet=_default" -UseBasicParsing | Out-Null
    Write-Host "[OK] Staging core created" -ForegroundColor Green
} catch {
    Write-Host "[WARNING] Staging core may already exist or Solr is still starting" -ForegroundColor Yellow
}

# Create production core
Write-Host "Creating production core (blacklight-core-prod)..."
try {
    Invoke-WebRequest -Uri "http://localhost:8983/solr/admin/cores?action=CREATE&name=blacklight-core-prod&configSet=_default" -UseBasicParsing | Out-Null
    Write-Host "[OK] Production core created" -ForegroundColor Green
} catch {
    Write-Host "[WARNING] Production core may already exist or Solr is still starting" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Access points:"
Write-Host "  Metadata Manager: http://localhost:8000" -ForegroundColor White
Write-Host "  Solr Admin:       http://localhost:8983" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Create an admin user:"
Write-Host "   docker exec -it sdoh-manager flask user create admin admin@example.com password" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Index records to staging:"
Write-Host "   docker exec -it sdoh-manager flask registry index --env stage" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Index records to production (admin only):"
Write-Host "   docker exec -it sdoh-manager flask registry index --env prod" -ForegroundColor Cyan
Write-Host ""
Write-Host "Login credentials:"
Write-Host "  Email: admin@example.com" -ForegroundColor White
Write-Host "  Password: password" -ForegroundColor White
Write-Host ""
Write-Host "To view logs:"
Write-Host "  docker compose logs -f manager" -ForegroundColor Cyan
Write-Host ""
Write-Host "To stop containers:"
Write-Host "  docker compose down" -ForegroundColor Cyan
Write-Host ""

