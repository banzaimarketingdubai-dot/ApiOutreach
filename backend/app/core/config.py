from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Revo Master Data Platform"
    API_V1_STR: str = "/api/v1"
    
    # Security
    JWT_SECRET: str = "revo_super_secret_key_change_me_in_prod"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Database & Cache
    DATABASE_URL: str = "postgresql+asyncpg://revo_user:revo_secret@localhost:5432/revo_masterdata"
    SYNC_DATABASE_URL: str = "postgresql://revo_user:revo_secret@localhost:5432/revo_masterdata"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # External APIs
    APIFY_API_TOKEN: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_API_KEYS: List[str] = []
    GROK_API_KEY: Optional[str] = None
    GROK_API_KEYS: List[str] = []
    
    # LLM Settings
    PRIMARY_GEMINI_MODEL: str = "gemini-1.5-pro"  # Fallback chain: gemini-1.5-pro, gemini-1.5-flash, gemini-1.0-pro
    FALLBACK_GEMINI_MODELS: List[str] = ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-2.0-flash-exp"]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
