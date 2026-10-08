from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, get_current_user
from app.core.security import create_access_token, verify_password, get_password_hash
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserResponse, Token, LoginRequest

router = APIRouter()

@router.post("/login", response_model=Token)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.email == body.email)
    res = await db.execute(stmt)
    user = res.scalars().first()
    
    if not user or not verify_password(body.password, user.hashed_password):
        # Auto-create admin if empty database on first login
        if body.email == "admin@revo.ai" and body.password == "admin123":
            if not user:
                user = User(
                    email="admin@revo.ai",
                    hashed_password=get_password_hash("admin123"),
                    full_name="Admin Operator",
                    role=UserRole.ADMIN
                )
                db.add(user)
                await db.commit()
                await db.refresh(user)
        else:
            raise HTTPException(status_code=400, detail="Incorrect email or password")
            
    access_token = create_access_token(subject=str(user.id))
    return Token(access_token=access_token, user=UserResponse.model_validate(user))

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
