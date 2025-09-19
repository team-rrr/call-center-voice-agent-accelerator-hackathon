# Sample Voice Call Simulation

This document describes the deterministic multi-agent sample flow implemented for demonstration purposes. It replaces dynamic LLM calls with static scripted outputs so you can validate the end-to-end audio + transcription pipeline rapidly.

## Scenario

User (caregiver) asks: "What should I prepare for my mother’s cardiology appointment?"

Goal: Provide a structured, clinically-relevant preparation checklist enriched with patient context and action-oriented guidance, then surface the final checklist to the caller via synthesized speech.

## Agents (Simplified)

Three lightweight agents are defined in `server/app/orchestrator/simple_agents.py`:

1. InfoAgent
   - Purpose: Provide general preparation guidance and helpful resource links.
   - Output: High-level checklist (records, medications, symptom log, questions) + links.
2. PatientContextAgent
   - Purpose: Returns mock patient context (hypertension, atrial fibrillation, last EKG, etc.).
3. ActionAgent
   - Purpose: Combines earlier guidance into a final actionable checklist and offers delivery (SMS/email).

All content is static and deterministic for demonstration. Modify the `response` fields to evolve messaging or localization.

## File Additions & Refactors

- `server/app/orchestrator/simple_agents.py`: Contains data classes and the `simulate_sample_conversation` function returning ordered agent turns.
- `server/app/orchestrator/orchestrator.py`: Rewritten to remove dependency on Semantic Kernel factory for this demo and expose `simulate_voice_call`.
- `server/app/handler/acs_media_handler.py`: On each completed transcription event, runs the simulation and:
  - Logs each agent turn.
  - Sends each agent response downstream as a `Transcription` message.
  - Creates a Voice Live `response.create` request with the final ActionAgent response for TTS.
- `docs/voice_call_simulation.md`: This documentation file.

## Runtime Flow

1. User speaks a question (audio) → ACS → forwarded to Azure Voice Live.
2. Voice Live emits `conversation.item.input_audio_transcription.completed` with transcript.
3. Handler triggers orchestrator simulation:
   - InfoAgent turn
   - PatientContextAgent turn
   - ActionAgent turn (final)
4. Each turn logged and emitted as a textual transcription event to the web client.
5. Final ActionAgent response submitted for speech synthesis.
6. Streaming synthesized audio returned to client.

## Testing Locally

1. Ensure environment variables are set (API key path used if managed identity not available).
2. Run the server (example, adjust as needed):

   ```powershell
   uv run python server/server.py
   ```

3. Open the web client page served (e.g., `http://localhost:8000/` or configured port).
4. Initiate a call / audio stream and speak the sample question.
5. Observe console logs for agent prompts & responses, and UI for streaming transcription.

## Extending the Demo

- Replace static `response` values with function calls to real LLM agents once stable.
- Insert a persistence layer (Cosmos, etc.) to record the conversation turns.
- Add a routing step that chooses which specialized agent participates based on classification.
- Enrich PatientContextAgent with real EHR integration (FHIR API) gated behind appropriate PHI controls.
- Add an optional PlannerAgent stage to select or re-order tasks dynamically.

## Logging

Each agent turn is logged with both prompt and response (INFO level). Adjust verbosity via standard logging configuration in `server/server.py`.

## Disclaimer

All medical content in this demo is illustrative only and not clinical advice. Replace with vetted, compliant content before any real-world use.

---

Revision: v0.1 deterministic demo scaffold
