# Telegram Integration

## Architecture
The Personal AI Infrastructure interfaces with Telegram clients via the Personal AI API webhook.
- **Isolation Policy**: Telegram bot settings are completely decoupled from Hermes internal config.
- **Authentication**: Messages received via Telegram webhook are authenticated against the Personal AI API using dedicated bot credentials.
- **Permissions**: Restricted to authorized user IDs and assigned scope `context:read` and `terminal:execute` (with confirmation).
