from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import auth, agents, conversations, chat, api_keys, public, state
from app.core.config import settings
from app.core.database import SessionLocal
from app.services.prebuilt_agents import seed_prebuilt_agents

app = FastAPI(
    title="Agentic Platform API",
    description="Multi-tenant AI agent platform",
    version="1.0.0"
)

# CORS middleware - allows cross-origin requests for API endpoints
# This enables other platforms to use your APIs from any domain
# For public APIs, we allow all origins (*) which is standard practice
# Security is handled by API key authentication, not CORS
cors_origins = settings.CORS_ORIGINS_API
if cors_origins == ["*"]:
    # Allow all origins for public API access
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow any origin
        allow_credentials=False,  # Must be False when using *
        allow_methods=["*"],  # Allow all HTTP methods
        allow_headers=["*"],  # Allow all headers (including X-API-Key)
        expose_headers=["*"],  # Expose all response headers
    )
else:
    # Restrict to specific origins (for frontend or specific platforms)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
app.include_router(conversations.router, prefix="/api/v1/conversations", tags=["conversations"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(api_keys.router, prefix="/api/v1/api-keys", tags=["api-keys"])
app.include_router(public.router, prefix="/api/v1/public", tags=["public"])
app.include_router(state.router, prefix="/api/v1/state", tags=["state"])

# Import and include streaming router
from app.api.v1 import chat_stream
app.include_router(chat_stream.router, prefix="/api/v1/chat", tags=["chat"])


@app.on_event("startup")
def startup_seed_prebuilt_agents() -> None:
    """Seed prebuilt agents on application startup."""
    if settings.ENV.lower() == "production" and settings.SECRET_KEY.startswith("your-secret-key"):
        raise RuntimeError("SECRET_KEY must be set to a secure value in production.")

    db = SessionLocal()
    try:
        seed_prebuilt_agents(db)
    finally:
        db.close()


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

 
