#!/bin/bash
# Example cron configuration for automated backups
# 
# To install this cron job:
# 1. Make backup.sh executable: chmod +x scripts/backup.sh
# 2. Edit your crontab: crontab -e
# 3. Add one of the example lines below (uncommented)

# Example 1: Run backup daily at 2:00 AM
# 0 2 * * * cd /path/to/SDOHPlace-MetadataManager && ./scripts/backup.sh >> ./backups/cron.log 2>&1

# Example 2: Run backup twice daily (2 AM and 2 PM)
# 0 2,14 * * * cd /path/to/SDOHPlace-MetadataManager && ./scripts/backup.sh >> ./backups/cron.log 2>&1

# Example 3: Run backup every Sunday at 3:00 AM
# 0 3 * * 0 cd /path/to/SDOHPlace-MetadataManager && ./scripts/backup.sh >> ./backups/cron.log 2>&1

# Example 4: Run backup daily at midnight with custom retention (keep 60 days)
# 0 0 * * * cd /path/to/SDOHPlace-MetadataManager && RETENTION_DAYS=60 ./scripts/backup.sh >> ./backups/cron.log 2>&1

# Example 5: Run backup with custom backup directory
# 0 2 * * * cd /path/to/SDOHPlace-MetadataManager && BACKUP_DIR=/mnt/backups ./scripts/backup.sh >> ./backups/cron.log 2>&1

# Cron syntax reference:
# * * * * * command
# │ │ │ │ │
# │ │ │ │ └─── Day of week (0-7, 0 or 7 is Sunday)
# │ │ │ └───── Month (1-12)
# │ │ └─────── Day of month (1-31)
# │ └───────── Hour (0-23)
# └─────────── Minute (0-59)

