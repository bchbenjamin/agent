# External intelligence clients: Hermes MCP

This is a direct tool interface, not an inference proxy. ChatGPT, Claude, Gemini or a local MCP host can supply reasoning while the existing Pi control plane executes tasks. Hermes Agent remains a separate client of the same context index. No AI Gateway key is required.

## Transport and authentication

- Existing loopback: `http://127.0.0.1:8765/mcp` (Streamable HTTP).
- Existing Render relay: `https://ai.bchbenjamin.in/_ingress/http/mcp/mcp`. This depends on Render's **transport**, not on its inference providers; it is not a solution to a Render outage or edge rejection.
- For private desktop/CLI clients, use a separately authenticated Tailscale/SSH transport to the loopback listener. Do not expose it anonymously.
- Claude remote custom connectors support a fixed Authorization header. For ChatGPT, use the supported OAuth client flow or Secure MCP Tunnel with appropriate authentication; do not put a bearer in a URL, turn off authentication or assume account eligibility. OAuth is not implemented by this adapter. Gemini custom MCP availability depends on the account and supported surface.
- Issue a distinct `external-brain` token per client. Do not use the bootstrap admin token. Start with `context:read,nodes:read,terminal:execute`; add `context:write`, `box:read` and `beeper:read` only as explicitly desired. Never grant `tasks:approve` or `nodes:admin` to an external brain.
- Example on the Pi (run locally, protect the result):
  `sudo -u pai-api env PAI_DB_PATH=/mnt/pi_data/personal-ai/pai.sqlite3 /opt/personal-ai/.venv/bin/python -m personal_ai_api.cli issue-token --client-id claude-external --client-type external-brain --scopes context:read,nodes:read,terminal:execute,context:write`
- Revocation: use the existing `revoke-client` command. Keep client credentials in the client credential store, never chat or Git.

## Capability and memory policy

Use `client_capabilities`, `list_nodes`, `submit_task` and `get_task`. Only fixed health probes are directly queued for external brains. Other exec and shell operations require the independent owner approval workflow. Poll an existing task ID; never repeat a mutation after an ambiguous response.

Use `query_context`, then `read_context_document` with pagination, then `remember_context` for explicitly approved facts, outcomes or selected conversations. `owner_confirmed` is a client assertion, not an independently authenticated consent record. The server uses client-scoped provenance and content-addressed IDs, so identical records are idempotent and external clients cannot overwrite ordinary indexed documents via the index endpoint. No automatic bulk export, arbitrary chat history access, native MEMORY.md synchronization or implicit memory write is implemented.

Hermes itself must consult its personal_ai MCP context tools at task start and after substantial work. Install the supplied instruction skill or add its guidance to the existing owner-controlled instructions; do not replace Hermes's own memory or history.

Optional direct read integrations: set `PAI_BOX_MCP_TOKEN` and/or `PAI_BEEPER_MCP_TOKEN` locally in the existing protected `/etc/personal-ai/mcp.env` using dedicated authorized credentials. Beeper supports a manually issued access token; preserve Hermes's existing OAuth configuration. `list_integrations` and `read_integration` use fixed upstream destinations and explicit read-only tool allowlists. They are disabled by default without credentials and enforce separate client scopes. Full Box execution, Beeper sends, GUI control, native Hermes history access and richer permission/approval mediation are subsequent work. Do not pretend that these tools already expose all Hermes capabilities.

## Upgrade and acceptance

On the Pi, verify the actual installed repository and service paths, inspect local changes, back up the SQLite database using SQLite's online backup interface and back up the installed source. Apply only the new reviewed tracked files to the existing root-owned /opt/personal-ai checkout, retaining venv, configs, tokens, and systemd units. Do not rerun first-install provisioning. Run tests against a temporary database, then restart personal-ai-api and personal-ai-mcp only. Check active services and the existing ingress policy; no new public API write routes are needed because memory writes pass through authenticated MCP to loopback API.

Test with a fresh restricted external-brain credential, initially over loopback, then the supported private or public transport: initialize and list tools, client identity, node status, queue hostname and poll the existing task until completed, query a benign indexed document, explicitly approve a synthetic memory record, read it from the separate Hermes client, restart MCP and read again. Verify a read-only client cannot write and an external-brain client cannot self-approve or access a task owned by another client. Test optional integrations using invented search text, not real chat content. Verify Gateway inference is not called during any of these operations. Do not claim a client connection or a live device test until actually observed.
