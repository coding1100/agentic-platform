from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
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
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields like GOOGLE_API_KEY if present in .env


settings = Settings()

