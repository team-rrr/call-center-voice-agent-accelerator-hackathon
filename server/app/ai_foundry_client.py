"""Lightweight async client for Azure AI Foundry multi-agent orchestrator.

This module follows Azure best-practices: prefer managed identity when available,
fall back to API key if provided, and never hardcode secrets. It implements simple
retry logic with exponential backoff and exposes two primary methods used by the
ACS handlers: notify_call_started and send_user_transcript.

Configuration (env vars / config dict keys):
- AI_FOUNDRY_ENDPOINT: full https endpoint for the Foundry orchestrator (required)
- AI_FOUNDRY_API_KEY: optional api-key fallback
- AZURE_USER_ASSIGNED_IDENTITY_CLIENT_ID: optional managed identity client id

"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, Optional

import httpx
from azure.identity.aio import ManagedIdentityCredential, DefaultAzureCredential

logger = logging.getLogger(__name__)


class AiFoundryClient:
    """Async client to talk to an AI Foundry multi-agent orchestrator.

    Simple contract:
    - inputs: JSON-serializable dicts
    - outputs: parsed JSON responses or raises on non-recoverable errors
    - errors: raises httpx.HTTPError after retries exhausted
    """

    def __init__(self, config: Dict[str, Any]):
        self.endpoint = config.get("AI_FOUNDRY_ENDPOINT") or os.getenv("AI_FOUNDRY_ENDPOINT")
        if not self.endpoint:
            raise ValueError("AI_FOUNDRY_ENDPOINT must be set in config or env")

        self.api_key = config.get("AI_FOUNDRY_API_KEY") or os.getenv("AI_FOUNDRY_API_KEY")
        self.client_id = (
            config.get("AZURE_USER_ASSIGNED_IDENTITY_CLIENT_ID")
            or os.getenv("AZURE_USER_ASSIGNED_IDENTITY_CLIENT_ID")
        )

        # httpx AsyncClient is created lazily
        self._client: Optional[httpx.AsyncClient] = None
        self._credential = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def _get_auth_header(self) -> Dict[str, str]:
        # Prefer managed identity / Azure AD token
        if self.client_id is not None:
            try:
                if self._credential is None:
                    self._credential = ManagedIdentityCredential(
                        managed_identity_client_id=self.client_id
                    )
                token = await self._credential.get_token(
                    "https://cognitiveservices.azure.com/.default"
                )
                return {"Authorization": f"Bearer {token.token}"}
            except Exception:
                logger.exception("ManagedIdentityCredential failed, falling back")

        # Try DefaultAzureCredential (works in many Azure-hosted contexts)
        try:
            if self._credential is None:
                self._credential = DefaultAzureCredential()
            token = await self._credential.get_token(
                "https://cognitiveservices.azure.com/.default"
            )
            return {"Authorization": f"Bearer {token.token}"}
        except Exception:
            logger.debug("DefaultAzureCredential did not yield a token or is unavailable")

        # Final fallback: API key header
        if self.api_key:
            return {"api-key": self.api_key}

        # No auth available
        logger.warning("No authentication available for AiFoundryClient")
        return {}

    async def _request_with_retries(self, method: str, path: str, json_body: Dict[str, Any]):
        url = self.endpoint.rstrip("/") + path
        client = await self._get_client()
        max_retries = 3
        backoff = 0.5

        for attempt in range(1, max_retries + 1):
            try:
                headers = {"Content-Type": "application/json"}
                headers.update(await self._get_auth_header())

                resp = await client.request(method, url, headers=headers, json=json_body)
                resp.raise_for_status()
                if resp.content:
                    return resp.json()
                return {}
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                # For 4xx errors, don't retry except 429
                if 400 <= status < 500 and status != 429:
                    logger.error("Non-retryable HTTP error from Foundry: %s %s", status, exc)
                    raise
                logger.warning(
                    "HTTPStatusError (attempt %s/%s): %s; retrying after backoff",
                    attempt,
                    max_retries,
                    status,
                )
            except Exception as exc:  # includes network errors
                logger.warning(
                    "Request error to Foundry (attempt %s/%s): %s; retrying after backoff",
                    attempt,
                    max_retries,
                    exc,
                )

            # backoff before next try
            await asyncio.sleep(backoff)
            backoff *= 2

        raise httpx.HTTPError("Foundry request failed after retries")

    async def notify_call_started(self, call_id: str, caller_id: str, callback_uri: str) -> Dict[str, Any]:
        """Notify the orchestrator that a new incoming call has been answered.

        The body is intentionally simple; adapt fields to your Foundry contract.
        Returns the parsed JSON response.
        """
        payload = {
            "event": "call.started",
            "call_id": call_id,
            "caller_id": caller_id,
            "callback_uri": callback_uri,
        }
        logger.info("Notifying Foundry of call start: %s", call_id)
        return await self._request_with_retries("POST", "/events/call", payload)

    async def send_user_transcript(self, session_id: str, transcript: str) -> Dict[str, Any]:
        """Send a user transcript to the orchestrator and return any action/response."""
        payload = {"event": "user.transcript", "session_id": session_id, "transcript": transcript}
        logger.info("Sending transcript to Foundry session=%s", session_id)
        return await self._request_with_retries("POST", "/events/transcript", payload)

    async def close(self):
        if self._client is not None:
            await self._client.aclose()
        if self._credential is not None:
            try:
                await self._credential.close()
            except Exception:
                pass
