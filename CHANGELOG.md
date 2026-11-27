# Changelog

## Unreleased — external brains and Oracle portability

- Expanded MCP to 13 scoped tools: shared context, Box probes, Beeper reads, native history.
- Added separate client credentials, private ChatGPT plugin connection documentation, and core-only Pi upgrade/verification.
- Added portable Oracle API/MCP installer and consistent SQLite migration snapshot with task-drain gate.
- Consolidated current-state inventory, reboot checks, cutover and rollback; Redmi uses native Termux.
- Oracle provisioning and complete external-tool federation remain pending.

## 0.2.0 — Personal AI control plane implementation

- Added persistent SQLite storage for client/node credentials, node heartbeats, tasks, context documents and hash-chained audit events.
- Added FastAPI authentication, node enrollment/revocation, outbound task polling, approval queue, task results and context search.
- Added unprivileged pai-agent daemon with bounded argv execution, approval-gated shell/sensitive operations and restricted systemd helper.
- Added official Python MCP SDK adapter with stdio and authenticated Streamable HTTP transports.
- Added isolated pai-api, pai-mcp and pai-agent service accounts; task processes cannot read the API database or node credential.
- Added a durable local task-result spool so completed work survives API restarts.
- Added a context:write-only indexing credential and API route, separate from context:read.
- Added Pi installer, systemd units, scoped credential CLI, context indexer and end-to-end tests.

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
