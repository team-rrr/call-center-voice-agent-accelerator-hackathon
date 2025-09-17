# Implementation Plan: Publish Agents to Azure AI Foundry

Branch: `001-ai-foundry` | Date: 2025-09-16

Input: /Users/graham.schmidt/src/call-center-voice-agent-accelerator-hackathon/.specify/specs/001-ai-foundry/spec.md

## Summary
Enable Foundry integration: register agents, forward transcripts, and allow orchestrator-driven actions.

## Technical Context
- Language/Version: Python 3.11
- Primary Dependencies: quart, websockets, httpx, azure-identity, azure-eventgrid, azure-communication-callautomation, semantic-kernel (to be added), voice-live API
- Storage: N/A (short-lived session data only)
- Testing: pytest (add contract tests)
- Target Platform: Linux/Azure Container Apps or Azure Functions (containerized)
- Project Type: Single web backend (server/ dir)
- Constraints: Use Managed Identity when hosted in Azure; fallback to API keys locally.

## Constitution Check
- No violations detected for this feature; it follows library-first, security, and test-first principles.
