# Raspberry Pi 5 Node Specification & Runbook

## Overview
The Raspberry Pi 5 is the primary on-premises execution node in the personal AI infrastructure. It hosts:
- **Hermes Agent**: Autonomous tool-calling agent connected upstream to the AI Gateway (`https://ai.bchbenjamin.in/codex/v1`).
- **Beeper Desktop**: Persistent messaging bridge running as a systemd service with a local OAuth-authenticated MCP server.
- **computer-use-linux**: System automation MCP server operating over Wayland (`labwc` virtual display `NOOP-1`).
- **Secondary SSD Storage**: 256 GB ext4 partition mounted at `/mnt/pi_data` for durable, non-boot data storage.

## Files
- `node-spec.yaml`: Exact hardware, filesystem, and service profile of this node.
- `install.sh`: Idempotent node provisioning script.
- `verify.sh`: Health and diagnostic verification script.

## Verification
To run health checks on this node:
```bash
bash nodes/pi5/verify.sh
```
