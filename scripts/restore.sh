#!/bin/bash

# SDOH Place - Metadata Manager Restore Script
# This script restores backups created by backup.sh

set -e  # Exit on error

# Configuration
BACKUP_DIR="${BACKUP_DIR:-./backups}"
LOG_FILE="${LOG_FILE:-./backups/restore.log}"

# Directories to restore to
SOLR_DATA_DIR="./solr-data"
MANAGER_DB="./manager/data.db"

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

# Display usage
usage() {
    cat << EOF
Usage: $0 <backup-name>

Restore a backup created by backup.sh

Arguments:
  backup-name    Name of the backup to restore (e.g., sdoh-backup-20241106_143022)
                 Can be with or without .tar.gz extension

Environment Variables:
  BACKUP_DIR     Directory containing backups (default: ./backups)
  LOG_FILE       Log file location (default: ./backups/restore.log)

Examples:
  $0 sdoh-backup-20241106_143022
  $0 sdoh-backup-20241106_143022.tar.gz

To list available backups:
  ls -lt ./backups/

EOF
    exit 1
}

# Check if Docker containers are running
check_containers() {
    if command -v docker &> /dev/null && docker compose ps | grep -q "Up"; then
        log_error "Docker containers are running!"
        log_error "Please stop containers before restoring: docker compose down"
        exit 1
    fi
}

# List available backups
list_backups() {
    log_info "Available backups:"
    if [ -d "${BACKUP_DIR}" ]; then
        ls -1t "${BACKUP_DIR}"/sdoh-backup-*.tar.gz 2>/dev/null | head -10 || {
            log_warn "No compressed backups found"
        }
        ls -1dt "${BACKUP_DIR}"/sdoh-backup-*/ 2>/dev/null | head -10 || {
            log_warn "No uncompressed backup directories found"
        }
    else
        log_error "Backup directory not found: ${BACKUP_DIR}"
    fi
}

# Extract backup if compressed
extract_backup() {
    local backup_name=$1
    local backup_path="${BACKUP_DIR}/${backup_name}"
    
    # Check if it's a compressed archive
    if [ -f "${backup_path}.tar.gz" ]; then
        log_info "Extracting compressed backup: ${backup_name}.tar.gz"
        tar -xzf "${backup_path}.tar.gz" -C "${BACKUP_DIR}" || {
            log_error "Failed to extract backup"
            exit 1
        }
        log_info "Backup extracted successfully"
        return 0
    elif [ -f "${backup_path}" ] && [[ "${backup_path}" == *.tar.gz ]]; then
        # Remove .tar.gz from name for extraction
        local clean_name="${backup_name%.tar.gz}"
        log_info "Extracting compressed backup: ${backup_name}"
        tar -xzf "${backup_path}" -C "${BACKUP_DIR}" || {
            log_error "Failed to extract backup"
            exit 1
        }
        echo "${clean_name}"
        return 0
    elif [ -d "${backup_path}" ]; then
        log_info "Backup is already uncompressed"
        return 0
    else
        log_error "Backup not found: ${backup_name}"
        list_backups
        exit 1
    fi
}

# Create backup of current data before restore
backup_current_data() {
    log_info "Creating backup of current data before restore..."
    
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local pre_restore_backup="${BACKUP_DIR}/pre-restore-${timestamp}"
    
    mkdir -p "${pre_restore_backup}"
    
    # Backup current Solr data if exists
    if [ -d "${SOLR_DATA_DIR}" ]; then
        cp -r "${SOLR_DATA_DIR}" "${pre_restore_backup}/solr-data" || log_warn "Could not backup current Solr data"
    fi
    
    # Backup current database if exists
    if [ -f "${MANAGER_DB}" ]; then
        mkdir -p "${pre_restore_backup}/manager"
        cp "${MANAGER_DB}" "${pre_restore_backup}/manager/data.db" || log_warn "Could not backup current database"
    fi
    
    log_info "Current data backed up to: ${pre_restore_backup}"
}

# Restore Solr data
restore_solr() {
    local backup_name=$1
    local backup_path="${BACKUP_DIR}/${backup_name}"
    
    log_info "Restoring Solr data..."
    
    if [ ! -d "${backup_path}/solr-data" ]; then
        log_warn "No Solr data found in backup"
        return 0
    fi
    
    # Remove current Solr data
    if [ -d "${SOLR_DATA_DIR}" ]; then
        rm -rf "${SOLR_DATA_DIR}"
    fi
    
    # Restore Solr data
    mkdir -p "${SOLR_DATA_DIR}"
    cp -r "${backup_path}/solr-data"/* "${SOLR_DATA_DIR}/" || {
        log_error "Failed to restore Solr data"
        exit 1
    }
    
    log_info "Solr data restored successfully"
}

# Restore SQLite database
restore_database() {
    local backup_name=$1
    local backup_path="${BACKUP_DIR}/${backup_name}"
    
    log_info "Restoring SQLite database..."
    
    if [ ! -f "${backup_path}/manager/data.db" ]; then
        log_warn "No SQLite database found in backup"
        return 0
    fi
    
    # Ensure manager directory exists
    mkdir -p "./manager"
    
    # Remove current database if exists
    if [ -f "${MANAGER_DB}" ]; then
        rm -f "${MANAGER_DB}"
    fi
    
    # Restore database
    cp "${backup_path}/manager/data.db" "${MANAGER_DB}" || {
        log_error "Failed to restore SQLite database"
        exit 1
    }
    
    log_info "SQLite database restored successfully"
}

# Display backup metadata
show_metadata() {
    local backup_name=$1
    local backup_path="${BACKUP_DIR}/${backup_name}"
    local metadata_file="${backup_path}/backup_metadata.txt"
    
    if [ -f "${metadata_file}" ]; then
        log_info "Backup metadata:"
        echo "========================================="
        cat "${metadata_file}"
        echo "========================================="
    fi
}

# Main restore function
main() {
    # Check if backup name provided
    if [ $# -eq 0 ]; then
        log_error "No backup name provided"
        usage
    fi
    
    local backup_name=$1
    # Remove .tar.gz extension if provided
    backup_name="${backup_name%.tar.gz}"
    
    log_info "========================================="
    log_info "Starting SDOH Place restore: ${backup_name}"
    log_info "========================================="
    
    # Check if containers are running
    check_containers
    
    # Extract backup if compressed
    backup_name=$(extract_backup "${backup_name}")
    
    # Show backup metadata
    show_metadata "${backup_name}"
    
    # Ask for confirmation
    echo ""
    read -p "Are you sure you want to restore this backup? This will overwrite current data. (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        log_warn "Restore cancelled by user"
        exit 0
    fi
    
    # Backup current data
    backup_current_data
    
    # Perform restore
    restore_solr "${backup_name}"
    restore_database "${backup_name}"
    
    log_info "========================================="
    log_info "Restore completed successfully!"
    log_info "You can now start the application: docker compose up -d"
    log_info "========================================="
}

# Run main function
main "$@"

