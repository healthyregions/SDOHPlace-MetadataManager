# Configuration Guide

This document explains how to configure the SDOH Place Metadata Manager with parameterized core names.

## Environment Variables

The application now supports flexible configuration through environment variables. You can override the default core names by setting these environment variables:

### Core Configuration

| Variable | Description | Default Value |
|----------|-------------|---------------|
| `SOLR_CORE_STAGE` | Staging core name | `blacklight-core-stage` |
| `SOLR_CORE_PROD` | Production core name | `blacklight-core-prod` |
| `SOLR_HOST` | Solr server URL | `http://localhost:8983/solr` |

### Other Configuration

| Variable | Description | Default Value |
|----------|-------------|---------------|
| `GBL_HOST` | GeoBlacklight URL | (optional) |
| `DISCOVERY_APP_URL` | Discovery app URL | (optional) |

## Usage Examples

### 1. Using Default Values
```bash
# No environment variables needed - uses defaults
docker-compose up
```

### 2. Custom Core Names
```bash
# Set custom core names
export SOLR_CORE_STAGE=my-stage-core
export SOLR_CORE_PROD=my-prod-core

docker-compose up
```

### 3. Using .env File
Create a `.env` file in the project root:
```bash
# .env
SOLR_CORE_STAGE=sdoh-stage-core
SOLR_CORE_PROD=sdoh-prod-core
SOLR_HOST=http://localhost:8983/solr
GBL_HOST=http://localhost:3000
```

Then run:
```bash
docker-compose up
```

### 4. Docker Compose with Environment Variables
```yaml
# docker-compose.override.yml
services:
  solr:
    environment:
      - SOLR_CORE_STAGE=my-custom-stage-core
      - SOLR_CORE_PROD=my-custom-prod-core
  manager:
    environment:
      - SOLR_CORE_STAGE=my-custom-stage-core
      - SOLR_CORE_PROD=my-custom-prod-core
```

## Solr Configuration

The `solrconfig.xml` now uses a generic data directory variable:
```xml
<dataDir>${solr.data.dir:}</dataDir>
```

This allows Solr to use the default data directory for each core, making the configuration more flexible.

## Application Code

The application now supports two environments:
- `stage`: Uses `SOLR_CORE_STAGE` 
- `prod`: Uses `SOLR_CORE_PROD`

Example usage in Python:
```python
from manager.solr import Solr

# Staging environment
solr_stage = Solr(environment="stage")

# Production environment
solr_prod = Solr(environment="prod")
```

## Migration from Hardcoded Names

If you were previously using hardcoded core names, you can migrate by:

1. Setting the appropriate environment variables to match your existing core names
2. The application will automatically use these values instead of the defaults
3. No code changes are required

## Benefits

- **Flexibility**: Easy to change core names without modifying code
- **Environment-specific**: Different core names for stage/prod
- **Docker-friendly**: Works seamlessly with Docker Compose
- **Backward compatible**: Existing deployments continue to work
- **Consistent**: All components use the same environment variables
