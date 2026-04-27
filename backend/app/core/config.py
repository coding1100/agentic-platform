from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Environment
    ENV: str = "development"
    TESTING: bool = False
    # Database
    # For Docker: use postgres:5432 (service name from docker-compose.yml)
    # For local dev: use localhost:5435 (if using docker-compose.yml with port mapping)
    # For production: use postgres:5432 (container-to-container communication)
    DATABASE_URL: str = "postgresql://agentic_user:agentic_password@localhost:5435/agentic_platform"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production-use-env-var"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Gemini API
    GEMINI_API_KEY: str = ""

    # Redis (optional, recommended in production)
    REDIS_URL: str = ""
    
    # CORS
    # For frontend web app - restrict to specific origins
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    # For public API access - allow all origins (set to ["*"] to allow any origin)
    CORS_ORIGINS_API: List[str] = ["*"]  # Allow all origins for API endpoints

    # Observability / request timing logs
    REQUEST_TIMING_LOG_ENABLED: bool = True
    REQUEST_TIMING_LOG_SAMPLE_RATE: float = 0.1
    REQUEST_TIMING_LOG_MIN_MS: int = 300

    # API key auth/rate-limit performance
    API_KEY_AUTH_CACHE_TTL_SECONDS: int = 60
    API_KEY_RATE_LIMIT_WINDOW_SECONDS: int = 60

    # LLM prompt guardrails
    # Set to 0 to disable truncation.
    SYSTEM_PROMPT_MAX_CHARS: int = 0

    # LLM output caps (configurable per deployment/use-case).
    LLM_MAX_OUTPUT_TOKENS: int = 1024
    LLM_MAX_OUTPUT_TOKENS_LONGFORM: int = 2048
    TUTOR_MAX_OUTPUT_TOKENS: int = 2048
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields like GOOGLE_API_KEY if present in .env


settings = Settings()

