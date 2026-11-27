# External chatbot clients

No inference API key is needed. Use a separate external-brain credential for each client, never the administrator or node credential. After the core MCP upgrade, run on the Pi:
```sh
sudo bash deployment/clients/issue-external-brain-token.sh chatgpt
```
The token is saved in the owner's existing protected credential directory. Enter its value directly into the chosen host's supported credential form; do not send it to the assistant, commit it, add it to a URL, or put it in a plugin archive. Re-running this helper retains the existing token.

## ChatGPT

The private Hermes Personal AI plugin was created in the owner's account with the existing public Streamable HTTP endpoint and API-key bearer authentication. Open the plugin's connection UI, install/connect explicitly and enter the separate ChatGPT token. The plugin does not grant approval or admin scope. Check tool discovery before using it. Its public transport still depends on Render.

## Claude

For Claude web, open Customize > Connectors, add a custom remote connector, use the same public MCP URL and, where available, add the request header Authorization: Bearer <Claude-specific token>. Never use the ChatGPT credential for Claude. Sign-in and token entry must be completed by the owner.

For Claude Code running directly on the Pi, merge the example MCP entry in claude-code-local.json into the existing client MCP configuration, without replacing other servers. The executable headers helper reads only the owner-local Claude token.

For Claude Code or a compatible MCP host running on an authenticated tailnet device, use an SSH tunnel instead of Render (replace PI_SSH_HOST with the actual known Pi Tailscale hostname or address):
```sh
ssh -N -T -o ExitOnForwardFailure=yes -L 127.0.0.1:18765:127.0.0.1:8765 bchbenjamin@PI_SSH_HOST
```
Use http://127.0.0.1:18765/mcp in that local client and a securely transferred client-specific token in its credential store. Do not disable SSH host-key verification. This is private and requires working SSH on the Pi; browser-hosted Claude/Gemini cannot reach a loopback address on your device.

## Gemini

The owner's Gemini web Developer Mode offers an HTTPS MCP URL and optional OAuth client ID and secret. It does not show a custom bearer header input. OAuth resource-server integration is still required for this client unless Google adds a supported token flow. Do not disable authentication or pass a token in the URL.

## Tests

Run the existing local protocol verifier with the client token file (no secret is printed). Verify client identity, tool list, then queue a read-only hostname task and poll its ID. Inspect optional integrations individually and preserve existing approvals.
