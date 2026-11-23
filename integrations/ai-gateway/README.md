# Independent AI Gateway (Layer 1) Integration

## Strict Isolation Guarantee
The AI Gateway (`https://ai.bchbenjamin.in`) is an independent inference service.
- **Role**: Routes completions to external model providers (Anthropic, OpenAI, custom).
- **Outbound Only**: Layer 2 (Hermes, Personal AI API) queries the AI Gateway for completions.
- **Zero Ingress**: The AI Gateway has no network route, credentials, or permissions to access personal nodes, databases, or devices.
- **Repository Separation**: The AI Gateway maintains its own independent repository and deployment lifecycle.
