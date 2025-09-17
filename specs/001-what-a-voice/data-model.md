# Data Model (Phase 1 Draft)

Date: 2025-09-17
Feature: Voice-Enabled Multi-Agent Orchestration Accelerator

## Overview
Derived from feature spec FR-001..FR-030 and Phase 0 research. Emphasis on minimal viable entities and clear state transitions.

## Entities

### Session
Fields:
- id (UUID)
- status (enum: active, ended)
- start_time (datetime)
- end_time (datetime|null)
- user_role (enum: standard, elevated)
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
- Max tasks per session (placeholder): propose cap=25 to prevent overload (finalize later).

## Versioning
Initial model version 0.1.0 aligned with constitution version.
