from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.waste import WasteLog, WasteLogCreate, WasteLogResponse, WasteReason
from dependencies import get_db, get_current_user

router = APIRouter(prefix="/waste", tags=["Waste Management"])


@router.post("/", response_model=WasteLogResponse, status_code=status.HTTP_201_CREATED)
async def log_waste(
    waste_data: WasteLogCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Log a waste entry"""
    org_id = current_user.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=400, detail="User must belong to an organization")
    
    waste = WasteLog(
        **waste_data.model_dump(),
        organization_id=org_id,
        logged_by=current_user["id"]
    )
    
    waste_dict = waste.model_dump()
    waste_dict['logged_at'] = waste_dict['logged_at'].isoformat()
    waste_dict['created_at'] = waste_dict['created_at'].isoformat()
    
    await db.waste_logs.insert_one(waste_dict)
    
    return WasteLogResponse(**waste.model_dump())


@router.get("/", response_model=List[WasteLogResponse])
async def list_waste_logs(
    kitchen_id: Optional[str] = None,
    reason: Optional[WasteReason] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List waste logs with filters"""
    org_id = current_user.get("organization_id")
    
    query = {}
    if current_user["role"] != "admin":
        if org_id:
            query["organization_id"] = org_id
        else:
            return []
    
    if kitchen_id:
        query["kitchen_id"] = kitchen_id
    if reason:
        query["reason"] = reason.value
    
    if start_date or end_date:
        date_query = {}
        if start_date:
            date_query["$gte"] = start_date
        if end_date:
            date_query["$lte"] = end_date
        if date_query:
            query["logged_at"] = date_query
    
    logs = await db.waste_logs.find(query, {"_id": 0}).sort("logged_at", -1).skip(skip).limit(limit).to_list(limit)
    
    for log in logs:
        if isinstance(log.get('logged_at'), str):
            log['logged_at'] = datetime.fromisoformat(log['logged_at'])
        if isinstance(log.get('created_at'), str):
            log['created_at'] = datetime.fromisoformat(log['created_at'])
    
    return [WasteLogResponse(**w) for w in logs]


@router.get("/summary")
async def get_waste_summary(
    kitchen_id: Optional[str] = None,
    period: str = Query("week", regex="^(day|week|month|year)$"),
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get waste summary statistics"""
    org_id = current_user.get("organization_id")
    
    query = {}
    if current_user["role"] != "admin":
        if org_id:
            query["organization_id"] = org_id
        else:
            return {"total_entries": 0, "total_cost": 0, "by_reason": {}}
    
    if kitchen_id:
        query["kitchen_id"] = kitchen_id
    
    logs = await db.waste_logs.find(query, {"_id": 0}).to_list(1000)
    
    total_cost = sum(log.get("estimated_cost", 0) or 0 for log in logs)
    
    by_reason = {}
    for log in logs:
        reason = log.get("reason", "other")
        if reason not in by_reason:
            by_reason[reason] = {"count": 0, "cost": 0}
        by_reason[reason]["count"] += 1
        by_reason[reason]["cost"] += log.get("estimated_cost", 0) or 0
    
    return {
        "total_entries": len(logs),
        "total_cost": round(total_cost, 2),
        "by_reason": by_reason
    }


@router.get("/{waste_id}", response_model=WasteLogResponse)
async def get_waste_log(
    waste_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get waste log by ID"""
    log = await db.waste_logs.find_one({"id": waste_id}, {"_id": 0})
    if not log:
        raise HTTPException(status_code=404, detail="Waste log not found")
    
    org_id = current_user.get("organization_id")
    if current_user["role"] != "admin" and log.get("organization_id") != org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if isinstance(log.get('logged_at'), str):
        log['logged_at'] = datetime.fromisoformat(log['logged_at'])
    if isinstance(log.get('created_at'), str):
        log['created_at'] = datetime.fromisoformat(log['created_at'])
    
    return WasteLogResponse(**log)


@router.delete("/{waste_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_waste_log(
    waste_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete waste log"""
    log = await db.waste_logs.find_one({"id": waste_id}, {"_id": 0})
    if not log:
        raise HTTPException(status_code=404, detail="Waste log not found")
    
    if current_user["role"] not in ["admin", "kitchen_manager"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    await db.waste_logs.delete_one({"id": waste_id})
