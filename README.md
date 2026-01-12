# Agentic Platform MVP

A multi-tenant AI agent platform where customers can create, configure, and chat with AI agents.

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: Vue 3 + TypeScript
- **Database**: PostgreSQL (Docker)
- **LLM**: Google Gemini

## Project Structure

```
agentic-platform/
├── backend/          # FastAPI backend
├── frontend/         # Vue 3 frontend
├── scripts/         # Deployment scripts
├── nginx/            # Nginx configuration
├── docker-compose.yml        # Development Docker Compose
└── docker-compose.prod.yml  # Production Docker Compose
```

## Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Copy environment file
cp .env.example .env
# Edit .env with your configuration

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

Services will be available at:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8009
- API Docs: http://localhost:8009/docs

### Option 2: Local Development

### Prerequisites

- Python 3.9+
- Node.js 18+
- Docker & Docker Compose (for database only)

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

4. Start PostgreSQL:
```bash
cd ../docker
docker-compose up -d
cd ../backend
```

5. Run migrations:
```bash
alembic upgrade head
```

6. Start the backend server:
```bash
uvicorn app.main:app --reload
```

Backend will be available at http://localhost:8000

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

Frontend will be available at http://localhost:5173

## Features

- ✅ User authentication (signup/login)
- ✅ Agent management (CRUD operations)
- ✅ Conversation management
- ✅ Chat interface with Gemini integration
- ✅ Multi-tenant architecture with proper ownership checks
- ✅ Unit tests for backend and frontend

## Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm run test:unit
```

## API Documentation

Once the backend is running:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Environment Variables

### Backend (.env)
```
DATABASE_URL=postgresql://agentic_user:agentic_password@localhost:5432/agentic_platform
SECRET_KEY=your-secret-key-here
GEMINI_API_KEY=your-gemini-api-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=10080
```

### Frontend (.env)
```
VITE_API_BASE_URL=http://localhost:8000
```

## Deployment

For production deployment to VPS using Docker Compose, see [DEPLOYMENT.md](./DEPLOYMENT.md) for complete setup instructions including CI/CD configuration.

The deployment uses Docker Compose to containerize all services (PostgreSQL, Backend, Frontend) for easy management and consistent environments.

## License

MIT

