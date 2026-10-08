from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Dict

from app.api.deps import get_db, get_current_user
from app.models.user import User, UserRole
from app.models.vault import VaultKey

router = APIRouter()

class VaultSetRequest(BaseModel):
    provider: str
    api_key: str

@router.get("/vault", response_model=List[Dict[str, str]])
async def get_vault_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Returns list of configured providers and their masked keys, including .env fallbacks."""
    res = await db.execute(select(VaultKey))
    db_keys = {k.provider: k.api_key_encrypted for k in res.scalars().all()}
    
    import os
    from app.core.config import settings
    
    def mask_key(k: str) -> str:
        if not k or len(k) < 6: return None
        return k[:4] + "*" * (len(k) - 8) + k[-4:]

    apify_key = db_keys.get("apify") or settings.APIFY_API_TOKEN or os.getenv("APIFY_API_TOKEN")
    gemini_key = db_keys.get("gemini") or settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
    hubspot_key = db_keys.get("hubspot") or os.getenv("HUBSPOT_API_KEY")
    
    providers = []
    if apify_key:
        providers.append({"provider": "apify", "status": "configured", "source": "Vault" if "apify" in db_keys else ".env", "masked": mask_key(apify_key)})
    if gemini_key:
        providers.append({"provider": "gemini", "status": "configured", "source": "Vault" if "gemini" in db_keys else ".env", "masked": mask_key(gemini_key)})
    if hubspot_key:
        providers.append({"provider": "hubspot", "status": "configured", "source": "Vault" if "hubspot" in db_keys else ".env", "masked": mask_key(hubspot_key)})
        
    return providers

@router.post("/vault")
async def set_vault_key(
    body: VaultSetRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Sets an API key for a provider. Admin only."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can manage vault keys.")
        
    res = await db.execute(select(VaultKey).where(VaultKey.provider == body.provider))
    existing = res.scalars().first()
    
    if existing:
        existing.api_key_encrypted = body.api_key # Storing plain for MVP
    else:
        new_key = VaultKey(provider=body.provider, api_key_encrypted=body.api_key)
        db.add(new_key)
        
    await db.commit()
    return {"message": f"{body.provider} API key configured successfully"}
