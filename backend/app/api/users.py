from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, get_current_user
from app.models.user import User, UserRole
from app.schemas.user import UserResponse
from app.core.security import get_password_hash
import uuid

router = APIRouter()

class UserRoleUpdate(BaseModel):
    role: UserRole

class UserInvite(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole = UserRole.OPERATOR

def check_super_admin(current_user: User):
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: SUPER_ADMIN role required."
        )

@router.get("", response_model=List[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_super_admin(current_user)
    stmt = select(User).order_by(User.created_at.desc())
    res = await db.execute(stmt)
    return res.scalars().all()

@router.patch("/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: UUID,
    body: UserRoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_super_admin(current_user)
    
    # Cannot demote yourself
    if current_user.id == user_id and body.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=400, detail="Cannot downgrade your own SUPER_ADMIN role")

    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    user = res.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.role = body.role
    await db.commit()
    await db.refresh(user)
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_super_admin(current_user)
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    user = res.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    await db.delete(user)
    await db.commit()

@router.post("/invite", response_model=UserResponse)
async def invite_user(
    body: UserInvite,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_super_admin(current_user)
    
    email_clean = body.email.strip().lower()
    
    # Check if user already exists
    stmt = select(User).where(User.email == email_clean)
    res = await db.execute(stmt)
    if res.scalars().first():
        raise HTTPException(status_code=400, detail="User with this email already exists")
        
    # Create the user with a dummy password since they will login via Google
    new_user = User(
        email=email_clean,
        full_name=body.full_name or email_clean.split('@')[0],
        hashed_password=get_password_hash(str(uuid.uuid4())), # random unusable password
        role=body.role
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Here we would integrate Resend to send an actual invitation email.
    # For now, since they will just login via Google, adding them to DB allows them in.
    return new_user
