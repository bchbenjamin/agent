# Morphic Frontend Integration

The fork at https://github.com/bchbenjamin/morphic implements an opt-in, owner-only Hermes chat mode (`/hermes`). It is a UI and streaming relay, not a second agent. The default Morphic researcher is bypassed in this mode. Hermes owns orchestration, memory, tools, and inference through the independent AI Gateway.

## Current configuration

See `docs/HERMES.md` in the Morphic repository. Enable real Morphic authentication (never anonymous mode) and set these server-side environment variables:

- `HERMES_CHAT_ENABLED=true`
- `HERMES_OWNER_USER_ID`: immutable authenticated owner ID
- `HERMES_WEB_ORIGIN=https://hermes.bchbenjamin.in`
- `HERMES_API_BASE_URL`: trusted Hermes `/v1` base URL; on the Pi this is `http://127.0.0.1:8642/v1`
- `HERMES_API_KEY`: distinct Hermes downstream API key, not an inference or Personal AI token
- `HERMES_API_MODEL=hermes`

Do not expose the key to browser code. Do not configure an AI Gateway key in this dedicated frontend deployment. Disable chat sharing and optional external telemetry. The public frontend requires a reachable, authenticated HTTPS ingress to Hermes; a cloud frontend cannot reach the Pi through its own loopback. Keep the existing Pi listeners private. The API domain can route an explicitly allowed Hermes `/v1/chat/completions` path to port 8642 when authenticated ingress is available; avoid route conflicts with Personal AI API operations on port 8000.

The first implementation streams text and derives stable session identity server-side per owner/conversation. Native session history browsing, approval UI, attachments, rich artifacts and production end-to-end validation are not yet complete.

## Future control-plane integration

If a dedicated owner-only node/task/approval panel is added, it may use a separate, minimal Personal AI client token server-side. Do not issue it merely for chat. Explicit approval should remain an owner action, never an automatic grant by the frontend. The Personal AI API and MCP endpoints retain their own credentials and are not used for inference.
