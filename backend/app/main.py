from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import auth, agents, conversations, chat, api_keys, public
from app.core.config import settings
from app.core.database import SessionLocal
from app.services.prebuilt_agents import seed_prebuilt_agents

app = FastAPI(
    title="Agentic Platform API",
    description="Multi-tenant AI agent platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
app.include_router(conversations.router, prefix="/api/v1/conversations", tags=["conversations"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(api_keys.router, prefix="/api/v1/api-keys", tags=["api-keys"])
app.include_router(public.router, prefix="/api/v1/public", tags=["public"])

# Import and include streaming router
from app.api.v1 import chat_stream
app.include_router(chat_stream.router, prefix="/api/v1/chat", tags=["chat"])

# Import and include TTS router
from app.api.v1 import tts
app.include_router(tts.router, prefix="/api/v1/tts", tags=["tts"])


@app.on_event("startup")
def startup_seed_prebuilt_agents() -> None:
    """Seed prebuilt agents on application startup."""
    db = SessionLocal()
    try:
        seed_prebuilt_agents(db)
    finally:
        db.close()


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

