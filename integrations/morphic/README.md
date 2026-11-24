# Morphic Frontend Integration

Morphic is the chat UI at hermes.bchbenjamin.in. Its server-side backend calls the Personal AI API at api.hermes.bchbenjamin.in.

- Use a dedicated client token with context:read, nodes:read, terminal:execute, services:manage and tasks:approve.
- Store the token only in the Morphic server environment as PAI_API_TOKEN.
- Never expose it as a browser/client-prefixed environment variable or include it in frontend JavaScript.
- Use GET /v1/tasks/pending-approval to render the owner approval queue and POST /v1/tasks/{task_id}/approve for explicit approval.
- Use GET /v1/nodes and GET /v1/tasks/{task_id} for node/task status.
- The API Gateway key is not a Personal AI API credential and must never be reused here.
