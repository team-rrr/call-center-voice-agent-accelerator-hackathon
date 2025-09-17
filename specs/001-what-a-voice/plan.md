
# Implementation Plan: Voice-Enabled Multi-Agent Orchestration Accelerator

**Branch**: `001-what-a-voice` | **Date**: 2025-09-17 | **Spec**: `/Users/graham.schmidt/src/call-center-voice-agent-accelerator-hackathon/specs/001-what-a-voice/spec.md`
**Input**: Feature specification from `/specs/001-what-a-voice/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, or `GEMINI.md` for Gemini CLI).
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Primary outcome: Enable real-time, low-latency voice interaction where user speech is transcribed, intents decomposed into agent tasks, and responses streamed back while background tasks continue. Plan emphasizes contracts-first schemas (session, utterance, task), strict latency + confidence thresholds (P95 ≤1500ms initial response, transcription confidence ≥0.75), and ethical transparency + consent handling. Technical approach: FastAPI backend with WebSocket for audio/control, Semantic Kernel orchestrated agents (planner, executor, domain-specific), Azure Speech / ACS for voice capture + TTS, structured observability (JSON logs, correlation IDs), and minimal initial multilingual support (en, es, fr).

## Technical Context
**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI, Uvicorn, Semantic Kernel (Python), Azure SDK (Speech/Communication), Azure OpenAI (GPT-4/GPT-4o), Pydantic, pytest
**Storage**: None initially (ephemeral in-memory structures + Azure telemetry); future persistence gated by constitution
**Testing**: pytest (unit, integration, contract), coverage enforcement ≥90% for handlers & orchestration modules
**Target Platform**: Azure Container Apps (Linux x86_64)
**Project Type**: Web (backend API + lightweight static client)
**Performance Goals**: Initial response P95 ≤1500ms from utterance end; streaming start <800ms; barge-in handling <200ms cutover
**Constraints**: No committed secrets; managed identity only; log retention 30 days; rate limit 20 utterances / 60s / session; queue depth 5
**Scale/Scope**: Prototype scope (single container, ≤ concurrent 50 active sessions baseline testing)

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle / Gate | Planned Alignment | Risk / Mitigation |
|------------------|-------------------|-------------------|
| Secure-by-Default | Managed Identity, Key Vault for any future secrets, no local credentials | Enforce secret scanning in CI |
| Contracts First | JSON Schemas for session, utterance, task, agent message before implementation | Drift risk → schema version tags |
| Test-First & Fast Feedback | Contract + unit tests generated Phase 1 prior to logic | Performance tests TBD after baseline |
| Observability & Traceability | Structured JSON logs (correlation_id, session_id, agent_id) + metrics (latency, error rate) | Overhead: keep minimal fields first |
| Minimal Surface | Only planner, executor, domain agent (placeholder) initial; no speculative tools | Feature creep → change control via PR template |
| Performance & Resilience | Latency budgets codified; retries & circuit breaker patterns in design doc | Need measurement harness early |
| Ethical & Responsible AI | Transparency notice + consent revocation flow; redact PII in export | Ensure redaction unit tests |
| Cost & Quota Gate | Pre-deploy script validates model quota <90% usage | Script must fail fast |
| Agent Validation | Scenario tests enforce tool guardrails pre-publish | Keep registry YAML under review |
| Teardown Hygiene | Non-prod ephemeral env tags + auto-destroy policy | Tag enforcement script pending |

Initial Constitution Check: PASS (no violations requiring Complexity Tracking yet)

## Project Structure

### Documentation (this feature)
```
## Summary
Primary outcome: Enable real-time voice interaction where user speech is transcribed, intents decomposed into simple agent tasks, and responses streamed back while tasks complete. MVP deliberately omits: formal latency SLO measurement, multilingual support, consent revocation, transcript export, structured observability, and rate limiting to accelerate iteration using the already functional Quart async bridge.
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
# Option 1: Single project (DEFAULT)
**Primary Dependencies**: Quart, websockets, httpx, Azure SDK (Speech/Communication), Azure OpenAI (GPT-4/GPT-4o), (future) Semantic Kernel, pytest
├── models/
**Storage**: None (all in-memory; no persistence layer in MVP)
├── cli/
**Testing**: pytest (basic unit + WebSocket integration stubs)

**Target Platform**: Azure Container Apps (Linux x86_64)
├── contract/
**Project Type**: Web (single backend + static client)
└── unit/
**Performance Goals**: Qualitative responsiveness only (no instrumentation phase 1)
# Option 2: Web application (when "frontend" + "backend" detected)
**Constraints**: No committed secrets; managed identity if available; intent queue depth 5
├── src/
**Scale/Scope**: Prototype (≤50 concurrent sessions assumed; not enforced)
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# Option 3: Mobile + API (when "iOS/Android" detected)
api/
| Observability & Traceability | Basic console logging only (no structured metrics) | Faster iteration; add structured logs later |
| Performance & Resilience | Qualitative responsiveness; simple retries only | Avoid early instrumentation overhead |
| Ethical & Responsible AI | Transparency notice only (no consent revocation workflow) | Scope reduction for speed |
## Phase 0: Outline & Research
1. Validate Azure Speech vs ACS Voice Live integration sequence (latency tuning deferred).
   - For each NEEDS CLARIFICATION → research task
4. Define minimal event naming (no correlation ids in MVP).
   - For each integration → patterns task
7. (Removed) Transcript export / redaction deferred.
8. (Removed) Consent revocation flow deferred.
9. (Removed) Latency measurement harness deferred.
10. Quota & cost pre-deploy script responsibilities.
- Data Model: Entities (Session, Utterance, Task, Agent, ToolInvocation) [ConsentRecord, TranscriptExport removed]
- FR-001..FR-007 → Session + transcription + routing tests (foundational contract tasks)
- FR-008..FR-015 → Planner decomposition + background task lifecycle tasks
- FR-016..FR-020 → Session management (timeouts, transparency, arbitration, error handling, cancellation)
3. **Consolidate findings** in `research.md` using format:
5. Transparency
6. Arbitration
7. (Removed) Metrics & reporting deferred
6. Arbitration
7. (Removed) Metrics & reporting deferred

Parallelizable ([P]) candidates: Schema validation tests, basic planner routing, cancellation flow.

Complexity Guardrails: Target ≤25 tasks; merge or defer anything not essential to basic voice + agent loop.
1. Validate Azure Speech vs ACS Voice Live integration sequence & latency tuning best practices.
2. Evaluate Semantic Kernel patterns for multi-agent planner + executor composition (Python).
| Omitted structured observability | Speed of prototype | Structured layer adds friction now |
| Omitted latency instrumentation | Reduce upfront complexity | Instrumentation overhead not yet justified |
| Removed consent revocation & export | Narrow initial scope | Governance features not core to demo |
| Removed rate limiting & multilingual | Focus single-language baseline | Avoid branching & test surface early |
3. Determine minimal JSON schema set (session, utterance, task, agent_message, error_event).
4. Define event naming + correlation strategy aligning with observability principle.
5. Barge-in interruption handling strategies (audio stream cancellation patterns).
6. Circuit breaker thresholds for model unavailability (failure rate %, open duration).
7. Redaction model for transcript export (fields excluded, hashing approach if needed).
8. Consent revocation flow (state transition + log behavior).
9. Latency measurement harness design (capture timestamps along pipeline).
10. Quota & cost pre-deploy script responsibilities.

Status: COMPLETE

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Each story → integration test scenario
   - Quickstart test = story validation steps

5. **Update agent file incrementally** (O(1) operation):
   - Run `.specify/scripts/bash/update-agent-context.sh copilot` for your AI assistant
   - If exists: Add only NEW tech from current plan
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, agent-specific file

Planned Design Elements:
- Data Model: Entities (Session, Utterance, Task, Agent, ToolInvocation, ConsentRecord, TranscriptExport)
- Schemas: JSON Schema v2020-12 definitions under `contracts/`
- API Surface (initial):
   - POST /sessions (create)
   - GET /sessions/{id}
   - POST /sessions/{id}/utterances (text fallback)
   - WS /sessions/{id}/stream (bi-directional audio + events)
   - GET /sessions/{id}/tasks
   - POST /sessions/{id}/tasks/{task_id}/cancel
   - GET /sessions/{id}/export
   - POST /sessions/{id}/consent/revoke
- Event Types (over WebSocket): user_utterance, transcript_partial, transcript_final, agent_plan, task_started, task_progress, task_completed, task_failed, barge_in, clarification_needed, consent_revoked, session_summary, error.
- Test Stubs: Contract tests asserting required fields & validation failures.
- Metrics Draft: latency_ms (pipeline stages), active_sessions gauge, utterances_per_session histogram, transcription_confidence histogram.

Status: IN PROGRESS

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `.specify/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (contracts, data model, quickstart)
- Each contract → contract test task [P]
- Each entity → model creation task [P]
- Each user story → integration test task
- Implementation tasks to make tests pass

**Ordering Strategy**:
- TDD order: Tests before implementation
- Dependency order: Models before services before UI
- Mark [P] for parallel execution (independent files)

**Estimated Output**: 25-30 numbered, ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

Planned Mapping (Preview):
- FR-001..FR-007 → Session + transcription + routing tests (foundational contract tasks)
- FR-008..FR-015 → Planner decomposition + background task lifecycle tasks
- FR-016..FR-023 → Session management (timeouts, export, consent, transparency, arbitration, error handling)
- FR-024..FR-030 → Observability, rate limiting, multilingual, metrics

Prioritization Order:
1. Contracts & core session lifecycle
2. Transcription + intent routing + agent plan
3. Background task execution + progress
4. Interruption / barge-in
5. Consent + transparency + export
6. Arbitration & rate limiting
7. Metrics & reporting

Parallelizable ([P]) candidates: Schema validation tests, multilingual detection handling, metrics instrumentation scaffolding.

Complexity Guardrails: Fail fast if task list exceeds 35; merge or defer non-critical tasks.

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute tasks.md following constitutional principles)
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |


## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented (NONE)

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*
