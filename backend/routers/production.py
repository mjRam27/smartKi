from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.production import ProductionLog, ProductionLogCreate, ProductionLogResponse, ProductionStatus
from dependencies import get_db, get_current_user

router = APIRouter(prefix="/production", tags=["Production"])


@router.post("/", response_model=ProductionLogResponse, status_code=status.HTTP_201_CREATED)
async def create_production_log(
    prod_data: ProductionLogCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new production log"""
    org_id = current_user.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=400, detail="User must belong to an organization")
    
    production = ProductionLog(
        **prod_data.model_dump(),
        organization_id=org_id,
        created_by=current_user["id"]
    )
    
    prod_dict = production.model_dump()
    prod_dict['created_at'] = prod_dict['created_at'].isoformat()
    prod_dict['updated_at'] = prod_dict['updated_at'].isoformat()
    if prod_dict.get('started_at'):
        prod_dict['started_at'] = prod_dict['started_at'].isoformat()
    if prod_dict.get('completed_at'):
        prod_dict['completed_at'] = prod_dict['completed_at'].isoformat()
    
    await db.production_logs.insert_one(prod_dict)
    
    return ProductionLogResponse(**production.model_dump())


@router.get("/", response_model=List[ProductionLogResponse])
async def list_production_logs(
    kitchen_id: Optional[str] = None,
    status: Optional[ProductionStatus] = None,
    scheduled_date: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List production logs"""
    org_id = current_user.get("organization_id")
    
    query = {}
    if current_user["role"] != "admin":
        if org_id:
            query["organization_id"] = org_id
        else:
            return []
    
    if kitchen_id:
        query["kitchen_id"] = kitchen_id
    if status:
        query["status"] = status.value
    if scheduled_date:
        query["scheduled_date"] = scheduled_date
    
    logs = await db.production_logs.find(query, {"_id": 0}).sort("scheduled_date", -1).skip(skip).limit(limit).to_list(limit)
    
    for log in logs:
        if isinstance(log.get('created_at'), str):
            log['created_at'] = datetime.fromisoformat(log['created_at'])
        if isinstance(log.get('updated_at'), str):
            log['updated_at'] = datetime.fromisoformat(log['updated_at'])
        if isinstance(log.get('started_at'), str):
            log['started_at'] = datetime.fromisoformat(log['started_at'])
        if isinstance(log.get('completed_at'), str):
            log['completed_at'] = datetime.fromisoformat(log['completed_at'])
    
    return [ProductionLogResponse(**p) for p in logs]


@router.get("/{prod_id}", response_model=ProductionLogResponse)
async def get_production_log(
    prod_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get production log by ID"""
    log = await db.production_logs.find_one({"id": prod_id}, {"_id": 0})
    if not log:
        raise HTTPException(status_code=404, detail="Production log not found")
    
    org_id = current_user.get("organization_id")
    if current_user["role"] != "admin" and log.get("organization_id") != org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if isinstance(log.get('created_at'), str):
        log['created_at'] = datetime.fromisoformat(log['created_at'])
    if isinstance(log.get('updated_at'), str):
        log['updated_at'] = datetime.fromisoformat(log['updated_at'])
    if isinstance(log.get('started_at'), str):
        log['started_at'] = datetime.fromisoformat(log['started_at'])
    if isinstance(log.get('completed_at'), str):
        log['completed_at'] = datetime.fromisoformat(log['completed_at'])
    
    return ProductionLogResponse(**log)


@router.put("/{prod_id}/start", response_model=ProductionLogResponse)
async def start_production(
    prod_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Start production"""
    log = await db.production_logs.find_one({"id": prod_id}, {"_id": 0})
    if not log:
        raise HTTPException(status_code=404, detail="Production log not found")
    
    if log.get("status") != "planned":
        raise HTTPException(status_code=400, detail="Production must be in planned status to start")
    
    await db.production_logs.update_one(
        {"id": prod_id},
        {"$set": {
            "status": "in_progress",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    updated = await db.production_logs.find_one({"id": prod_id}, {"_id": 0})
    if isinstance(updated.get('created_at'), str):
        updated['created_at'] = datetime.fromisoformat(updated['created_at'])
    if isinstance(updated.get('updated_at'), str):
        updated['updated_at'] = datetime.fromisoformat(updated['updated_at'])
    if isinstance(updated.get('started_at'), str):
        updated['started_at'] = datetime.fromisoformat(updated['started_at'])
    
    return ProductionLogResponse(**updated)


@router.put("/{prod_id}/complete", response_model=ProductionLogResponse)
async def complete_production(
    prod_id: str,
    actual_quantity: int,
    servings_produced: int,
    servings_sold: Optional[int] = 0,
    servings_wasted: Optional[int] = 0,
    production_cost: Optional[float] = None,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Complete production and log results"""
    log = await db.production_logs.find_one({"id": prod_id}, {"_id": 0})
    if not log:
        raise HTTPException(status_code=404, detail="Production log not found")
    
    if log.get("status") != "in_progress":
        raise HTTPException(status_code=400, detail="Production must be in progress to complete")
    
    # Calculate revenue and profit
    unit_price = log.get("unit_price", 0) or 0
    total_revenue = servings_sold * unit_price
    profit = total_revenue - (production_cost or 0) if production_cost else None
    
    await db.production_logs.update_one(
        {"id": prod_id},
        {"$set": {
            "status": "completed",
            "actual_quantity": actual_quantity,
            "servings_produced": servings_produced,
            "servings_sold": servings_sold,
            "servings_wasted": servings_wasted,
            "production_cost": production_cost,
            "total_revenue": total_revenue,
            "profit": profit,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Log waste if any
    if servings_wasted and servings_wasted > 0:
        from models.waste import WasteLog, WasteReason
        waste = WasteLog(
            kitchen_id=log.get("kitchen_id"),
            organization_id=log.get("organization_id"),
            recipe_id=log.get("recipe_id"),
            recipe_name=log.get("recipe_name"),
            ingredient_name=log.get("recipe_name"),
            quantity=servings_wasted,
            unit="servings",
            reason=WasteReason.OVERPRODUCTION,
            estimated_cost=servings_wasted * unit_price if unit_price else None,
            logged_by=current_user["id"]
        )
        waste_dict = waste.model_dump()
        waste_dict['logged_at'] = waste_dict['logged_at'].isoformat()
        waste_dict['created_at'] = waste_dict['created_at'].isoformat()
        await db.waste_logs.insert_one(waste_dict)
    
    updated = await db.production_logs.find_one({"id": prod_id}, {"_id": 0})
    if isinstance(updated.get('created_at'), str):
        updated['created_at'] = datetime.fromisoformat(updated['created_at'])
    if isinstance(updated.get('updated_at'), str):
        updated['updated_at'] = datetime.fromisoformat(updated['updated_at'])
    if isinstance(updated.get('started_at'), str):
        updated['started_at'] = datetime.fromisoformat(updated['started_at'])
    if isinstance(updated.get('completed_at'), str):
        updated['completed_at'] = datetime.fromisoformat(updated['completed_at'])
    
    return ProductionLogResponse(**updated)


@router.delete("/{prod_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_production(
    prod_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Cancel production"""
    log = await db.production_logs.find_one({"id": prod_id}, {"_id": 0})
    if not log:
        raise HTTPException(status_code=404, detail="Production log not found")
    
    if log.get("status") == "completed":
        raise HTTPException(status_code=400, detail="Cannot cancel completed production")
    
    if current_user["role"] not in ["admin", "kitchen_manager", "chef"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    await db.production_logs.update_one(
        {"id": prod_id},
        {"$set": {"status": "cancelled", "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
