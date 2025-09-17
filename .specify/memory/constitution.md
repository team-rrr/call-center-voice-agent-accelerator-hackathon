# Call Center Voice Agent Accelerator Constitution

Minimal, enforceable engineering contract for this Python web application integrating:
1. Azure Communication Services (voice-live API) for bi-directional audio.
2. Semantic Kernel multi-agent orchestration published to Azure AI Foundry.
3. Secure, observable, testable delivery on Azure.

## Core Principles

### 1. Secure-by-Default
All credentials resolved via Managed Identity or Key Vault; no secrets committed. Principle of least privilege for Azure resources; threat / abuse cases considered for every external interaction (voice, agent actions, prompt injections).

### 2. Deterministic Contracts First
Interfaces (voice event schema, agent message schema, tool invocation shapes) defined before implementation; changes require version bump + migration note.

### 3. Test-First & Fast Feedback
Unit tests for agent logic, prompt function routing, and voice event handlers precede feature code. Any regression requires adding / tightening a test. CI gate: lint + type check + tests must pass in < 5 min.

### 4. Observability & Traceability
Structured JSON logging (correlation_id, call_id, agent_id). Azure Monitor / App Insights (traces + latency + error rate). No silent except blocks; failures surfaced with context.

### 5. Minimal Surface, Incremental Complexity
Ship the smallest viable agent behaviors; defer speculative tools. Remove unused prompts/skills before release. Prefer composition over deep inheritance.

### 6. Performance & Resilience
Streaming audio latency budget: < 800ms end-to-end (capture → agent response start). Retries with exponential backoff for transient Azure SDK calls. Circuit breaker for downstream model unavailability; graceful degradation (fallback agent or canned response).

### 7. Ethical & Responsible AI
Disclose AI involvement in call greeting. Log user opt-out requests. No storage of raw PII beyond retention window (configurable). Prompt templates avoid sensitive data persistence.

## Architecture & Technology Constraints
- Language: Python 3.11+ (match runtime in `server/pyproject.toml`).
- Web tier: Single container (Container Apps or App Service) exposing WebSocket / HTTP endpoints for voice session control.
- Agents: Implemented via Semantic Kernel planners / orchestration; multi-agent topology defined declaratively (YAML/JSON) and published to Azure AI Foundry.
- Voice Integration: ACS voice-live events processed by handler layer (`app/handler/*`). Media streaming uses secure WebSocket; audio codecs standardized (PCM 16-bit 16kHz unless platform forces alternative).
- Configuration: Env vars only (12-factor). Mandatory: `AI_FOUNDRY_ENDPOINT`, `ACS_RESOURCE`, `DEFAULT_MODEL`, `LOG_LEVEL`.
- Package Policy: Pin direct prod deps; use caret only for dev tooling. Security scan (dependabot or equivalent) weekly.
- Data Stores: Introduce new persistent storage only with documented query / latency need; otherwise reuse existing telemetry or ephemeral cache.
- Agent Registry: Each agent definition includes: purpose, allowed tools, guardrails (max tokens, escalation conditions). Version every change.

## Development Workflow & Quality Gates
1. Define Contract: Add / update schema (OpenAPI / JSON Schema) for any new endpoint or agent message type.
2. Add Tests: Unit + (if cross-service) integration stub tests. Voice event replay fixtures for new scenarios.
3. Implement Feature: Keep functions < 60 lines where practical. Pure logic separated from IO for testability.
4. Observability Hooks: Ensure new paths emit structured logs + metrics.
5. Review Checklist (must answer YES): Secrets externalized? Tests added & passing? Latency impact acceptable? Logs structured? Schema versioned?
6. CI Gates: black/ruff (style & lint), mypy (strict optional), pytest (>=90% branch coverage for `app/handler` & agent orchestration modules), container build, security scan (bandit + dependency audit).
7. Release: Semantic versioning (MAJOR breaking schema, MINOR new non-breaking capability, PATCH fixes). Tag + changelog entry required.
8. Cost & Quota Gate: Deployment job asserts quota + budget headroom; rejects if >90% quota consumption for primary model.
9. Agent Validation: Before publishing agent changes, run scenario tests validating: (a) tool usage constraints enforced, (b) escalation path triggers on ambiguous intent, (c) no prompt injection bypass for restricted tools.
10. Teardown Hygiene: Non-production ephemeral environments auto-destroy after 24h inactivity or upon PR close.

## Governance
This constitution overrides ad-hoc practices. Any amendment requires: (a) rationale, (b) impact assessment (performance, security, developer workflow), (c) migration steps, (d) version increment here. Pull Requests must quote the Principle(s) satisfied or amended in the description. Non-compliant code cannot merge.
Responsible AI transparency file (FAQ) must be kept current with any new model, agent, or data source integration; link added in README when updated.

## Versioning
Version: 0.1.0 | Ratified: 2025-09-17 | Last Amended: 2025-09-17

Change Log Summary:
- 0.1.0 Initial minimal constitution established.