from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # LLM — required
    GROQ_API_KEY: str

    # MongoDB — required
    MONGODB_URI: str
    MONGODB_DB: str = "security_copilot"

    # AWS — optional (graceful degradation if not set)
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"

    # Redis + Celery — optional
    REDIS_URL: str = "redis://localhost:6379/0"

    # Email — optional
    RESEND_API_KEY: Optional[str] = None
    ALERT_EMAIL_FROM: str = "onboarding@resend.dev"
    ALERT_EMAIL_TO: Optional[str] = None

    # Pinecone — optional
    PINECONE_API_KEY: Optional[str] = None
    PINECONE_INDEX: str = "security-copilot"

    # OpenAI — optional
    OPENAI_API_KEY: Optional[str] = None

    # CORS
    FRONTEND_URL: str = "http://localhost:3000"

    class Config:
        env_file = ".env"

settings = Settings()