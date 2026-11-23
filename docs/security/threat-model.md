# Threat Model & Security Posture

## 1. Assets
- **Personal Chat History**: Beeper message databases and attachments.
- **Node Access**: Shell and command execution on the Raspberry Pi 5.
- **Inference Gateways**: API tokens and quota for external LLM inference.
- **Personal Files**: Documents and storage on `/mnt/pi_data`.

## 2. Threat Scenarios & Mitigations

### Threat: Malicious Prompt Injection via External AI Model
- **Vector**: An external completion attempts to instruct the agent to exfiltrate private files.
- **Mitigation**:
  - The AI Gateway has no network path into local nodes.
  - The unprivileged node agent cannot execute arbitrary destructive commands.
  - All tools require explicit permission scopes.

### Threat: Stolen Client Credential (e.g. Morphic or Telegram)
- **Vector**: An attacker steals a client token.
- **Mitigation**:
  - Granular scopes: A Morphic token cannot execute `services:manage` or `nodes:admin`.
  - Immediate token revocation: TokenManager marks hash invalid immediately.
  - Audit logging records every invocation with IP and client ID.
