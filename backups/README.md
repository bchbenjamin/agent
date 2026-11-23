# Backup Policy & Storage Standards

## 1. Zero Personal Data on GitHub
Git repositories must never contain:
- Beeper chat history or SQLite databases (`.config/BeeperTexts/`).
- Recovered user profiles or keyrings (`Default_Keyring.keyring`).
- Operational state databases (`kanban.db`, `projects.db`, `state.db`).
- Active `.env` files or secret keys.

## 2. Backup Categories & Storage

| Category | Description | Destination | Encryption |
| :--- | :--- | :--- | :--- |
| **Source & Specs** | Repository code, node-spec.yaml, ADRs | GitHub (Private Repository) | TLS in transit |
| **Config Templates** | YAML/env templates | Git & local backup | None required |
| **Hermes State** | SQLite databases (`kanban.db`, etc.) | Off-git `/mnt/pi_data/backups` | Encrypted / 0600 mode |
| **Beeper User Data** | Full Electron profile, media | `/mnt/pi_data/backups/beeper` | Off-git, local storage |

## 3. Automated Scripts
- [deployment/backup/backup-config.sh](file:///home/bchbenjamin/personal-ai-infrastructure/deployment/backup/backup-config.sh)
- [deployment/backup/backup-hermes-state.sh](file:///home/bchbenjamin/personal-ai-infrastructure/deployment/backup/backup-hermes-state.sh)
- [deployment/backup/restore.sh](file:///home/bchbenjamin/personal-ai-infrastructure/deployment/backup/restore.sh)
