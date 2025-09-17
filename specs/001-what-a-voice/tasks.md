# Tasks: Voice-Enabled Voice MVP (Feature 001-what-a-voice)

**Input**: Design documents from `/specs/001-what-a-voice/`
**Prerequisites**: `plan.md` (required), `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

Scope Note: Trimmed MVP excludes consent revocation, export endpoint, multilingual, advanced arbitration, structured observability, background task lifecycle UI, role-based access, metrics, rate limiting.

## Execution Flow (auto-generated)
```
1. Load plan.md & supporting docs
2. Generate test-first tasks from contracts, user stories, quickstart scenarios
3. Generate model tasks from data-model entities (Session, Utterance, Agent, Task, ToolInvocation)
4. Map integration (WebSocket stream, barge-in handling)
5. Add implementation tasks to satisfy failing tests
6. Add minimal polish & docs tasks
7. Provide parallel execution guidance ([P])
```

## Phase 3.1: Setup
- [ ] T001 Create base Python project structure (if missing) `server/` submodules: `server/models/`, `server/services/`, `tests/` (skip if already present)
- [ ] T002 Initialize dependency alignment: ensure `pyproject.toml` includes quart, websockets, httpx, openai, azure-communication-callautomation (or ACS equivalent), pytest
- [ ] T003 [P] Add basic test config `tests/conftest.py` with pytest fixtures (event loop, test client)
- [ ] T004 [P] Add `.env.example` documenting required env vars (TTS_VOICE, OPENAI_MODEL, OPENAI_API_KEY or managed identity note)

## Phase 3.2: Tests First (TDD) — MUST FAIL BEFORE IMPLEMENTATION
Contract Schemas (each → validation test):
- [ ] T005 [P] Contract test `tests/contract/test_session_schema.py` validating `contracts/session.schema.json`
- [ ] T006 [P] Contract test `tests/contract/test_utterance_schema.py` validating `contracts/utterance.schema.json`
- [ ] T007 [P] Contract test `tests/contract/test_task_schema.py` validating `contracts/task.schema.json`
- [ ] T008 [P] Contract test `tests/contract/test_agent_message_schema.py` validating `contracts/agent-message.schema.json`
- [ ] T009 [P] Contract test `tests/contract/test_error_event_schema.py` validating `contracts/error-event.schema.json`

Integration / Scenario Tests (from user story + quickstart, adjusted for MVP):
- [ ] T010 Integration test start session (POST /sessions placeholder) & health endpoint `tests/integration/test_session_start.py`
- [ ] T011 [P] Integration test WebSocket stream basic flow (session_started → transcript_partial → transcript_final → agent_response → session_ended) `tests/integration/test_stream_basic.py`
- [ ] T012 [P] Integration test barge-in (interrupt playback) `tests/integration/test_barge_in.py`
- [ ] T013 [P] Integration test redact long digit sequences in transcript `tests/integration/test_redaction.py`
- [ ] T014 Integration test context truncation when exceeding turn budget `tests/integration/test_context_truncation.py`
- [ ] T015 [P] Integration test error event emission on simulated upstream failure (LLM/TTS) `tests/integration/test_error_events.py`

Unit / Component Tests (pre-implementation scaffolds):
- [ ] T016 [P] Unit test retry helper for transient failures `tests/unit/test_retries.py`
- [ ] T017 [P] Unit test agent strategy interface (echo vs mock LLM) `tests/unit/test_agent_strategy.py`

## Phase 3.3: Core Models & Utilities
- [ ] T018 [P] Implement data classes / Pydantic models: Session, Utterance in `server/models/session.py` & `server/models/utterance.py`
- [ ] T019 [P] Implement Agent & AgentStrategy interface `server/models/agent.py`
- [ ] T020 [P] Implement Task & ToolInvocation models (forward-compatible, minimal) `server/models/task.py`
- [ ] T021 Implement context manager (rolling buffer, truncation) `server/services/context_manager.py`
- [ ] T022 Implement redaction utility (>=12 digit regex) `server/services/redaction.py`
- [ ] T023 Implement retry utility with exponential backoff `server/services/retry.py`

## Phase 3.4: Core Service & Transport Implementation
- [ ] T024 Implement health endpoint in existing Quart app `server/server.py`
- [ ] T025 Implement session creation (in-memory store) `server/services/session_store.py` + route
- [ ] T026 Implement WebSocket handler: session_started, partial/final transcript ingestion, agent response dispatch `server/handler/stream_handler.py`
- [ ] T027 Implement transcription adapter (stub returning provided text for now) `server/services/transcription.py`
- [ ] T028 [P] Implement TTS adapter stub (returns silent/placeholder audio bytes) `server/services/tts.py`
- [ ] T029 Implement barge-in handling logic (cancel current playback) integrate in stream handler
- [ ] T030 Implement agent strategy selection + echo strategy `server/services/agent_runtime.py`
- [ ] T031 [P] Implement error event emission & structured error codes `server/services/error_events.py`
- [ ] T032 Implement placeholder tool invocation logging pathway `server/services/tool_invocation.py`

## Phase 3.5: Wire-Up & Make Tests Pass
- [ ] T033 Integrate context manager + redaction + agent runtime into stream handler
- [ ] T034 Integrate retry utility inside transcription + TTS + agent calls
- [ ] T035 Add context truncation enforcement in session flow
- [ ] T036 Connect error event service into global exception handling in WebSocket & REST

## Phase 3.6: Polish & Docs
- [ ] T037 [P] Add unit tests for redaction edge cases (no false positives) `tests/unit/test_redaction.py`
- [ ] T038 [P] Add unit tests for context manager truncation `tests/unit/test_context_manager.py`
- [ ] T039 [P] Update `quickstart.md` removing consent/export steps & add health + test harness instructions
- [ ] T040 Add developer harness static page enhancements (show events list) `server/static/index.html`
- [ ] T041 Add basic README section describing MVP limitations
- [ ] T042 CI lint/format workflow (ruff/black or flake8) `.github/workflows/ci.yml`
- [ ] T043 Final pass ensure no logs leak audio or secrets

## Dependencies & Ordering Notes
- T001-T004 before any tests
- Contract tests (T005-T009) independent → parallel
- Integration tests (T010-T015) mostly independent except T010 precedes others (session id usage)
- Unit tests (T016-T017) parallel to contract tests
- Models (T018-T020) before services using them (T021+)
- Utilities (T021-T023) before service integration (T033+)
- Service endpoints (T024-T032) after failing tests in 3.2
- Wire-up tasks (T033-T036) after core services exist
- Polish (T037-T043) last

## Parallel Execution Examples
Example 1 (after T004):
```
Run in parallel: T005 T006 T007 T008 T009 T011 T012 T013 T015 T016 T017
```
Example 2 (after models ready):
```
Run in parallel: T021 T022 T023 T028 T031
```
Example 3 (polish phase):
```
Run in parallel: T037 T038 T039
```

## Validation Checklist
- [ ] All schema files have a contract test (T005-T009)
- [ ] Each entity (Session, Utterance, Agent, Task, ToolInvocation) has a model task (T018-T020)
- [ ] Tests precede implementation (3.2 before 3.3/3.4)
- [ ] Parallel tasks touch distinct files
- [ ] Redaction & retry utilities tested
- [ ] WebSocket flow & barge-in tested
- [ ] No deferred features accidentally reintroduced

## Post-MVP (Not in this tasks list)
- Structured JSON logging & correlation ids
- Latency measurement harness & metrics
- Role-based access control & consent revocation
- Transcript export & persistence
- Advanced planner / multi-agent orchestration
- Rate limiting, multilingual support

