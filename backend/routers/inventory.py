from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.inventory import InventoryItem, InventoryItemCreate, InventoryItemResponse, InventoryMovement, MovementType
from dependencies import get_db, get_current_user
import uuid

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.post("/", response_model=InventoryItemResponse, status_code=status.HTTP_201_CREATED)
async def create_inventory_item(
    item_data: InventoryItemCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new inventory item"""
    org_id = current_user.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=400, detail="User must belong to an organization")
    
    # Verify kitchen belongs to organization
    kitchen = await db.kitchens.find_one({"id": item_data.kitchen_id, "organization_id": org_id}, {"_id": 0})
    if not kitchen:
        raise HTTPException(status_code=400, detail="Invalid kitchen")
    
    # Get ingredient name
    ingredient = await db.ingredients.find_one({"id": item_data.ingredient_id}, {"_id": 0})
    ingredient_name = ingredient.get("name") if ingredient else None
    
    item = InventoryItem(
        **item_data.model_dump(),
        organization_id=org_id,
        total_value=(item_data.quantity * item_data.cost_per_unit) if item_data.cost_per_unit else None
    )
    
    item_dict = item.model_dump()
    item_dict['created_at'] = item_dict['created_at'].isoformat()
    item_dict['updated_at'] = item_dict['updated_at'].isoformat()
    
    await db.inventory.insert_one(item_dict)
    
    response = item.model_dump()
    response['ingredient_name'] = ingredient_name
    
    return InventoryItemResponse(**response)


@router.get("/", response_model=List[InventoryItemResponse])
async def list_inventory(
    kitchen_id: Optional[str] = None,
    low_stock: Optional[bool] = None,
    expiring_soon: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List inventory items"""
    org_id = current_user.get("organization_id")
    
    query = {"is_active": True}
    if current_user["role"] != "admin":
        if org_id:
            query["organization_id"] = org_id
        else:
            return []
    
    if kitchen_id:
        query["kitchen_id"] = kitchen_id
    
    items = await db.inventory.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    
    # Get ingredient names
    ingredient_ids = list(set(item.get("ingredient_id") for item in items if item.get("ingredient_id")))
    ingredients = await db.ingredients.find({"id": {"$in": ingredient_ids}}, {"_id": 0, "id": 1, "name": 1}).to_list(500)
    ingredient_map = {i["id"]: i["name"] for i in ingredients}
    
    result = []
    for item in items:
        if isinstance(item.get('created_at'), str):
            item['created_at'] = datetime.fromisoformat(item['created_at'])
        if isinstance(item.get('updated_at'), str):
            item['updated_at'] = datetime.fromisoformat(item['updated_at'])
        
        item['ingredient_name'] = ingredient_map.get(item.get('ingredient_id'))
        
        # Filter low stock
        if low_stock:
            if item.get('reorder_point') and item.get('quantity', 0) <= item['reorder_point']:
                result.append(InventoryItemResponse(**item))
        else:
            result.append(InventoryItemResponse(**item))
    
    return result


@router.get("/{item_id}", response_model=InventoryItemResponse)
async def get_inventory_item(
    item_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get inventory item by ID"""
    item = await db.inventory.find_one({"id": item_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    
    org_id = current_user.get("organization_id")
    if current_user["role"] != "admin" and item.get("organization_id") != org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if isinstance(item.get('created_at'), str):
        item['created_at'] = datetime.fromisoformat(item['created_at'])
    if isinstance(item.get('updated_at'), str):
        item['updated_at'] = datetime.fromisoformat(item['updated_at'])
    
    # Get ingredient name
    ingredient = await db.ingredients.find_one({"id": item.get("ingredient_id")}, {"_id": 0})
    item['ingredient_name'] = ingredient.get("name") if ingredient else None
    
    return InventoryItemResponse(**item)


@router.put("/{item_id}/adjust", response_model=InventoryItemResponse)
async def adjust_inventory(
    item_id: str,
    quantity: float,
    movement_type: MovementType,
    notes: Optional[str] = None,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Adjust inventory quantity"""
    item = await db.inventory.find_one({"id": item_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    
    org_id = current_user.get("organization_id")
    if current_user["role"] != "admin" and item.get("organization_id") != org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Calculate new quantity
    current_qty = item.get("quantity", 0)
    if movement_type in [MovementType.RECEIPT, MovementType.RETURN]:
        new_qty = current_qty + quantity
    elif movement_type in [MovementType.ISSUE, MovementType.WASTE]:
        new_qty = current_qty - quantity
    else:
        new_qty = quantity  # ADJUSTMENT sets absolute value
    
    if new_qty < 0:
        raise HTTPException(status_code=400, detail="Insufficient inventory")
    
    # Update inventory
    cost_per_unit = item.get("cost_per_unit", 0) or 0
    await db.inventory.update_one(
        {"id": item_id},
        {"$set": {
            "quantity": new_qty,
            "total_value": new_qty * cost_per_unit,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Log movement
    movement = InventoryMovement(
        inventory_item_id=item_id,
        kitchen_id=item.get("kitchen_id"),
        organization_id=org_id,
        movement_type=movement_type,
        quantity=quantity,
        unit=item.get("unit", "unit"),
        notes=notes,
        performed_by=current_user["id"]
    )
    
    movement_dict = movement.model_dump()
    movement_dict['created_at'] = movement_dict['created_at'].isoformat()
    await db.inventory_movements.insert_one(movement_dict)
    
    updated = await db.inventory.find_one({"id": item_id}, {"_id": 0})
    if isinstance(updated.get('created_at'), str):
        updated['created_at'] = datetime.fromisoformat(updated['created_at'])
    if isinstance(updated.get('updated_at'), str):
        updated['updated_at'] = datetime.fromisoformat(updated['updated_at'])
    
    ingredient = await db.ingredients.find_one({"id": updated.get("ingredient_id")}, {"_id": 0})
    updated['ingredient_name'] = ingredient.get("name") if ingredient else None
    
    return InventoryItemResponse(**updated)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_inventory_item(
    item_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete inventory item (soft delete)"""
    item = await db.inventory.find_one({"id": item_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    
    if current_user["role"] not in ["admin", "kitchen_manager"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    await db.inventory.update_one(
        {"id": item_id}, 
        {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
