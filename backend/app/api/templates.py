from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

from app.api.deps import get_db, get_current_user
from app.models.user import User, UserRole
from app.models.template import PromptTemplate

router = APIRouter()

class TemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    niche: Optional[str] = None
    template_text: str

class TemplateResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    niche: Optional[str]
    template_text: str
    is_active: bool

    class Config:
        from_attributes = True

@router.get("", response_model=List[TemplateResponse])
async def list_templates(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    res = await db.execute(select(PromptTemplate).where(PromptTemplate.is_active == True))
    return res.scalars().all()

@router.post("", response_model=TemplateResponse)
async def create_template(
    body: TemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_tpl = PromptTemplate(**body.model_dump())
    db.add(new_tpl)
    await db.commit()
    await db.refresh(new_tpl)
    return new_tpl

@router.delete("/{id}")
async def delete_template(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    res = await db.execute(select(PromptTemplate).where(PromptTemplate.id == id))
    tpl = res.scalars().first()
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")
    
    await db.delete(tpl)
    await db.commit()
    return {"message": "Deleted successfully"}
