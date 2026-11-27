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

## Consistent control-plane migration snapshot

Use deployment/backup/control-plane-snapshot.py instead of copying a live
SQLite file. The helper uses the online backup API, checks integrity and
foreign keys, and refuses to overwrite existing files. Use --quiescent for
final migration after all writers are stopped and tasks drained. It refuses
queued/running/approval-required tasks rather than replaying them.

The legacy archive helpers are not sufficient for full migration; stop
Hermes before archiving its canonical runtime, preserve all relevant state
and permissions, and encrypt private archives before off-host transfer.
See [Oracle migration](../deployment/oracle-migration.md) for the full
cutover and rollback checklist.
