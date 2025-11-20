#!/bin/bash

# SDOH Place - Metadata Manager Backup Script
# This script creates timestamped backups of Solr data and SQLite database
# Can be run manually or scheduled via cron/systemd timer

set -e  # Exit on error

# Configuration
BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
COMPRESS="${COMPRESS:-true}"
LOG_FILE="${LOG_FILE:-${BACKUP_DIR}/backup.log}"

# Directories to backup
SOLR_DATA_DIR="./solr-data"
MANAGER_DB="./manager/data.db"

# Timestamp for backup
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="sdoh-backup-${TIMESTAMP}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    echo -e "${timestamp} [${level}] ${message}" | tee -a "${LOG_FILE}"
}

log_info() {
    log "INFO" "${GREEN}$@${NC}"
}

log_warn() {
    log "WARN" "${YELLOW}$@${NC}"
}

log_error() {
    log "ERROR" "${RED}$@${NC}"
}

# Create backup directory if it doesn't exist
create_backup_dir() {
    if [ ! -d "${BACKUP_DIR}" ]; then
        mkdir -p "${BACKUP_DIR}"
        log_info "Created backup directory: ${BACKUP_DIR}"
    fi
}

# Check if Docker containers are running
check_containers() {
    if command -v docker &> /dev/null && docker compose ps | grep -q "Up"; then
        log_warn "Docker containers are running. Backup will proceed, but data consistency may vary."
        log_warn "For best results, consider stopping containers first: docker compose down"
    else
        log_info "Docker containers are not running or Docker is not available."
        log_info "This is ideal for data consistency."
    fi
    return 0
}

# Backup Solr data
backup_solr() {
    log_info "Starting Solr data backup..."
    
    if [ ! -d "${SOLR_DATA_DIR}" ]; then
        log_error "Solr data directory not found: ${SOLR_DATA_DIR}"
        return 1
    fi
    
    local temp_dir="${BACKUP_DIR}/${BACKUP_NAME}"
    mkdir -p "${temp_dir}/solr-data"
    
    # Copy Solr data (handle empty directory case)
    if [ -n "$(ls -A "${SOLR_DATA_DIR}" 2>/dev/null)" ]; then
        cp -r "${SOLR_DATA_DIR}"/* "${temp_dir}/solr-data/" 2>/dev/null || {
            log_error "Failed to copy Solr data"
            return 1
        }
    else
        log_warn "Solr data directory is empty"
    fi
    
    log_info "Solr data backed up successfully"
    return 0
}

# Backup SQLite database
backup_database() {
    log_info "Starting SQLite database backup..."
    
    if [ ! -f "${MANAGER_DB}" ]; then
        log_warn "SQLite database not found: ${MANAGER_DB}"
        log_warn "This may be normal if the application hasn't been initialized yet."
        return 0
    fi
    
    local temp_dir="${BACKUP_DIR}/${BACKUP_NAME}"
    mkdir -p "${temp_dir}/manager"
    
    # Copy database file
    cp "${MANAGER_DB}" "${temp_dir}/manager/data.db" 2>/dev/null || {
        log_error "Failed to copy SQLite database"
        return 1
    }
    
    log_info "SQLite database backed up successfully"
    return 0
}

# Create metadata file
create_metadata() {
    local temp_dir="${BACKUP_DIR}/${BACKUP_NAME}"
    local metadata_file="${temp_dir}/backup_metadata.txt"
    
    cat > "${metadata_file}" << EOF
SDOH Place - Metadata Manager Backup
=====================================
Backup Date: $(date +"%Y-%m-%d %H:%M:%S")
Backup Name: ${BACKUP_NAME}
Hostname: $(hostname)
User: $(whoami)

Contents:
- Solr Data: ${SOLR_DATA_DIR}
- SQLite DB: ${MANAGER_DB}

To restore this backup, use:
  ./scripts/restore.sh ${BACKUP_NAME}

EOF
    
    log_info "Metadata file created"
}

# Compress backup
compress_backup() {
    if [ "${COMPRESS}" = "true" ]; then
        log_info "Compressing backup..."
        
        local temp_dir="${BACKUP_DIR}/${BACKUP_NAME}"
        local archive_name="${BACKUP_NAME}.tar.gz"
        
        tar -czf "${BACKUP_DIR}/${archive_name}" -C "${BACKUP_DIR}" "${BACKUP_NAME}" || {
            log_error "Failed to compress backup"
            return 1
        }
        
        # Remove uncompressed directory
        rm -rf "${temp_dir}"
        
        local size=$(du -h "${BACKUP_DIR}/${archive_name}" | cut -f1)
        log_info "Backup compressed: ${archive_name} (${size})"
        echo "${archive_name}"
    else
        log_info "Compression disabled, backup left uncompressed"
        echo "${BACKUP_NAME}"
    fi
}

# Clean old backups based on retention policy
cleanup_old_backups() {
    log_info "Cleaning up backups older than ${RETENTION_DAYS} days..."
    
    local deleted_count=0
    
    # Find and delete old backup archives
    if [ -d "${BACKUP_DIR}" ]; then
        while IFS= read -r -d '' file; do
            rm -f "$file"
            log_info "Deleted old backup: $(basename "$file")"
            ((deleted_count++))
        done < <(find "${BACKUP_DIR}" -name "sdoh-backup-*.tar.gz" -mtime +${RETENTION_DAYS} -print0 2>/dev/null)
        
        # Also clean up old uncompressed directories
        while IFS= read -r -d '' dir; do
            rm -rf "$dir"
            log_info "Deleted old backup directory: $(basename "$dir")"
            ((deleted_count++))
        done < <(find "${BACKUP_DIR}" -maxdepth 1 -type d -name "sdoh-backup-*" -mtime +${RETENTION_DAYS} -print0 2>/dev/null)
    fi
    
    if [ ${deleted_count} -eq 0 ]; then
        log_info "No old backups to clean up"
    else
        log_info "Deleted ${deleted_count} old backup(s)"
    fi
}

# Main backup function
main() {
    log_info "========================================="
    log_info "Starting SDOH Place backup: ${BACKUP_NAME}"
    log_info "========================================="
    
    # Create backup directory (must be done before logging)
    create_backup_dir
    
    # Ensure log file directory exists
    mkdir -p "$(dirname "${LOG_FILE}")"
    
    # Check container status
    check_containers
    
    # Perform backups
    backup_solr || exit 1
    backup_database || exit 1
    
    # Create metadata
    create_metadata
    
    # Compress if enabled
    local final_backup=$(compress_backup)
    
    # Cleanup old backups
    cleanup_old_backups
    
    log_info "========================================="
    log_info "Backup completed successfully!"
    log_info "Backup location: ${BACKUP_DIR}/${final_backup}"
    log_info "========================================="
}

# Run main function
main

