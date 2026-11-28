# Deployment inventory and known limits

Repository: https://github.com/bchbenjamin/agent
Last known source baseline before Oracle consolidation: 58d8ede.
This inventory describes known configuration and owner-reported deployment
steps, not an automatically collected live inventory.

## Current Pi

- Raspberry Pi 5 4 GB, aarch64; permanent 64 GB microSD boot.
- 256 GB OSC SSD, ext4, UUID cbdf283b-2951-44de-945e-c082bf87f337,
  mounted at /mnt/pi_data; control-plane DB /mnt/pi_data/personal-ai/pai.sqlite3.
- Owner bchbenjamin; system services personal-ai-api, personal-ai-mcp,
  personal-ai-node, beeper, tailscaled; user Hermes gateway
  hermes-gateway-e86e8d0b and ingress/origin services. Verify enablement
  and lingering on actual machine; systemd active alone is not enough.
- Canonical runtime ~/.hermes-pi, application ~/.hermes, installed control
  plane /opt/personal-ai and protected configs /etc/personal-ai.
- Core services enabled in earlier Pi report. Owner subsequently reported
  executing upgrade and integration script; actual post-upgrade thirteen
  tool discovery and reboot acceptance have not been independently observed.
- Beeper local MCP port 23373, Hermes native API 8642, Personal AI API
  8000, MCP 8765, Caddy origin 18080. Existing Pi relay uses
  https://ai.bchbenjamin.in/_ingress/http/mcp/mcp.
- Direct Gemini fallback removed per Pi report; primary Gateway unchanged.
- Pi/Box execution roles, Redmi/Instabox inference roles. Box is not
  connected to Pi Tailscale as last observed; no Tailscale Funnel configured.

## External clients

- Private ChatGPT plugin Hermes Personal AI v0.1.0:
  https://chatgpt.com/plugins/plugins_6b099ab6900881918f465e9e79b73a8f
  Existing plugin ID plugins_6b099ab6900881918f465e9e79b73a8f.
  Config uses API-key bearer and existing Render relay. Created and stored,
  not independently authenticated or tested live.
- Claude web sign-in was required in Box. Claude Code local config and
  headers helper are in deployment/clients. Dedicated tokens under
  ~/.config/personal-ai/external-brain; no raw credentials in Git.
- Gemini Developer Mode was observed with custom HTTPS MCP and OAuth client
  ID/secret inputs. No fixed header input; OAuth integration pending.
- Morphic frontend https://hermes.bchbenjamin.in uses native Hermes relay.
  Preserve the original UI and owner authentication. Do not store its
  deployment secrets in this repository.

## Capability baseline

13 tools: list_nodes, get_node_status, submit_task, get_task, query_context,
client_capabilities, read_context_document, remember_context,
list_integrations, read_integration, box_health_probe,
list_native_conversations, read_native_conversation.
External-brain tokens cannot have nodes:admin or tasks:approve. Box health
probes, read-only Beeper, read-only history, approved context records only.
No automatic full chat export, native memory sync, arbitrary Box execution,
external desktop control or Beeper mutation. Current client tools are
independent of Gateway inference, not necessarily Render network transport.

## Reboot verification

Run nodes/pi5/verify.sh, check enabled units and user linger, then run
deployment/install/verify-external-brain-mcp.py with the owner-local token.
Verify actual authenticated hostname, memory retrieval, Beeper and Box
separately. Check public relay with authorized client; 401 alone is not
a proof of successful tool calls. Never print credentials or conversations
in diagnostics. A crash-interrupted task may require reconciliation.

The repository's storage-recovery timer keeps the API and MCP stopped until
the expected SSD UUID is mounted, then retries service activation. It never
mounts or fscks the device. On the 2026-11-28 post-boot inspection, that timer
was not yet installed on the host. The SSD UUID was absent, kernel logs showed
repeated undervoltage and USB disconnects, and the API/MCP correctly remained
inactive behind their mount dependencies. Beeper was running as a user-started
desktop process while its system unit had failed on a dangling AppImage path;
the stable symlink now resolves to the installed 4.3.366 image, but the
root-owned unit still needs installation/reset. Recheck after stabilizing the
USB power path; don't claim reboot recovery before authenticated MCP execution
succeeds.
