# Morphic Frontend Integration

## Overview
Morphic serves as the conversational AI search and chat UI at `https://hermes.bchbenjamin.in`.
- It communicates downstream with the Personal AI API (`https://api.hermes.bchbenjamin.in`).
- It uses dedicated client tokens restricted to scopes `context:read`, `terminal:execute`, and `nodes:read`.
- It does not communicate directly with managed nodes or the AI Gateway.
