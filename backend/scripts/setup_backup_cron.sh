#!/bin/bash

##############################################################################
# Automated Backup Setup Script
#
# This script sets up automated daily database backups using cron.
#
# Usage:
#   sudo ./setup_backup_cron.sh
##############################################################################

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKUP_SCRIPT="$SCRIPT_DIR/backup_postgres_database.sh"
LOG_FILE="/var/log/wedding-backup.log"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}This script should be run as root (sudo) to set up system-wide cron jobs${NC}"
    echo "Continuing anyway for user-level cron setup..."
fi

# Ensure backup script is executable
chmod +x "$BACKUP_SCRIPT"

# Create log directory
sudo mkdir -p "$(dirname "$LOG_FILE")"
sudo touch "$LOG_FILE"
sudo chmod 666 "$LOG_FILE"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "$BACKUP_SCRIPT"; then
    echo -e "${YELLOW}Cron job already exists. Updating...${NC}"
    # Remove old cron job
    crontab -l 2>/dev/null | grep -v "$BACKUP_SCRIPT" | crontab - || true
fi

# Add new cron job (daily at 2 AM)
(crontab -l 2>/dev/null || true; echo "0 2 * * * $BACKUP_SCRIPT >> $LOG_FILE 2>&1") | crontab -

echo -e "${GREEN}✓ Automated backup cron job installed${NC}"
echo ""
echo "Backup schedule: Daily at 2:00 AM"
echo "Backup script: $BACKUP_SCRIPT"
echo "Log file: $LOG_FILE"
echo ""
echo "Current cron jobs:"
crontab -l

echo ""
echo -e "${YELLOW}To modify the schedule, run: crontab -e${NC}"
echo ""
echo "Cron schedule examples:"
echo "  Every day at 2 AM:      0 2 * * *"
echo "  Every 6 hours:          0 */6 * * *"
echo "  Every hour:             0 * * * *"
echo "  Weekly (Sunday 3 AM):   0 3 * * 0"
