#!/bin/bash

# Quick start script for Docker setup with stage/prod workflow

echo "========================================="
echo "SDOHPlace Metadata Manager - Docker Setup"
echo "========================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

# Check if .env.docker exists
if [ ! -f .env.docker ]; then
    echo "Creating .env.docker..."
    cat > .env.docker << 'EOF'
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
EOF
    echo "✓ Created .env.docker"
    echo "⚠️  Please edit .env.docker and set a secure SECRET_KEY"
    echo ""
fi

# Start Docker Compose
echo "Starting Docker containers..."
docker compose up -d --build

echo ""
echo "Waiting for services to be ready..."
sleep 10

# Check if containers are running
if ! docker ps | grep -q sdoh-manager; then
    echo "Error: Manager container failed to start"
    echo "Check logs with: docker compose logs manager"
    exit 1
fi

if ! docker ps | grep -q sdoh-solr; then
    echo "Error: Solr container failed to start"
    echo "Check logs with: docker compose logs solr"
    exit 1
fi

echo "✓ Containers are running"
echo ""

# Create Solr cores
echo "Creating Solr cores..."

# Wait for Solr to be fully ready
sleep 5

# Create staging core
echo "Creating staging core (blacklight-core-stage)..."
curl -s "http://localhost:8983/solr/admin/cores?action=CREATE&name=blacklight-core-stage&configSet=_default" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✓ Staging core created"
else
    echo "⚠️  Staging core may already exist or Solr is still starting"
fi

# Create production core
echo "Creating production core (blacklight-core-prod)..."
curl -s "http://localhost:8983/solr/admin/cores?action=CREATE&name=blacklight-core-prod&configSet=_default" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✓ Production core created"
else
    echo "⚠️  Production core may already exist or Solr is still starting"
fi

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Access points:"
echo "  Metadata Manager: http://localhost:8000"
echo "  Solr Admin:       http://localhost:8983"
echo ""
echo "Next steps:"
echo ""
echo "1. Create an admin user:"
echo "   docker exec -it sdoh-manager flask user create admin admin@example.com password"
echo ""
echo "2. Index records to staging:"
echo "   docker exec -it sdoh-manager flask registry index --env stage"
echo ""
echo "3. Index records to production (admin only):"
echo "   docker exec -it sdoh-manager flask registry index --env prod"
echo ""
echo "Login credentials:"
echo "  Email: admin@example.com"
echo "  Password: password"
echo ""
echo "To view logs:"
echo "  docker compose logs -f manager"
echo ""
echo "To stop containers:"
echo "  docker compose down"
echo ""

