# Quickstart (Phase 1 Draft)

This quickstart demonstrates initiating a session, sending an utterance (text fallback), and receiving agent response & task progress events.

## Prerequisites
- Python 3.11+
- Container runtime (Docker)
- Environment variables: AI_FOUNDRY_ENDPOINT, DEFAULT_MODEL, LOG_LEVEL, (optional) ACS_RESOURCE

## Steps
1. Create a session (POST /sessions).
2. Open WebSocket: /sessions/{id}/stream.
3. Send audio frames (client) or text fallback (POST /sessions/{id}/utterances).
4. Receive events: transcript_partial -> transcript_final -> agent_plan -> task_started -> response.
5. Interrupt playback by new audio → observe barge_in event.
6. Revoke consent (POST /sessions/{id}/consent/revoke) to switch to ephemeral mode.
7. Export transcript (GET /sessions/{id}/export) prior to consent revocation or after session end.

## Expected Event Ordering (Happy Path)
user_utterance → transcript_partial* → transcript_final → agent_plan → task_started → response → task_completed → session_summary

( *Multiple partial events possible )

## Validation Goals
- Initial response latency P95 <= 1500ms (instrument timestamps)
- All events include correlation_id & event_id
- Clarification triggered when confidence < 0.75

## Next
Implement contract tests to enforce schemas before service logic.
