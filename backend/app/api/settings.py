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
    """Returns list of configured providers (e.g. Apify, Gemini) without revealing the key."""
    res = await db.execute(select(VaultKey))
    keys = res.scalars().all()
    return [{"provider": k.provider, "status": "configured"} for k in keys]

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
