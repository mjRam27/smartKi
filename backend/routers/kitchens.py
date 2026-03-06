from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.kitchen import Kitchen, KitchenCreate, KitchenResponse
from dependencies import get_db, get_current_user

router = APIRouter(prefix="/kitchens", tags=["Kitchens"])


@router.post("/", response_model=KitchenResponse, status_code=status.HTTP_201_CREATED)
async def create_kitchen(
    kitchen_data: KitchenCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new kitchen"""
    org_id = current_user.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=400, detail="User must belong to an organization")
    
    kitchen = Kitchen(
        **kitchen_data.model_dump(),
        organization_id=org_id
    )
    
    kitchen_dict = kitchen.model_dump()
    kitchen_dict['created_at'] = kitchen_dict['created_at'].isoformat()
    kitchen_dict['updated_at'] = kitchen_dict['updated_at'].isoformat()
    
    await db.kitchens.insert_one(kitchen_dict)
    
    return KitchenResponse(**kitchen.model_dump())


@router.get("/", response_model=List[KitchenResponse])
async def list_kitchens(
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List kitchens for current organization"""
    org_id = current_user.get("organization_id")
    if not org_id and current_user["role"] != "admin":
        return []
    
    query = {} if current_user["role"] == "admin" else {"organization_id": org_id}
    kitchens = await db.kitchens.find(query, {"_id": 0}).to_list(100)
    
    for kitchen in kitchens:
        if isinstance(kitchen.get('created_at'), str):
            kitchen['created_at'] = datetime.fromisoformat(kitchen['created_at'])
        if isinstance(kitchen.get('updated_at'), str):
            kitchen['updated_at'] = datetime.fromisoformat(kitchen['updated_at'])
    
    return [KitchenResponse(**k) for k in kitchens]


@router.get("/{kitchen_id}", response_model=KitchenResponse)
async def get_kitchen(
    kitchen_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get kitchen by ID"""
    kitchen = await db.kitchens.find_one({"id": kitchen_id}, {"_id": 0})
    if not kitchen:
        raise HTTPException(status_code=404, detail="Kitchen not found")
    
    # Check access
    org_id = current_user.get("organization_id")
    if current_user["role"] != "admin" and kitchen.get("organization_id") != org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if isinstance(kitchen.get('created_at'), str):
        kitchen['created_at'] = datetime.fromisoformat(kitchen['created_at'])
    if isinstance(kitchen.get('updated_at'), str):
        kitchen['updated_at'] = datetime.fromisoformat(kitchen['updated_at'])
    
    return KitchenResponse(**kitchen)


@router.put("/{kitchen_id}", response_model=KitchenResponse)
async def update_kitchen(
    kitchen_id: str,
    kitchen_data: KitchenCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update kitchen"""
    kitchen = await db.kitchens.find_one({"id": kitchen_id}, {"_id": 0})
    if not kitchen:
        raise HTTPException(status_code=404, detail="Kitchen not found")
    
    org_id = current_user.get("organization_id")
    if current_user["role"] not in ["admin", "kitchen_manager"] and kitchen.get("organization_id") != org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    update_data = kitchen_data.model_dump()
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.kitchens.update_one({"id": kitchen_id}, {"$set": update_data})
    
    updated = await db.kitchens.find_one({"id": kitchen_id}, {"_id": 0})
    if isinstance(updated.get('created_at'), str):
        updated['created_at'] = datetime.fromisoformat(updated['created_at'])
    if isinstance(updated.get('updated_at'), str):
        updated['updated_at'] = datetime.fromisoformat(updated['updated_at'])
    
    return KitchenResponse(**updated)


@router.delete("/{kitchen_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_kitchen(
    kitchen_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete kitchen (soft delete)"""
    kitchen = await db.kitchens.find_one({"id": kitchen_id}, {"_id": 0})
    if not kitchen:
        raise HTTPException(status_code=404, detail="Kitchen not found")
    
    if current_user["role"] not in ["admin", "kitchen_manager"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    await db.kitchens.update_one(
        {"id": kitchen_id}, 
        {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
