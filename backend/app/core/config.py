from pydantic_settings import BaseSettings
 
class Settings(BaseSettings):
    GROQ_API_KEY: str
    MONGODB_URI: str
    MONGODB_DB: str = "security_copilot"
 
    class Config:
        env_file = ".env"
 
settings = Settings()