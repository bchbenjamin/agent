# Changelog

All notable changes to the Personal AI Infrastructure repository will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-11-23

### Added
- Established canonical `personal-ai-infrastructure` repository.
- Defined two-layer architectural boundary isolating Layer 1 (AI Gateway inference at `https://ai.bchbenjamin.in`) from Layer 2 (Personal AI Infrastructure).
- Conducted Phase 1 comprehensive audit of Raspberry Pi 5 live environment and generated `reports/initial-audit.md`.
- Implemented Control Plane core: node registry, task router, token authentication, permission scope validation, and audit logging.
- Created Personal AI API server application (`https://api.hermes.bchbenjamin.in`) with FastAPI.
- Implemented MCP protocol adapter (`https://mcp.hermes.bchbenjamin.in`) routing MCP calls into authenticated API operations.
- Added unprivileged Node Agent daemon and systemd service adapters.
- Created managed node specification for Raspberry Pi 5 (`nodes/pi5/node-spec.yaml`) with verified hardware and storage topology.
- Added future node specifications for Redmi Note 5 Pro (`nodes/redmi/`) and Simular Box (`nodes/box/`).
- Migrated Hermes, Beeper, computer-use-linux, and Simular Box deployment configurations and templates.
- Established central upstream dependency manifest (`upstreams/manifest.yaml`) pinning Hermes Agent, computer-use-linux, Morphic, and Beeper.
- Created idempotent node bootstrap, upgrade, rollback, and backup scripts.
- Added automated unit, integration, and security test suites including automated secret scanning.
- Set up GitHub Actions CI workflows for test execution and secret verification.
