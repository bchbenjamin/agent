# Redmi Note 5 Pro Node Specification

## Purpose
The Redmi Note 5 Pro is designated as an auxiliary mobile edge worker. It provides:
- Redundant messaging observation.
- Lightweight batch tasks and sandbox test execution.
- Battery-backed uptime during power outages.

## Architecture
- **OS**: Android / Linux container runtime (proot / postmarketOS).
- **Agent**: Lightweight Python `node-agent` communicating outbound over Tailscale to `api.hermes.bchbenjamin.in`.
- **Note**: DroidSpaces is not assumed; deployment proceeds via standard Linux userspace.
