import os
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.vault import VaultKey
from app.core.config import settings

async def get_api_key(provider: str) -> str:
    """
    Fetches the API key for a given provider.
    Checks the database Vault first, then falls back to environment variables.
    """
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(VaultKey).where(VaultKey.provider == provider.lower()))
        key_record = res.scalars().first()
        
    if key_record and key_record.api_key_encrypted:
        return key_record.api_key_encrypted
        
    # Fallback to .env
    if provider.lower() == "apify":
        return settings.APIFY_API_TOKEN or os.getenv("APIFY_API_TOKEN")
    elif provider.lower() == "gemini":
        return settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
    elif provider.lower() == "hubspot":
        return os.getenv("HUBSPOT_API_KEY")
    elif provider.lower() == "groq":
        return os.getenv("GROQ_API_KEY")
        
    return None
