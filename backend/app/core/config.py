from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Groq
    GROQ_API_KEY: str

    # MongoDB
    MONGODB_URI: str
    MONGODB_DB: str = "security_copilot"

    # AWS
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str = "ap-southeast-1"

    # Celery + Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Email (Resend)
    RESEND_API_KEY: str
    ALERT_EMAIL_FROM: str = "alerts@yourdomain.com"
    ALERT_EMAIL_TO: str

    # Pinecone
    PINECONE_API_KEY: str
    PINECONE_INDEX: str = "security-copilot"

    # OpenAI (embeddings only)
    OPENAI_API_KEY: str

    class Config:
        env_file = ".env"

settings = Settings()