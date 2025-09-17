# Feature: Publish Agents to Azure AI Foundry

Summary
-------
Enable the application to publish and integrate multi-agent orchestrators hosted in Azure AI Foundry. Agents will leverage Semantic Kernel for reasoning and planning, run on Python (uv-managed), and use Azure Voice Live for real-time voice interactions.

User stories
------------
- As a developer, I want the app to register and publish an AI agent to Azure AI Foundry so the orchestrator can route conversations to it.
- As a call handler, when a call is answered, the system should notify Foundry of the new call and provide callbacks for agent actions.
- As a conversational agent, I want Semantic Kernel to run agent plans and produce actions that may include voice responses via Voice Live.

Functional requirements
-----------------------
- Provide a lightweight Foundry client to POST events to the orchestrator (call.start, user.transcript).
- Authenticate to Foundry using Managed Identity (preferred) or API key fallback.
- Forward user transcripts to Foundry and accept agent commands/responses.
- Keep integration optional and non-blocking: failures should be logged, not fatal.

Non-functional requirements
---------------------------
- Use secure auth patterns: Managed Identity / DefaultAzureCredential when running in Azure, Service Principal for CI.
- Implement retry logic with exponential backoff for transient failures.
- Minimal latency for transcript forwarding (<200ms added ideally). Accept eventual consistency for non-critical operations.

Acceptance criteria
-------------------
- The app can POST a call.started event to Foundry and receive a 2xx response.
- The app forwards transcripts and receives actionable responses or acknowledgements.
- The integration is configurable with `AI_FOUNDRY_ENDPOINT` and optional `AI_FOUNDRY_API_KEY` and `AZURE_USER_ASSIGNED_IDENTITY_CLIENT_ID`.

Constraints and assumptions
---------------------------
- Foundry exposes simple HTTP endpoints for events; exact contract will be refined.
- Semantic Kernel integration will run locally within the Python runtime or within orchestrator-managed agents depending on deployment.
- The repo uses `uv` / pyproject-managed workflow.
