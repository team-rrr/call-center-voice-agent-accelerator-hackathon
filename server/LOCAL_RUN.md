# Local run instructions

This document explains how to run the server locally for development and testing.

See the main project README for general deployment and architecture notes: ../README.md

## Prerequisites
- Python 3.9+ (3.11 or 3.12 recommended)
- `uv` (Astral UV) recommended for dependency management (https://docs.astral.sh/uv/)
- (Optional) Docker to run the provided image
- (For ACS phone testing) Azure Dev CLI / DevTunnels (`devtunnel`)

## 1. Prepare environment
1. Copy the sample env file and fill in values:

```bash
cp .env.sample .env
# Edit .env and add the keys (API keys, endpoints, ACS connection string, etc.)
open -e .env   # or use your editor
```

Required keys to set (no secrets are included here):
- `AZURE_VOICE_LIVE_API_KEY`
- `AZURE_VOICE_LIVE_ENDPOINT`

Optional keys for ACS features:
- `ACS_CONNECTION_STRING`
- `ACS_DEV_TUNNEL` (set this after creating a DevTunnel)
- `AZURE_USER_ASSIGNED_IDENTITY_CLIENT_ID`

## 2. Install dependencies (recommended: use `uv`)
If you use `uv` the project includes `pyproject.toml` and `uv.lock` to manage a reproducible environment.

1. Install `uv` following its install docs.
2. From the `server/` directory run:

```bash
# create an environment and install dependencies
uv sync --frozen
# or if you have a virtualenv: pip install -r requirements.txt (if you generate one)
```

If you don't use `uv`, install the packages from `pyproject.toml` manually:

```bash
python -m venv .venv
source .venv/bin/activate
pip install quart websockets httpx python-dotenv quart-cors azure-core \
  azure-communication-identity aiohttp azure-eventgrid azure-identity \
  azure-communication-callautomation openai[realtime]
```

## 3. Run the server locally
From the `server/` directory, with `.env` present and dependencies installed:

```bash
py server.py
# or
python server.py
```

The server listens on port `8000` by default. Open http://127.0.0.1:8000 in your browser to view the web client.

## 4. Run with Docker (alternative)
Build the image and run with `.env`:

```bash
docker build -t voiceagent .
docker run --env-file .env -p 8000:8000 -it voiceagent
```

Then open http://127.0.0.1:8000.

## 5. Expose local server for ACS webhooks (DevTunnel)
To receive ACS IncomingCall webhooks locally, expose port 8000 with DevTunnels.

1. Install Azure Dev CLI / DevTunnels and login:

```bash
devtunnel login
devtunnel create --allow-anonymous
devtunnel port create -p 8000
devtunnel host
```

2. Copy the hosted URL output (eg. `https://<your-tunnel>.devtunnels.ms:8000`) into your `.env` as `ACS_DEV_TUNNEL`.
3. In the Azure Portal, configure your Communication Services Event Subscription:
   - Event Type: `IncomingCall`
   - Endpoint Type: `Web Hook`
   - Endpoint: `https://<your-tunnel>.devtunnels.ms:8000/acs/incomingcall`

With the DevTunnel and local server running, incoming calls to your ACS phone number should be forwarded to your local app.

## 6. Smoke tests
- HTTP: `curl -v http://127.0.0.1:8000/` should return the index HTML.
- Browser: Open http://127.0.0.1:8000 and click Start to use the web client.
- WebSockets: the web client uses `/web/ws`; ACS connections use `/acs/ws`.

## 7. Troubleshooting
- Missing env variables: server prints errors if required env vars are missing. Check `.env` and restart.
- Packages: If import errors occur, ensure the virtual environment is activated or Docker image is built correctly.
- DevTunnel: ensure the devtunnel host is reachable and `ACS_DEV_TUNNEL` matches the URL used in the portal.

## 8. Next steps
- To deploy to Azure, see the main README: ../README.md
- If you'd like, generate a `requirements.txt` from the `pyproject.toml` for alternate workflows.
