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

## Realtime Note

LiveKit/avatar realtime functionality has been removed. The backend now supports chat-first workflows only.

