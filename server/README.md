# Overview
This project is managed using `pyproject.toml` and the [`uv`](https://github.com/astral-sh/uv) package manager for fast Python dependency management.

## 1. Test with Web Client

### Local quickstart

1. From the project `server/` directory copy the sample env and fill in values:

```bash
cp .env.sample .env
# edit .env and set AZURE_VOICE_LIVE_API_KEY, AZURE_VOICE_LIVE_ENDPOINT
# set ACS_CONNECTION_STRING if you will use ACS features
```

2. Start the server (development workflow used during testing):

```bash
uv run server.py
```

3. Open http://127.0.0.1:8000 in your browser and click **Start** to use the web client.

Notes
- You must have appropriate RBAC permissions to obtain the Voice Live API key and the ACS connection string. This typically requires permissions to read or create secrets (Key Vault roles or equivalent) and permissions to manage Communication Services resources.
- See the main README for full deployment details: ../README.md

### Run with Docker (Alternative)

If you prefer Docker or are running in GitHub Codespaces:

1. Build the image:

    ```
    docker build -t voiceagent .
    ```

2. Run the image with local environment variables:

    ```
    docker run --env-file .env -p 8000:8000 -it voiceagent
    ```
3. Open [http://127.0.0.1:8000](http://127.0.0.1:8000) and click **Start** to interact with the agent.

## 2. Test with ACS Client (Phone Call)

To test Azure Communication Services (ACS) locally, we’ll expose the local server using **Azure DevTunnels**.

> DevTunnels allow public HTTP/S access to your local environment — ideal for webhook testing.

1. [Install Azure Dev CLI](https://learn.microsoft.com/azure/developer/dev-tunnels/overview) if not already installed.

2. Log in and create a tunnel:

    ```bash
    devtunnel login
    devtunnel create --allow-anonymous
    devtunnel port create -p 8000
    devtunnel host
    ```

3. The final command will output a URL like:

    ```
    https://<your-tunnel>.devtunnels.ms:8000
    ```

4. Add this URL to your `.env` file under:

    ```
    ACS_DEV_TUNNEL=https://<your-tunnel>.devtunnels.ms:8000
    ```

### Set Up Incoming Call Event

1. Go to your **Communication Services** resource in the Azure Portal.
2. In the left menu, click **Events** → **+ Event Subscription**.
3. Use the following settings:
   - **Event type**: `IncomingCall`
   - **Endpoint type**: `Web Hook`
   - **Endpoint URL**:
     ```
     https://<your-tunnel>.devtunnels.ms:8000/acs/incomingcall
     ```

> Ensure both your local Python server and DevTunnel are running before creating the subscription.

### Call the Agent

1. [Get a phone number](https://learn.microsoft.com/azure/communication-services/quickstarts/telephony/get-phone-number?tabs=windows&pivots=platform-azp-new) for your ACS resource if not already provisioned.
2. Call the number. Your call will route to your local agent.

## Recap

- Use the **web client** for fast local testing.
- Use **DevTunnel + ACS** to simulate phone calls and test telephony integration.
- Customize the `.env` file, system prompts, and runtime behavior to fit your use case.

## AI Foundry multi-agent orchestrator integration

This project can optionally notify a multi-agent orchestrator (Azure AI Foundry) when calls start
and forward user transcripts. The integration is optional and enabled by setting the following
environment variables (in addition to the existing Voice Live / ACS vars):

- `AI_FOUNDRY_ENDPOINT` (required to enable integration) - full https URL to the foundry HTTP API
- `AI_FOUNDRY_API_KEY` (optional) - API key fallback if Managed Identity / AAD tokens are unavailable
- `AZURE_USER_ASSIGNED_IDENTITY_CLIENT_ID` (optional) - use a user-assigned managed identity to request AAD tokens

The code will prefer Managed Identity / DefaultAzureCredential for auth. No secrets are hardcoded.

Behavior:
- `acs_event_handler` will call `notify_call_started` when a call is answered.
- `acs_media_handler` will call `send_user_transcript` when a transcription completes.

These calls are best-effort: failures will be logged but won't block call handling.

