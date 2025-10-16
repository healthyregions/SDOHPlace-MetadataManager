# SDOH Place - Metadata Manager

This is the metadata manager for the SDOH & Place Project, a map-based search platform for SDOH data discovery that curates and integrates validated geospatial data relevant to public health.

## Quick Start with Docker

### Prerequisites
- Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- Docker Compose

### 1. Clone and Setup
```bash
git clone <repository-url>
cd SDOHPlace-MetadataManager
```

### 2. Start the Application
```bash
docker compose up -d --build
```

This will:
- Build the metadata manager Docker image
- Start Solr on port 8983
- Start the metadata manager on port 8000
- Create `blacklight-core-stage` and `blacklight-core-prod` cores automatically

### 3. Access the Application
- **Metadata Manager**: http://localhost:8000
- **Solr Admin**: http://localhost:8983

### 4. Create Admin User
```bash
docker exec -it sdoh-manager flask user create admin admin@example.com password
```

**Important:** Login uses **email** and **password**, not the username!

### 5. Index Records
```bash
# Index to staging (all users)
docker exec -it sdoh-manager flask registry index --env stage

# Index to production (admin only)
docker exec -it sdoh-manager flask registry index --env prod
```

## Configuration

### Environment Variables

You can customize core names and other settings using environment variables:

| Variable | Description | Default Value |
|----------|-------------|---------------|
| `SOLR_CORE_STAGE` | Staging core name | `blacklight-core-stage` |
| `SOLR_CORE_PROD` | Production core name | `blacklight-core-prod` |
| `SOLR_HOST` | Solr server URL | `http://localhost:8983/solr` |
| `GBL_HOST` | GeoBlacklight URL | (optional) |

### Custom Configuration Examples

**Using .env file:**
```bash
# Create .env file
echo "SOLR_CORE_STAGE=my-stage-core" > .env
echo "SOLR_CORE_PROD=my-prod-core" >> .env
docker compose up
```

**Using environment variables:**
```bash
export SOLR_CORE_STAGE=my-stage-core
export SOLR_CORE_PROD=my-prod-core
docker compose up
```

## Management Commands

### Registry Commands
```bash
# Index all records to staging
flask registry index --env stage

# Index specific record to production
flask registry index --id <record-id> --env prod

# Clean and reindex all records
flask registry index --clean --env stage

# Resave all records (triggers data cleaning)
flask registry resave-records

# Bulk update records
flask registry bulk-update --field <field-name> --value <new-value>
```

### User Management
```bash
# Create user
flask user create <username> <email> <password>

# List users
flask user list

# Delete user
flask user delete <username>
```

## Connecting to Data Discovery App

If you're running the SDOHPlace Data Discovery application locally, configure it to use the appropriate Solr core:

**For staging preview:**
```env
NEXT_PUBLIC_SOLR_URL='http://localhost:8983/solr/blacklight-core-stage'
```

**For production:**
```env
NEXT_PUBLIC_SOLR_URL='http://localhost:8983/solr/blacklight-core-prod'
```

## Development Setup

### Local Development (without Docker)

1. **Install Python dependencies:**
```bash
pip install -r requirements.txt
pip install -e .
```

2. **Setup environment:**
```bash
cp .env.example .env
# Edit .env with your settings
```

3. **Start Solr locally:**
```bash
# Follow Solr installation guide for your OS
# Create cores manually or use provided scripts
```

4. **Run Flask app:**
```bash
export FLASK_APP=manager/app.py
export FLASK_ENV=development
flask run
```

## Schema Information

We use the Aardvark schema from [OpenGeoMetadata (OGM) Aardvark Schema](https://opengeometadata.org/ogm-aardvark/), with custom fields:

- **Spatial Resolution**: tract, zip code, county
- **Spatial Resolution Note**: Additional spatial context
- **Data Variables**: SDOH-specific data variables
- **Methods Variables**: Methodology and analysis variables

## Troubleshooting

### Common Issues

**Solr cores not created:**
```bash
# Check if cores exist
curl http://localhost:8983/solr/admin/cores?action=STATUS

# Manually create cores if needed
docker exec -it sdoh-solr solr create_core -c blacklight-core-stage -d /solr-configset
docker exec -it sdoh-solr solr create_core -c blacklight-core-prod -d /solr-configset
```

**Permission issues:**
```bash
# Check container logs
docker logs sdoh-manager
docker logs sdoh-solr
```

**Reset everything:**
```bash
docker compose down -v
docker compose up -d --build
```

## Shutdown

```bash
docker compose down
```

## Contributors

- Marynia Kolak
- Sarthak Joshi
- Augustyn Crane
- Adam Cox
- Mandela Gadri
- Arli Coli
- Camrin Garrett