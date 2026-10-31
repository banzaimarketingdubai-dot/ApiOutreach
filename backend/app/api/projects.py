import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.product import Product
from app.models.audience import Audience
from app.models.lead import Lead
from app.models.outreach_campaign import OutreachCampaign
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse

router = APIRouter()

@router.get("", response_model=List[ProjectResponse])
async def list_projects(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all projects with calculated entity counts."""
    stmt = select(Project).order_by(Project.created_at.desc())
    res = await db.execute(stmt)
    projects = res.scalars().all()
    
    result = []
    for proj in projects:
        # Count products
        prod_count_stmt = select(func.count(Product.id)).where(Product.project_id == proj.id)
        prod_count = (await db.execute(prod_count_stmt)).scalar() or 0
        
        # Count audiences
        aud_count_stmt = select(func.count(Audience.id)).where(Audience.project_id == proj.id)
        aud_count = (await db.execute(aud_count_stmt)).scalar() or 0
        
        # Count leads
        leads_count_stmt = select(func.count(Lead.id)).where(Lead.project_id == proj.id)
        leads_count = (await db.execute(leads_count_stmt)).scalar() or 0
        
        # Count outreach campaigns
        camp_count_stmt = select(func.count(OutreachCampaign.id)).where(OutreachCampaign.project_id == proj.id)
        camp_count = (await db.execute(camp_count_stmt)).scalar() or 0
        
        resp = ProjectResponse.model_validate(proj)
        resp.products_count = prod_count
        resp.audiences_count = aud_count
        resp.leads_count = leads_count
        resp.campaigns_count = camp_count
        result.append(resp)
        
    return result

@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new project workspace."""
    # If set as default, reset other defaults
    if data.is_default:
        existing_defaults = (await db.execute(select(Project).where(Project.is_default == True))).scalars().all()
        for p in existing_defaults:
            p.is_default = False

    new_project = Project(
        name=data.name,
        description=data.description,
        sender_name=data.sender_name,
        sender_email=data.sender_email,
        reply_to_email=data.reply_to_email,
        settings=data.settings or {},
        is_default=data.is_default or False
    )
    db.add(new_project)
    await db.commit()
    await db.refresh(new_project)
    
    resp = ProjectResponse.model_validate(new_project)
    resp.products_count = 0
    resp.audiences_count = 0
    resp.leads_count = 0
    resp.campaigns_count = 0
    return resp

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get project details and stats."""
    stmt = select(Project).where(Project.id == project_id)
    proj = (await db.execute(stmt)).scalars().first()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    prod_count = (await db.execute(select(func.count(Product.id)).where(Product.project_id == proj.id))).scalar() or 0
    aud_count = (await db.execute(select(func.count(Audience.id)).where(Audience.project_id == proj.id))).scalar() or 0
    leads_count = (await db.execute(select(func.count(Lead.id)).where(Lead.project_id == proj.id))).scalar() or 0
    camp_count = (await db.execute(select(func.count(OutreachCampaign.id)).where(OutreachCampaign.project_id == proj.id))).scalar() or 0

    resp = ProjectResponse.model_validate(proj)
    resp.products_count = prod_count
    resp.audiences_count = aud_count
    resp.leads_count = leads_count
    resp.campaigns_count = camp_count
    return resp

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: uuid.UUID,
    data: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update project settings."""
    stmt = select(Project).where(Project.id == project_id)
    proj = (await db.execute(stmt)).scalars().first()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    if data.name is not None:
        proj.name = data.name
    if data.description is not None:
        proj.description = data.description
    if data.sender_name is not None:
        proj.sender_name = data.sender_name
    if data.sender_email is not None:
        proj.sender_email = data.sender_email
    if data.reply_to_email is not None:
        proj.reply_to_email = data.reply_to_email
    if data.settings is not None:
        proj.settings = data.settings
    if data.is_default is not None:
        if data.is_default:
            existing_defaults = (await db.execute(select(Project).where(Project.is_default == True))).scalars().all()
            for p in existing_defaults:
                p.is_default = False
        proj.is_default = data.is_default

    await db.commit()
    await db.refresh(proj)

    prod_count = (await db.execute(select(func.count(Product.id)).where(Product.project_id == proj.id))).scalar() or 0
    aud_count = (await db.execute(select(func.count(Audience.id)).where(Audience.project_id == proj.id))).scalar() or 0
    leads_count = (await db.execute(select(func.count(Lead.id)).where(Lead.project_id == proj.id))).scalar() or 0
    camp_count = (await db.execute(select(func.count(OutreachCampaign.id)).where(OutreachCampaign.project_id == proj.id))).scalar() or 0

    resp = ProjectResponse.model_validate(proj)
    resp.products_count = prod_count
    resp.audiences_count = aud_count
    resp.leads_count = leads_count
    resp.campaigns_count = camp_count
    return resp

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete project workspace and associated data."""
    stmt = select(Project).where(Project.id == project_id)
    proj = (await db.execute(stmt)).scalars().first()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    await db.delete(proj)
    await db.commit()
    return None
