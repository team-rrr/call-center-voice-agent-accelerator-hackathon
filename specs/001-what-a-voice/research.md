# Phase 0 Research Findings

Date: 2025-09-17
Feature: Voice-Enabled Multi-Agent Orchestration Accelerator
Branch: 001-what-a-voice

## Method
Extracted unknowns & focal points from spec + constitution. Focused on latency, schemas, orchestration patterns, resilience, consent, and observability.

## Findings

### 1. Azure Speech vs ACS Voice Live Integration
- Decision: Use Azure Speech SDK for transcription + TTS; ACS (optional) only if telephony ingress needed.
- Rationale: Speech SDK lower friction for browser client, stable latency; ACS adds capability but increases setup.
- Alternatives: ACS-only (higher complexity), 3rd party STT (violates minimal principle).

### 2. Semantic Kernel Planner + Executor Pattern
- Decision: Implement a lightweight planner agent that emits task graph; executor processes tasks sequentially or in limited parallel (<=2) to preserve resource use.
- Rationale: Simplicity + transparency. Full DAG engine unnecessary at prototype scale.
- Alternatives: Full workflow engine (Temporal, Prefect) rejected (overhead, scope creep).

### 3. JSON Schemas (Session, Utterance, Task, AgentMessage, ErrorEvent)
- Decision: Define base schemas with $id and semantic version field; compose via references.
- Rationale: Contracts-first principle; enables validation + future evolution.
- Alternatives: Ad-hoc Pydantic only (harder external consumption) rejected.

### 4. Event Naming & Correlation
- Decision: correlation_id per session; each event includes event_id (UUIDv7), timestamp (RFC3339), type.
- Rationale: Traceability & analytics alignment.
- Alternatives: Incremental counters (hard in distributed cases) rejected.

### 5. Barge-In Handling Strategy
- Decision: On new user audio onset while TTS streaming, issue stop signal to TTS engine and flush pending audio buffer; emit `barge_in` event.
- Rationale: Minimizes perceived latency; required by FR-011/FR-029.
- Alternatives: Let audio finish (hurts UX) rejected.

### 6. Circuit Breaker Thresholds
- Decision: Open breaker when 5 consecutive model call failures OR 50% failure over rolling 60s.
- Rationale: Protect latency and avoid cascading retries.
- Alternatives: Higher thresholds delay recovery; lower cause flapping.

### 7. Transcript Export Redaction
- Decision: Exclude tool invocation parameters flagged sensitive; hash user identifiers (SHA256 salt env-provided) before export.
- Rationale: Privacy + minimal retained PII.
- Alternatives: Full raw export (privacy risk) rejected.

### 8. Consent Revocation Flow
- Decision: Mark session state consent_revoked; cease new persistence (logs limited to operational minimal), disable transcript export, allow continuation ephemeral.
- Rationale: Align with Responsible AI principle.
- Alternatives: Immediate forced termination (poor UX) rejected.

### 9. Latency Measurement Harness
- Decision: Timestamps at pipeline stages: audio_end, stt_complete, intent_routed, agent_response_start, first_audio_chunk_sent. Compute deltas; emit metrics.
- Rationale: Enables verification of <1500ms initial response.
- Alternatives: Coarse total-only metric hides bottlenecks.

### 10. Quota & Cost Pre-Deploy Script
- Decision: Script queries model quota usage + estimated cost from configurable threshold; fails if >90% quota or budget warning threshold exceeded.
- Rationale: Constitution cost gate compliance.
- Alternatives: Manual review error-prone.

## Open Questions (To Resolve in Phase 1)
1. Do we need an explicit progress update minimum interval override per task type? (Default 10s acceptable for now.)
2. Should multilingual fallback attempt auto-detect or enforce specified language list? (Plan: auto-detect, clamp to supported.)

## Risk Log
| Risk | Impact | Mitigation |
|------|--------|------------|
| Latency regression with added instrumentation | Miss P95 target | Measure overhead early; optimize log path |
| Planner task explosion | Resource overuse | Enforce max tasks/session (TBD Phase 1) |
| Consent revocation partial logging gap | Compliance issue | Add unit test for state transition coverage |

## Decisions Summary
All critical unknowns resolved; remaining questions non-blocking and deferred to Phase 1 design refinement.

## Status
Phase 0: COMPLETE
