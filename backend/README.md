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

