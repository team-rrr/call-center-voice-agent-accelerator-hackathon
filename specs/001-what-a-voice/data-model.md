# Data Model (Phase 1 Draft)

Date: 2025-09-17
Feature: Voice-Enabled Multi-Agent Orchestration Accelerator

## Overview
Derived from feature spec FR-001..FR-030 and Phase 0 research. Emphasis on minimal viable entities and clear state transitions.

## Entities

### Session
Fields:
- id (UUID)
- status (enum: active, inactive, ended, consent_revoked)
- start_time (datetime)
- end_time (datetime|null)
- language (enum: en, es, fr)
- user_role (enum: standard, elevated)
- metrics (object: latency_ms_first_response, utterance_count, task_count, avg_confidence)
- version (string semver)

### Utterance
Fields:
- id (UUID)
- session_id (UUID FK Session)
- text (string)
- confidence (float 0..1)
- start_time (datetime)
- end_time (datetime)
- interrupted (bool)

Validation:
- confidence >= 0 and <= 1
- length(text) > 0

### Agent
Fields:
- name (string)
- version (string semver)
- purpose (string)
- allowed_tools (array[string])
- guardrails (object: max_tokens:int, escalation_policy:string)

### Task
Fields:
- id (UUID)
- session_id (UUID FK Session)
- originating_agent (string FK Agent.name)
- status (enum: queued, running, succeeded, failed, canceled)
- created_at (datetime)
- updated_at (datetime)
- result_summary (string|null)
- error_code (string|null)
- progress (int 0..100)

State Transitions:
queued -> running -> succeeded | failed | canceled
running -> canceled

### ToolInvocation
Fields:
- id (UUID)
- task_id (UUID FK Task)
- tool_name (string)
- parameters (object sanitized)
- outcome_status (enum: success, error)
- duration_ms (int)
- timestamp (datetime)

### ConsentRecord
Fields:
- session_id (UUID PK/FK Session)
- acknowledged_at (datetime)
- revoked_at (datetime|null)
- active (bool)

### TranscriptExport
Fields:
- id (UUID)
- session_id (UUID FK Session)
- created_at (datetime)
- format (enum: json, text)
- redaction_version (string)
- hash_salt_version (string)

## Relationships
- Session 1..* Utterance
- Session 1..* Task
- Task 1..* ToolInvocation
- Session 1..1 ConsentRecord
- Session 0..* TranscriptExport

## Derived / Computed Fields
- Session.metrics.latency_ms_first_response: difference between last utterance end_time and first agent response timestamp.
- Task.progress: computed from internal executor events; default increments or explicit updates.

## Invariants / Constraints
- A session with status ended MUST have end_time set.
- Consent revocation sets Session.status=consent_revoked; no further TranscriptExport allowed.
- Utterance.interrupted true => following agent audio was cut short event logged.
- Task.result_summary present only if status in (succeeded, failed, canceled).

## Open Items
- Max tasks per session (placeholder): propose cap=25 to prevent overload (to finalize during contract definition).
- Progress minimum update interval: default 10s (align FR-025).

## Versioning
Initial model version 0.1.0 aligned with constitution version.
