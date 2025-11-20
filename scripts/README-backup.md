# Backup and Restore Scripts

Technical reference for backup and restore scripts. See the [main README](../README.md#backup-and-restore) for usage instructions.

## Files

- **`backup.sh`** - Main backup script that creates timestamped archives
- **`restore.sh`** - Restore script that recovers data from backups
- **`backup-cron-example.sh`** - Example cron job configurations
- **`sdoh-backup.service`** - Systemd service unit for automated backups
- **`sdoh-backup.timer`** - Systemd timer unit for scheduling backups

## Script Configuration

### Environment Variables

Both scripts support these environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `BACKUP_DIR` | `./backups` | Directory for storing backups (also used as base for log files) |
| `RETENTION_DAYS` | `30` | Days to keep old backups (backup.sh only) |
| `COMPRESS` | `true` | Enable/disable compression (backup.sh only) |
| `LOG_FILE` | `${BACKUP_DIR}/backup.log` or `${BACKUP_DIR}/restore.log` | Log file location (uses BACKUP_DIR by default) |

### Script Behavior

**`backup.sh`:**
- Creates timestamped archives: `sdoh-backup-YYYYMMDD_HHMMSS.tar.gz`
- Backs up `./solr-data/` and `./manager/data.db`
- Automatically cleans up backups older than `RETENTION_DAYS`
- Color-coded console output (green=info, yellow=warning, red=error)
- Logs all operations to `${BACKUP_DIR}/backup.log` (default: `./backups/backup.log`)
- Exit code 0 on success, 1 on failure

**`restore.sh`:**
- Requires backup name as argument (with or without .tar.gz extension)
- Checks if Docker containers are running (will exit if they are)
- Creates pre-restore backup before overwriting data
- Displays backup metadata and asks for confirmation
- Logs all operations to `${BACKUP_DIR}/restore.log` (default: `./backups/restore.log`)
- Exit code 0 on success, 1 on failure

## Backup Archive Structure

Each backup archive contains:
```
sdoh-backup-YYYYMMDD_HHMMSS/
├── backup_metadata.txt       # Backup information
├── solr-data/                 # Complete Solr data directory
│   ├── blacklight-core-stage/
│   └── blacklight-core-prod/
└── manager/
    └── data.db                # SQLite database
```

## Log Files

**Backup log** (default: `${BACKUP_DIR}/backup.log`):
```
2024-11-06 02:00:00 [INFO] Starting SDOH Place backup: sdoh-backup-20241106_020000
2024-11-06 02:00:01 [INFO] Solr data backed up successfully
2024-11-06 02:00:02 [INFO] SQLite database backed up successfully
2024-11-06 02:00:05 [INFO] Backup completed successfully!
```

**Restore log** (default: `${BACKUP_DIR}/restore.log`):
```
2024-11-06 10:30:00 [INFO] Starting SDOH Place restore: sdoh-backup-20241106_020000
2024-11-06 10:30:05 [INFO] Solr data restored successfully
2024-11-06 10:30:06 [INFO] SQLite database restored successfully
2024-11-06 10:30:06 [INFO] Restore completed successfully!
```

## Exit Codes

Both scripts use standard exit codes:
- `0` - Success
- `1` - Error (check log files for details)

## See Also

- **Usage Instructions**: [Main README - Backup and Restore](../README.md#backup-and-restore)
- **GitHub Issue**: [#73 - Implement automated backup script](https://github.com/healthyregions/SDOHPlace-MetadataManager/issues/73)

