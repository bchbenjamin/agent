# ADR 0001: Two-Layer Isolation Architecture

## Context
Personal AI infrastructure needs access to sensitive local systems (chat databases, local desktop controls, edge compute), while relying on external model providers for inference. If the model inference gateway is coupled to the personal infrastructure, prompt injection or compromised API keys could directly expose edge devices.

## Decision
Strictly separate Layer 1 (Independent AI Gateway) from Layer 2 (Personal AI Infrastructure).
- Layer 1 (`ai.bchbenjamin.in`) provides raw LLM inference routing and has zero access to personal files, databases, or local devices.
- Layer 2 (`api.hermes.bchbenjamin.in`) orchestrates nodes and personal context, querying Layer 1 solely as an external inference client.

## Consequences
- Protects personal data from prompt injection attacks.
- Enables seamless switching of model providers without altering edge node configurations.
- Guarantees zero reverse ingress from the AI Gateway into private infrastructure.
