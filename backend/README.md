# Agentic Platform Backend

FastAPI backend for the Agentic Platform MVP.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Start PostgreSQL (using Docker):
```bash
cd ../docker
docker-compose up -d
```

5. Run migrations:
```bash
alembic upgrade head
```

## Development

```bash
uvicorn app.main:app --reload
```

## Testing

```bash
pytest
```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Tutor Tool API

The Tutor Tool is an AI-based learning workflow, not a human tutoring service.

Authenticated endpoints:

- `GET /api/v1/tutor/{agent_id}/workspace`
- `PUT /api/v1/tutor/{agent_id}/workspace`
- `POST /api/v1/tutor/{agent_id}/execute`

The structured Tutor flow stores workspace state in `user_states` and supports:

- Subject + academic level setup
- Hidden optional `learner_name` from the frontend
- `ask_question`, `upload_notes`, and `practice`
- Progress tracking, recent sources, and recent results

Optional follow-up chat can continue over:

- `POST /api/v1/chat/{agent_id}/stream`

## Realtime Avatar Setup (LiveKit)

Add these environment variables to `.env`:

```bash
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret
OPENAI_API_KEY=your_openai_api_key
```

For the avatar worker:

```bash
cd backend
pip install -r requirements.txt
python -m app.services.avatar_interview_worker dev
```

Useful worker env vars:

```bash
LIVEKIT_AVATAR_AGENT_NAME=avatar-interview-agent
LIVEKIT_AVATAR_INTERVIEW_INSTRUCTIONS=optional_custom_prompt
LIVEKIT_AVATAR_STT=deepgram/nova-3-general:en
LIVEKIT_AVATAR_TTS=cartesia/sonic-2:9626c31c-bec5-4cca-baa8-f8ba9e84c8bc
# Optional override:
LIVEKIT_AVATAR_LLM=openai/gpt-4.1-mini
```

Notes on model providers:
- STT/TTS in this worker use LiveKit Inference provider strings.
- If an unsupported STT/TTS provider is configured (for example old `openai/...` values), the worker now falls back to safe defaults.

### Realtime API Endpoints

Authenticated:

- `PUT /api/v1/realtime/agents/{agent_id}/embed`
- `GET /api/v1/realtime/agents/{agent_id}/embed`
- `GET /api/v1/realtime/agents/{agent_id}/sessions`
- `POST /api/v1/realtime/agents/{agent_id}/token`
- `POST /api/v1/realtime/sessions/{session_id}/end`

Public (for iframe/custom frontend embeds):

- `POST /api/v1/public/realtime/embed/{embed_id}/token`
- `POST /api/v1/public/realtime/embed/{embed_id}/sessions/{session_id}/end`

LiveKit webhook (session lifecycle sync):

- `POST /api/v1/realtime/webhooks/livekit`

Notes:

- For production embeds, configure `allowed_origins` per deployment (origins can include ports, e.g. `http://localhost:5173` for local testing).
- Keep the LiveKit webhook enabled so sessions are closed even when browsers disconnect unexpectedly.
- The worker reads agent dispatch metadata (`instructions` and optional `realtime_config` model overrides) so each avatar agent can behave differently without a separate service.
- Avatar rendering is done in the frontend (browser-based), so no paid avatar provider credentials are required.

