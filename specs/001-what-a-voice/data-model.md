# Data Model (Phase 1 Draft)

Date: 2025-09-17
Feature: Voice-Enabled Multi-Agent Orchestration Accelerator

## Overview
Aligned with trimmed MVP FR-001..FR-023 after scope reduction. Removed deferred constructs (language, metrics, multi-role access, advanced arbitration, consent/export). Emphasis on only what runtime presently needs plus forward-compatible placeholders (Task, ToolInvocation).

## Entities

### Session
Fields:
- id (UUID)
- status (enum: active, ended)
- start_time (datetime)
- end_time (datetime|null)
- version (string semver)

Removed (deferred): user_role, language, metrics summary.

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

<!-- ConsentRecord and TranscriptExport removed for simplified MVP scope -->

## Relationships
- Session 1..* Utterance
- Session 1..* Task
- Task 1..* ToolInvocation
<!-- ConsentRecord and TranscriptExport relationships removed -->

## Derived / Computed Fields
- Task.progress: computed from internal executor events; default increments or explicit updates.

## Invariants / Constraints
- A session with status ended MUST have end_time set.
- Utterance.interrupted true => following agent audio was cut short event logged.
- Task.result_summary present only if status in (succeeded, failed, canceled).

## Open Items
- Task cap per session deferred (low complexity in MVP traffic expectation).
*- Consider re-introducing metrics object once observability phase resumes.*

## Versioning
Initial model version 0.1.0 aligned with constitution version.
