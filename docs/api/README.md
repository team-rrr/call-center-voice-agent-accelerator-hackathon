# API Documentation

This directory contains comprehensive API documentation for the Call Center Voice Agent Accelerator.

## Available Documentation

- [**WebSocket API**](websocket-api.md) - Real-time voice streaming and event handling
- [**REST API**](rest-api.md) - Session management and status endpoints  
- [**Data Models**](data-models.md) - Core entities and their schemas
- [**Event Types**](event-types.md) - All WebSocket event message formats
- [**Error Handling**](error-handling.md) - Error codes and response patterns

## Quick Start

The primary interface for voice interaction is the WebSocket endpoint:

```
ws://localhost:8000/stream/{session_id}
```

See [WebSocket API](websocket-api.md) for detailed usage patterns and examples.

## Schema Validation

All API endpoints use JSON Schema validation. Contract definitions are available in the `specs/001-what-a-voice/contracts/` directory.

## Authentication

Currently, the API uses environment variable configuration. In production deployments:

- Azure Managed Identity is recommended for service authentication
- API keys are configured via Azure Key Vault
- Connection strings use secure storage patterns

See the main [README.md](../../README.md) for deployment and configuration details.