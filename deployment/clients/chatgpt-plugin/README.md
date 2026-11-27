# Portable private plugin source

This is a sanitized source representation of the existing Hermes Personal AI
plugin (not an exact byte-for-byte export). The existing private plugin ID
is documented in docs/deployment/current-state.md. On migration, update
that existing plugin rather than creating a duplicate. Change only the
verified HTTPS MCP URL after testing the new origin. No credentials, user
history or deployment secrets belong in this package.
