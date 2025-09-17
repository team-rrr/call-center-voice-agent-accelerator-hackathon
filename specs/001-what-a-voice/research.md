# Phase 0 Research Findings

Date: 2025-09-17
Feature: Voice-Enabled Multi-Agent Orchestration Accelerator
Branch: 001-what-a-voice

## Method
Extracted unknowns & focal points from spec + constitution. Refocused on minimal schemas, basic orchestration pattern, and resilience (latency/consent/export deferred).

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

### 4. Event Naming (Simplified)
- Decision: Minimal event type strings only; no correlation ids in MVP.
- Rationale: Reduce overhead; instrumentation deferred.
- Alternatives: Full correlation & structured logging (added complexity) rejected.

### 5. Barge-In Handling Strategy
- Decision: On new user audio onset while TTS streaming, issue stop signal to TTS engine and flush pending audio buffer; emit `barge_in` event.
- Rationale: Minimizes perceived latency; required by FR-011/FR-029.
- Alternatives: Let audio finish (hurts UX) rejected.

### 6. Circuit Breaker Thresholds
- Decision: Open breaker when 5 consecutive model call failures OR 50% failure over rolling 60s.
- Rationale: Protect latency and avoid cascading retries.
- Alternatives: Higher thresholds delay recovery; lower cause flapping.

### 7. (Removed) Transcript Export / Redaction
### 8. (Removed) Consent Revocation Flow
### 9. (Removed) Latency Measurement Harness
### 10. Quota & Cost Pre-Deploy Script
- Decision: Script queries model quota usage + estimated cost from configurable threshold; fails if >90% quota or budget warning threshold exceeded.
- Rationale: Constitution cost gate compliance.
- Alternatives: Manual review error-prone.

## Open Questions (To Resolve in Phase 1)
1. Do we impose a max tasks per session now or later? (Leaning later once planner exists.)

## Risk Log
| Risk | Impact | Mitigation |
|------|--------|------------|
| Latency regression with added instrumentation | Miss P95 target | Measure overhead early; optimize log path |
| Planner task explosion | Resource overuse | Enforce max tasks/session (TBD Phase 1) |
| (Removed features) Consent/export gap | None (out of scope) | Reintroduce in post-MVP roadmap |

## Decisions Summary
All critical unknowns for MVP resolved; removed features documented for future phases.

## Status
Phase 0: COMPLETE
