# Native Hermes contract for the owner web frontend

The web server holds the native Hermes downstream bearer key and verifies the authenticated owner before calling Hermes. Keep the key and relay URL server-side. Never accept a browser-supplied bearer, arbitrary upstream URL, or arbitrary session header. The Personal AI API and MCP use separate credentials.

## Routes

With the public Hermes base `https://ai.bchbenjamin.in/_ingress/http/api/v1`, append `/models`, `/capabilities`, `/chat/completions`, `/responses`, or `/runs`. Derive the history prefix by removing only the final `/v1` segment and appending `/api/sessions`. Retain `/_ingress/http/api`.

- `GET /api/sessions?source=telegram&limit=25&offset=0` lists existing Telegram conversations. Session metadata includes stable ID, source, title, timestamps, and message and tool counts.
- `GET /api/sessions/{id}/messages?limit=40&offset=0&order=latest` returns the resolved session ID and pagination. Messages carry the role and content, and tool records add tool name, call ID, arguments or result. Preserve call IDs when rendering related records.
- `POST /api/sessions` with `{"title":"New web conversation"}` creates an isolated web session. Send web writes only to owner-mapped web sessions. Display Telegram history read-only. The bare bearer can read both sources, so this policy belongs in the web server's authorization and session mapping.
- `POST /api/sessions/{id}/chat/stream` takes `{"message":"A user request"}`. Keep the explicit session ID, and use the effective ID returned by Hermes. For Chat Completions set `X-Hermes-Session-Id`. Gateway commit `c4b4876` forwards `X-Hermes-Session-Key` in both directions; refresh the installed connector policy to that revision before testing continuity. For Responses chaining use the previous response ID as supported by Hermes.

## Events and run control

Native session streaming uses named SSE frames with `session_id`, `run_id`, `seq`, and `ts`. A sanitized example:

```text
event: tool.started
data: {"session_id":"api_disposable","run_id":"run_disposable","seq":3,"ts":0,"message_id":"msg_disposable","tool_name":"context_query","preview":"Looking up context","args":{}}

event: tool.completed
data: {"session_id":"api_disposable","run_id":"run_disposable","seq":4,"ts":0,"message_id":"msg_disposable","tool_name":"context_query","preview":"Completed","args":{}}
```

Use `assistant.delta` for incremental text. Terminal events include `assistant.completed` and `run.completed`, `run.failed`, or `run.cancelled`, followed by `done`. On completion use the returned transcript or fetch session messages for tool results. Progress previews may be truncated and should not replace canonical results.

For explicit cancellation, `POST /v1/runs` persists the returned run ID and `POST /v1/runs/{id}/stop` requests interruption. Poll `GET /v1/runs/{id}` for the terminal status. An early stop on a native session stream may return 409. Do not interpret browser disconnect as proof of cancellation.

An `approval.request` carries run/request IDs, a redacted prompt, and allowed choices. Render only those choices. POST `{"request_id":"request_disposable","choice":"once"}` to `/v1/runs/{id}/approval` only after an explicit owner decision. Show the result from Hermes. Personal AI task approval is a different, private control-plane operation.

Use 401 for authentication failure, 404 for an unavailable route, and the relay's 503 response to distinguish an offline/busy connector from an unconfigured deployment. Do not automatically resubmit a mutation after an ambiguous response or truncated stream. Preserve user input for explicit recovery.

Citations and artifacts stay attached to structured tool results when provided. Native web search and extraction can remain in Hermes. A supplementary research MCP can return stable citation records with URLs and titles plus a human-readable answer. Do not assume every assistant stream or Telegram message exposes a structured citation schema. Treat artifact links as owner-only, validate their origin, and never serve arbitrary Pi paths.
