#!/bin/bash

##############################################################################
# Database Backup Script for Wedding Planner PostgreSQL Database
#
# This script creates compressed backups of the PostgreSQL database with
# timestamps and implements a retention policy to manage old backups.
#
# Usage:
#   ./backup_database.sh [backup_dir]
#
# Environment Variables (from .env or set manually):
#   - DATABASE_URL: PostgreSQL connection string
#   - BACKUP_RETENTION_DAYS: Number of days to keep backups (default: 30)
##############################################################################

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DEFAULT_BACKUP_DIR="$PROJECT_ROOT/backups"
BACKUP_DIR="${1:-$DEFAULT_BACKUP_DIR}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Load environment variables
if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
else
    echo -e "${YELLOW}Warning: .env file not found. Using environment variables.${NC}"
fi

# Parse DATABASE_URL
if [ -z "${DATABASE_URL:-}" ]; then
    echo -e "${RED}Error: DATABASE_URL environment variable is not set${NC}"
    exit 1
fi

# Extract database credentials from DATABASE_URL
# Format: postgresql+asyncpg://user:password@host:port/database
DB_USER=$(echo "$DATABASE_URL" | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
DB_PASSWORD=$(echo "$DATABASE_URL" | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')
DB_HOST=$(echo "$DATABASE_URL" | sed -n 's/.*@\([^:]*\):.*/\1/p')
DB_PORT=$(echo "$DATABASE_URL" | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
DB_NAME=$(echo "$DATABASE_URL" | sed -n 's/.*\/\([^?]*\).*/\1/p')

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Backup filename
BACKUP_FILE="$BACKUP_DIR/wedding_db_${TIMESTAMP}.sql.gz"
BACKUP_LOG="$BACKUP_DIR/backup.log"

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$BACKUP_LOG"
}

# Function to send alert (implement your notification method)
send_alert() {
    local message="$1"
    log_message "ALERT: $message"
}

echo -e "${GREEN}Starting database backup...${NC}"
log_message "Starting database backup to $BACKUP_FILE"

# Export password for pg_dump
export PGPASSWORD="$DB_PASSWORD"

# Perform backup
if pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    --no-owner --no-acl --clean --if-exists | gzip > "$BACKUP_FILE"; then

    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo -e "${GREEN}✓ Backup completed successfully${NC}"
    log_message "Backup completed successfully. Size: $BACKUP_SIZE"

    # Verify backup integrity
    if gunzip -t "$BACKUP_FILE" 2>/dev/null; then
        echo -e "${GREEN}✓ Backup file integrity verified${NC}"
        log_message "Backup integrity verified"
    else
        echo -e "${RED}✗ Backup file integrity check failed${NC}"
        log_message "ERROR: Backup integrity check failed"
        send_alert "Database backup integrity check failed for $BACKUP_FILE"
        exit 1
    fi
else
    echo -e "${RED}✗ Backup failed${NC}"
    log_message "ERROR: Backup failed"
    send_alert "Database backup failed"
    exit 1
fi

# Clean up old backups (retention policy)
echo -e "${YELLOW}Cleaning up old backups (retention: ${RETENTION_DAYS} days)...${NC}"
log_message "Cleaning up backups older than $RETENTION_DAYS days"

DELETED_COUNT=0
while IFS= read -r old_backup; do
    rm -f "$old_backup"
    DELETED_COUNT=$((DELETED_COUNT + 1))
    log_message "Deleted old backup: $(basename "$old_backup")"
done < <(find "$BACKUP_DIR" -name "wedding_db_*.sql.gz" -type f -mtime +$RETENTION_DAYS)

if [ $DELETED_COUNT -gt 0 ]; then
    echo -e "${GREEN}✓ Deleted $DELETED_COUNT old backup(s)${NC}"
    log_message "Deleted $DELETED_COUNT old backups"
else
    echo -e "${GREEN}✓ No old backups to delete${NC}"
fi

# Display backup summary
echo ""
echo -e "${GREEN}=== Backup Summary ===${NC}"
echo "Backup file: $BACKUP_FILE"
echo "Size: $BACKUP_SIZE"
echo "Retention policy: $RETENTION_DAYS days"
echo "Total backups: $(find "$BACKUP_DIR" -name "wedding_db_*.sql.gz" -type f | wc -l)"

# Unset password
unset PGPASSWORD

log_message "Backup process completed successfully"
echo -e "${GREEN}✓ Backup process completed${NC}"
