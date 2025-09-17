# Research: Foundry Integration

Decisions
- Use an async HTTP client (httpx.AsyncClient) with ManagedIdentityCredential / DefaultAzureCredential for AAD tokens.
- Keep HTTP endpoints simple: `/events/call` and `/events/transcript` for starter contract.
- Add `ai_foundry_client.py` as a small, testable module under `server/app/`.

Rationale
- httpx provides a robust async client and is already present in `pyproject.toml`.
- Managed Identity and DefaultAzureCredential are recommended per Azure best practices.

Alternatives considered
- Direct SDK: No official Foundry SDK assumed; HTTP is simplest and portable.
