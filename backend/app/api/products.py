import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.product import Product
from app.models.project import Project
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse

router = APIRouter()

@router.get("", response_model=List[ProductResponse])
async def list_products(
    project_id: Optional[uuid.UUID] = Query(None, description="Filter products by project ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List products, optionally filtered by project_id."""
    stmt = select(Product)
    if project_id:
        stmt = stmt.where(Product.project_id == project_id)
    stmt = stmt.order_by(Product.created_at.desc())
    
    res = await db.execute(stmt)
    products = res.scalars().all()
    return products

@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    data: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new product/offer."""
    proj = (await db.execute(select(Project).where(Project.id == data.project_id))).scalars().first()
    if not proj:
        raise HTTPException(status_code=400, detail="Target project not found")

    new_prod = Product(
        project_id=data.project_id,
        name=data.name,
        description=data.description,
        target_audience_icp=data.target_audience_icp,
        pain_points=data.pain_points or [],
        value_props=data.value_props or [],
        target_action_cta=data.target_action_cta,
        pricing_details=data.pricing_details,
        settings=data.settings or {}
    )
    db.add(new_prod)
    await db.commit()
    await db.refresh(new_prod)
    return new_prod

@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get product details."""
    stmt = select(Product).where(Product.id == product_id)
    prod = (await db.execute(stmt)).scalars().first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    return prod

@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: uuid.UUID,
    data: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update product details."""
    stmt = select(Product).where(Product.id == product_id)
    prod = (await db.execute(stmt)).scalars().first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")

    if data.name is not None:
        prod.name = data.name
    if data.description is not None:
        prod.description = data.description
    if data.target_audience_icp is not None:
        prod.target_audience_icp = data.target_audience_icp
    if data.pain_points is not None:
        prod.pain_points = data.pain_points
    if data.value_props is not None:
        prod.value_props = data.value_props
    if data.target_action_cta is not None:
        prod.target_action_cta = data.target_action_cta
    if data.pricing_details is not None:
        prod.pricing_details = data.pricing_details
    if data.settings is not None:
        prod.settings = data.settings

    await db.commit()
    await db.refresh(prod)
    return prod

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a product."""
    stmt = select(Product).where(Product.id == product_id)
    prod = (await db.execute(stmt)).scalars().first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")

    await db.delete(prod)
    await db.commit()
    return None
