from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.organization import Organization, OrganizationCreate, OrganizationResponse
from dependencies import get_db, get_current_user

router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.post("/", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    org_data: OrganizationCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new organization"""
    org = Organization(
        **org_data.model_dump(),
        owner_id=current_user["id"]
    )
    
    org_dict = org.model_dump()
    org_dict['created_at'] = org_dict['created_at'].isoformat()
    org_dict['updated_at'] = org_dict['updated_at'].isoformat()
    
    await db.organizations.insert_one(org_dict)
    
    # Update user's organization_id
    await db.users.update_one(
        {"id": current_user["id"]},
        {"$set": {"organization_id": org.id, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return OrganizationResponse(**org.model_dump())


@router.get("/", response_model=List[OrganizationResponse])
async def list_organizations(
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List organizations (admin sees all, others see their own)"""
    if current_user["role"] == "admin":
        orgs = await db.organizations.find({}, {"_id": 0}).to_list(100)
    else:
        org_id = current_user.get("organization_id")
        if not org_id:
            return []
        orgs = await db.organizations.find({"id": org_id}, {"_id": 0}).to_list(1)
    
    for org in orgs:
        if isinstance(org.get('created_at'), str):
            org['created_at'] = datetime.fromisoformat(org['created_at'])
        if isinstance(org.get('updated_at'), str):
            org['updated_at'] = datetime.fromisoformat(org['updated_at'])
    
    return [OrganizationResponse(**org) for org in orgs]


@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get organization by ID"""
    org = await db.organizations.find_one({"id": org_id}, {"_id": 0})
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Check access
    if current_user["role"] != "admin" and current_user.get("organization_id") != org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if isinstance(org.get('created_at'), str):
        org['created_at'] = datetime.fromisoformat(org['created_at'])
    if isinstance(org.get('updated_at'), str):
        org['updated_at'] = datetime.fromisoformat(org['updated_at'])
    
    return OrganizationResponse(**org)


@router.put("/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: str,
    org_data: OrganizationCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update organization"""
    org = await db.organizations.find_one({"id": org_id}, {"_id": 0})
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Check access
    if current_user["role"] not in ["admin", "kitchen_manager"] and org.get("owner_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    update_data = org_data.model_dump()
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.organizations.update_one({"id": org_id}, {"$set": update_data})
    
    updated_org = await db.organizations.find_one({"id": org_id}, {"_id": 0})
    if isinstance(updated_org.get('created_at'), str):
        updated_org['created_at'] = datetime.fromisoformat(updated_org['created_at'])
    if isinstance(updated_org.get('updated_at'), str):
        updated_org['updated_at'] = datetime.fromisoformat(updated_org['updated_at'])
    
    return OrganizationResponse(**updated_org)
