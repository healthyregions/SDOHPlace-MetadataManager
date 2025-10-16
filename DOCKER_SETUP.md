# Docker Compose Setup Guide

This guide explains how to use Docker Compose to run the SDOHPlace Metadata Manager with the stage/prod workflow.

## Prerequisites

- Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- Docker Compose (usually included with Docker Desktop)

## Quick Start

### 1. Start the Application

```bash
docker compose up -d --build
```

This command will:
- Build the metadata manager Docker image
- Start a Solr container on port 8983
- Start the metadata manager container on port 8000
- Create a default Solr core named `blacklight-core-stage`

**Access the application:**
- Metadata Manager: http://localhost:8000
- Solr Admin: http://localhost:8983

### 2. Create a User

First, get the container ID:

```bash
docker ps
```

Look for the container named `sdoh-manager` and copy its ID, then enter the container:

```bash
docker exec -it sdoh-manager bash
```

Or use the container name directly:

```bash
docker exec -it sdoh-manager bash
```

Inside the container, create an admin user:

```bash
flask user create admin admin@example.com password
```

**Important:** Login uses **email** and **password**, not the username!

### 3. Create Staging and Production Cores (Optional)

The docker-compose setup creates `blacklight-core-stage` and `blacklight-core-prod` cores automatically.

If you need to create additional cores or recreate them, use:

```bash
# From inside the container
curl "http://solr:8983/solr/admin/cores?action=CREATE&name=blacklight-core-stage&configSet=_default"
curl "http://solr:8983/solr/admin/cores?action=CREATE&name=blacklight-core-prod&configSet=_default"

# Or from your host machine
curl "http://localhost:8983/solr/admin/cores?action=CREATE&name=blacklight-core-stage&configSet=_default"
curl "http://localhost:8983/solr/admin/cores?action=CREATE&name=blacklight-core-prod&configSet=_default"
```

Verify cores were created at: http://localhost:8983/solr/#/~cores

### 4. Configure Environment Variables

Copy the example environment file and customize it:

```bash
cp .env.docker.example .env.docker
```

Then edit `.env.docker` and change at minimum:
- `SECRET_KEY` - Set to a secure random string (required for Flask sessions)

**Important:** 
- The `.env.docker` file is git-ignored and will not be tracked
- Inside Docker, use `http://solr:8983/solr` (service name), not `localhost`
- For local (non-Docker) setup, you would use `http://localhost:8983/solr` instead

See `.env.docker.example` for all available configuration options.

### 5. Index Records

Inside the container:

```bash
# Index all records to dev/staging
flask registry index --env dev

# Index all records to production (after verifying in dev)
flask registry index --env prod

# Index specific record to dev
flask registry index --id my-record-id --env dev
```

## Docker Compose Commands

### Start Services

```bash
# Start in background
docker compose up -d

# Start with build
docker compose up -d --build

# Start with logs
docker compose up
```

### Stop Services

```bash
# Stop containers (keeps data)
docker compose down

# Stop and remove volumes (deletes all data!)
docker compose down -v
```

### View Logs

```bash
# All services
docker compose logs

# Specific service
docker compose logs manager
docker compose logs solr

# Follow logs (live)
docker compose logs -f manager
```

### Restart Services

```bash
# Restart all
docker compose restart

# Restart specific service
docker compose restart manager
```

## Working with the Manager Container

### Enter the Container

```bash
docker exec -it sdoh-manager bash
```

### Run Flask Commands

Inside the container:

```bash
# Create user
flask user create username email@example.com password

# Index to dev/staging
flask registry index --env dev

# Index to production
flask registry index --env prod

# Validate records
flask registry validate-records

# Check coverage
flask coverage generate-highlight-ids input.csv tract -i id_field
```

### Exit Container

```bash
exit
```

## Environment Setup

The docker-compose configuration uses `.env.docker` for environment variables. A template is provided as `.env.docker.example`.

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key for sessions | (required) |
| `FLASK_APP` | Flask application path | `manager/app.py` |
| `SOLR_HOST` | Solr server URL | `http://solr:8983/solr` |
| `SOLR_CORE_STAGE` | Staging core name | `blacklight-core-stage` |
| `SOLR_CORE_PROD` | Production core name | `blacklight-core-prod` |
| `SOLR_CORE` | Legacy single core (optional) | - |
| `SOLR_USERNAME` | Solr authentication username | (optional) |
| `SOLR_PASSWORD` | Solr authentication password | (optional) |
| `GBL_HOST` | GeoBlacklight URL | (optional) |
| `DISCOVERY_APP_URL` | Data discovery app URL | (optional) |
| `PORT` | Internal container port | `8000` |

## Solr Core Configuration

### Manual Core Creation

If you need custom configuration, you can create cores manually:

1. Copy your config files to the Solr container:
```bash
docker cp ./solr/conf sdoh-solr:/opt/solr-9.7.0-slim/server/solr/configsets/myconfig/
```

2. Create core with custom config:
```bash
docker exec -it sdoh-solr solr create_core -c blacklight-core-stage -d /opt/solr-9.7.0-slim/server/solr/configsets/myconfig
```

### Verify Cores

Check which cores exist:

```bash
curl "http://localhost:8983/solr/admin/cores?action=STATUS"
```

Or visit: http://localhost:8983/solr/#/~cores

## Integrating with Data Discovery App

If you're running the SDOHPlace Data Discovery application locally, configure it to use the appropriate core:

In your Data Discovery app's `.env`:

```env
# For staging preview
NEXT_PUBLIC_SOLR_URL='http://localhost:8983/solr/blacklight-core-stage'

# For production
NEXT_PUBLIC_SOLR_URL='http://localhost:8983/solr/blacklight-core-prod'
```

## Troubleshooting

### Container won't start

Check logs:
```bash
docker compose logs manager
```

### Can't connect to Solr

1. Verify Solr is running:
```bash
docker compose ps
```

2. Check Solr health:
```bash
curl http://localhost:8983/solr/admin/ping
```

3. Ensure cores are created:
```bash
curl "http://localhost:8983/solr/admin/cores?action=STATUS"
```

### Port already in use

If port 8000 or 8983 is already in use, modify `docker-compose.yml`:

```yaml
services:
  solr:
    ports:
      - "8984:8983"  # Use different host port
  
  manager:
    ports:
      - "8001:8000"  # Use different host port
```

### Permission denied

If you get permission errors, ensure the volumes are correctly mounted:

```yaml
volumes:
  - ./manager:/home/herop/manager
```

### 503 Error from Solr

This is a health check ping error and can be safely ignored. The cores still work correctly.

## Updating Configuration

After changing `.env.docker`:

```bash
docker compose down
docker compose up -d
```

After changing code:

```bash
docker compose up -d --build
```

## Data Persistence

Data is stored in Docker volumes:
- Solr data persists across container restarts
- Manager database (`data.db`) persists if volume is mounted

To completely reset:

```bash
docker compose down -v
docker compose up -d --build
```

Then recreate user and reindex records.

## Production Deployment

For production deployments:

1. Use strong `SECRET_KEY` in `.env.docker`
2. Configure proper `SOLR_USERNAME` and `SOLR_PASSWORD`
3. Use a reverse proxy (nginx) in front of the manager
4. Enable HTTPS
5. Configure proper backup strategy for Solr data
6. Use separate Solr instances for staging and production if possible

## Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Solr Documentation](https://solr.apache.org/guide/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Project README](./README.md)

