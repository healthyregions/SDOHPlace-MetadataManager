# Docker Quick Reference

Quick reference guide for common Docker Compose tasks with the SDOHPlace Metadata Manager.

## Initial Setup

### 1. Start Everything (First Time)

**Linux/Mac:**
```bash
chmod +x docker-quickstart.sh
./docker-quickstart.sh
```

**Windows:**
```powershell
.\docker-quickstart.ps1
```

**Or manually:**
```bash
# Create .env.docker file with required values
cat > .env.docker << 'EOF'
SECRET_KEY=change-me-to-a-random-secret-key
FLASK_APP=manager/app.py
SOLR_HOST=http://solr:8983/solr
SOLR_CORE_STAGE=blacklight-core-stage
SOLR_CORE_PROD=blacklight-core-prod
SOLR_USERNAME=
SOLR_PASSWORD=
GBL_HOST=http://localhost:3000
DISCOVERY_APP_URL=http://localhost:3001
PORT=8000
EOF

# Edit .env.docker and set a secure SECRET_KEY

# Start containers
docker compose up -d --build

# Create Solr cores
curl "http://localhost:8983/solr/admin/cores?action=CREATE&name=blacklight-core-stage&configSet=_default"
curl "http://localhost:8983/solr/admin/cores?action=CREATE&name=blacklight-core-prod&configSet=_default"

# Create admin user
docker exec -it sdoh-manager flask user create admin admin@example.com password

# Index records
docker exec -it sdoh-manager flask registry index --env stage
```

## Daily Operations

### Start/Stop Containers

```bash
# Start
docker compose up -d

# Stop
docker compose down

# Restart
docker compose restart
```

### View Logs

```bash
# All logs
docker compose logs

# Follow logs (live)
docker compose logs -f

# Specific service
docker compose logs -f manager
docker compose logs -f solr
```

### Access Container Shell

```bash
# Manager container
docker exec -it sdoh-manager bash

# Solr container
docker exec -it sdoh-solr bash

# Exit container
exit
```

## User Management

```bash
# Enter container first
docker exec -it sdoh-manager bash

# Create user
flask user create username email@example.com password

# Create admin user (can index to production)
flask user create admin admin@example.com password

# Reset password
flask user reset-password email@example.com

# Change password
flask user change-password email@example.com newpassword
```

## Indexing Operations

```bash
# Enter container first
docker exec -it sdoh-manager bash

# Index all records to staging
flask registry index --env stage

# Index all records to production
flask registry index --env prod

# Index specific record to staging
flask registry index --id record-id --env stage

# Clean and reindex to staging
flask registry index --clean --env stage

# Validate all records
flask registry validate-records
```

## One-Line Commands (Without Entering Container)

```bash
# Create user
docker exec -it sdoh-manager flask user create admin admin@example.com password

# Index to staging
docker exec -it sdoh-manager flask registry index --env stage

# Index to production
docker exec -it sdoh-manager flask registry index --env prod

# Validate records
docker exec -it sdoh-manager flask registry validate-records
```

## Solr Management

### Access Solr Admin
http://localhost:8983

### Check Cores

```bash
# List all cores
curl "http://localhost:8983/solr/admin/cores?action=STATUS"

# Check staging core
curl "http://localhost:8983/solr/blacklight-core-stage/admin/ping"

# Check production core
curl "http://localhost:8983/solr/blacklight-core-prod/admin/ping"
```

### Create/Delete Cores

```bash
# Create staging core
curl "http://localhost:8983/solr/admin/cores?action=CREATE&name=blacklight-core-stage&configSet=_default"

# Create production core
curl "http://localhost:8983/solr/admin/cores?action=CREATE&name=blacklight-core-prod&configSet=_default"

# Delete core
curl "http://localhost:8983/solr/admin/cores?action=UNLOAD&core=blacklight-core-stage&deleteIndex=true"
```

## Troubleshooting

### Container won't start

```bash
# Check status
docker compose ps

# View logs
docker compose logs manager
docker compose logs solr

# Rebuild
docker compose down
docker compose up -d --build
```

### Can't connect to Solr

```bash
# Check Solr is running
docker ps | grep solr

# Test Solr ping
curl http://localhost:8983/solr/admin/ping

# Check cores exist
curl "http://localhost:8983/solr/admin/cores?action=STATUS"
```

### Permission errors

```bash
# Check volume mounts
docker compose config

# Restart with rebuild
docker compose down
docker compose up -d --build
```

### Port conflicts

Edit `docker-compose.yml` to use different ports:

```yaml
services:
  solr:
    ports:
      - "8984:8983"  # Change host port
  
  manager:
    ports:
      - "8001:8000"  # Change host port
```

## Environment Configuration

### Update Environment Variables

1. Edit `.env.docker`
2. Restart containers:
```bash
docker compose down
docker compose up -d
```

### Key Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SOLR_HOST` | Solr URL (use 'solr' inside Docker) | `http://solr:8983/solr` |
| `SOLR_CORE_STAGE` | Staging core name | `blacklight-core-stage` |
| `SOLR_CORE_PROD` | Production core name | `blacklight-core-prod` |
| `SECRET_KEY` | Flask secret (change this!) | - |

## Data Management

### Backup Data

```bash
# Backup Solr data
docker exec sdoh-solr tar czf /tmp/solr-backup.tar.gz /var/solr/data

# Copy backup from container
docker cp sdoh-solr:/tmp/solr-backup.tar.gz ./solr-backup.tar.gz

# Backup manager database
docker cp sdoh-manager:/home/herop/manager/data.db ./data.db.backup
```

### Restore Data

```bash
# Restore Solr data
docker cp ./solr-backup.tar.gz sdoh-solr:/tmp/
docker exec sdoh-solr tar xzf /tmp/solr-backup.tar.gz -C /

# Restore manager database
docker cp ./data.db.backup sdoh-manager:/home/herop/manager/data.db

# Restart
docker compose restart
```

### Complete Reset

```bash
# Remove everything (containers, volumes, images)
docker compose down -v
docker compose up -d --build

# Recreate cores
curl "http://localhost:8983/solr/admin/cores?action=CREATE&name=blacklight-core-stage&configSet=_default"
curl "http://localhost:8983/solr/admin/cores?action=CREATE&name=blacklight-core-prod&configSet=_default"

# Recreate user and reindex
docker exec -it sdoh-manager flask user create admin admin@example.com password
docker exec -it sdoh-manager flask registry index --env stage
```

## Access Points

- **Metadata Manager UI:** http://localhost:8000
- **Solr Admin UI:** http://localhost:8983
- **Solr Staging Core:** http://localhost:8983/solr/blacklight-core-stage
- **Solr Production Core:** http://localhost:8983/solr/blacklight-core-prod

## Common Workflows

### Preview Changes Before Publishing

1. Edit metadata in manager UI (http://localhost:8000)
2. Click "Index — Staging" button
3. Configure Data Discovery app to use staging core:
   ```env
   NEXT_PUBLIC_SOLR_URL='http://localhost:8983/solr/blacklight-core-stage'
   ```
4. Preview changes in Data Discovery app
5. When satisfied, click "Index — Production" (admin only)
6. Switch Data Discovery app to production core

### Update Single Record

1. Edit record in manager UI
2. Click "Index — Staging" to preview
3. Click "Index — Production" to publish (admin only)

### Bulk Update All Records

```bash
docker exec -it sdoh-manager bash

# Update and reindex all to staging
flask registry save-records
flask registry index --env stage --clean

# After verification, index to production
flask registry index --env prod --clean
```

## Additional Resources

- [Full Docker Documentation](./DOCKER_SETUP.md)
- [Stage/Prod Workflow Guide](./STAGE_PROD_WORKFLOW.md)
- [Main README](./README.md)

