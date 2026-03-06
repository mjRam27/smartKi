from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.supplier import Supplier, SupplierCreate, SupplierResponse, SupplierStatus
from dependencies import get_db, get_current_user

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])


@router.post("/", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
async def create_supplier(
    supplier_data: SupplierCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new supplier"""
    org_id = current_user.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=400, detail="User must belong to an organization")
    
    if current_user["role"] not in ["admin", "kitchen_manager", "procurement_manager"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    supplier = Supplier(
        **supplier_data.model_dump(),
        organization_id=org_id
    )
    
    supplier_dict = supplier.model_dump()
    supplier_dict['created_at'] = supplier_dict['created_at'].isoformat()
    supplier_dict['updated_at'] = supplier_dict['updated_at'].isoformat()
    
    await db.suppliers.insert_one(supplier_dict)
    
    return SupplierResponse(**supplier.model_dump())


@router.get("/", response_model=List[SupplierResponse])
async def list_suppliers(
    status: Optional[SupplierStatus] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List suppliers with filters"""
    org_id = current_user.get("organization_id")
    
    query = {"is_active": True}
    if current_user["role"] != "admin":
        if org_id:
            query["organization_id"] = org_id
        else:
            return []
    
    if status:
        query["status"] = status.value
    if category:
        query["categories"] = category
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"contact_name": {"$regex": search, "$options": "i"}},
            {"city": {"$regex": search, "$options": "i"}}
        ]
    
    suppliers = await db.suppliers.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    
    for supplier in suppliers:
        if isinstance(supplier.get('created_at'), str):
            supplier['created_at'] = datetime.fromisoformat(supplier['created_at'])
        if isinstance(supplier.get('updated_at'), str):
            supplier['updated_at'] = datetime.fromisoformat(supplier['updated_at'])
    
    return [SupplierResponse(**s) for s in suppliers]


@router.get("/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(
    supplier_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get supplier by ID"""
    supplier = await db.suppliers.find_one({"id": supplier_id}, {"_id": 0})
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    org_id = current_user.get("organization_id")
    if current_user["role"] != "admin" and supplier.get("organization_id") != org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if isinstance(supplier.get('created_at'), str):
        supplier['created_at'] = datetime.fromisoformat(supplier['created_at'])
    if isinstance(supplier.get('updated_at'), str):
        supplier['updated_at'] = datetime.fromisoformat(supplier['updated_at'])
    
    return SupplierResponse(**supplier)


@router.put("/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(
    supplier_id: str,
    supplier_data: SupplierCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update supplier"""
    supplier = await db.suppliers.find_one({"id": supplier_id}, {"_id": 0})
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    if current_user["role"] not in ["admin", "kitchen_manager", "procurement_manager"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    update_data = supplier_data.model_dump()
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.suppliers.update_one({"id": supplier_id}, {"$set": update_data})
    
    updated = await db.suppliers.find_one({"id": supplier_id}, {"_id": 0})
    if isinstance(updated.get('created_at'), str):
        updated['created_at'] = datetime.fromisoformat(updated['created_at'])
    if isinstance(updated.get('updated_at'), str):
        updated['updated_at'] = datetime.fromisoformat(updated['updated_at'])
    
    return SupplierResponse(**updated)


@router.put("/{supplier_id}/rate", response_model=SupplierResponse)
async def rate_supplier(
    supplier_id: str,
    rating: float = Query(ge=1, le=5),
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Rate a supplier (1-5 stars)"""
    supplier = await db.suppliers.find_one({"id": supplier_id}, {"_id": 0})
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    await db.suppliers.update_one(
        {"id": supplier_id},
        {"$set": {"rating": rating, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    updated = await db.suppliers.find_one({"id": supplier_id}, {"_id": 0})
    if isinstance(updated.get('created_at'), str):
        updated['created_at'] = datetime.fromisoformat(updated['created_at'])
    if isinstance(updated.get('updated_at'), str):
        updated['updated_at'] = datetime.fromisoformat(updated['updated_at'])
    
    return SupplierResponse(**updated)


@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_supplier(
    supplier_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete supplier (soft delete)"""
    supplier = await db.suppliers.find_one({"id": supplier_id}, {"_id": 0})
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    if current_user["role"] not in ["admin", "kitchen_manager", "procurement_manager"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    await db.suppliers.update_one(
        {"id": supplier_id}, 
        {"$set": {"is_active": False, "status": "inactive", "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
