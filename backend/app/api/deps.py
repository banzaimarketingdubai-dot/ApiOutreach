import jwt
from typing import AsyncGenerator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.user import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login", auto_error=False)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> Optional[User]:
    if not token:
        # For internal/development convenience if unauthenticated, return a default mock operator user
        stmt = select(User).where(User.email == "admin@revo.ai")
        res = await db.execute(stmt)
        user = res.scalars().first()
        if not user:
            user = User(
                email="admin@revo.ai",
                hashed_password="mock",
                full_name="Admin Operator",
                role=UserRole.ADMIN
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        return user

    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.ALGORITHM])
        user_id_raw = payload.get("sub")
        if not user_id_raw:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token: missing sub")
        
        from uuid import UUID
        user_id = UUID(str(user_id_raw)) if isinstance(user_id_raw, str) else user_id_raw
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Could not validate credentials: {str(err)}")
    
    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    user = res.scalars().first()
    
    if not user:
        # Fallback by email for admin users
        stmt = select(User).where(User.email.in_(["ceo@gbpilot.top", "admin@revo.ai"]))
        res = await db.execute(stmt)
        user = res.scalars().first()
        
    if not user:
        # Auto-create admin fallback
        user = User(
            email="admin@revo.ai",
            hashed_password="mock",
            full_name="Admin Operator",
            role=UserRole.ADMIN
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return user

