# Backup and Restoration Guide

## Backup Principles
- **No Git Backups for Personal Data**: Personal databases, Beeper chats, and secret keys are never committed to Git.
- **Segregated Backups**: Configuration templates are kept separate from operational state.

## Creating Backups
```bash
# 1. Back up non-sensitive configuration
bash deployment/backup/backup-config.sh

# 2. Back up Hermes state databases (off-git)
bash deployment/backup/backup-hermes-state.sh
```

## Restoring Backups
```bash
# Restore state to target directory
bash deployment/backup/restore.sh ~/backups/hermes-state-<timestamp>.tar.gz ~/.hermes-pi/
```
