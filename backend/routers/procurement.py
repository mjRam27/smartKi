from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.procurement import PurchaseOrder, PurchaseOrderCreate, PurchaseOrderResponse, OrderStatus
from dependencies import get_db, get_current_user
import uuid

router = APIRouter(prefix="/procurement", tags=["Procurement"])


def generate_order_number() -> str:
    """Generate a unique order number"""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    unique = str(uuid.uuid4())[:6].upper()
    return f"PO-{timestamp}-{unique}"


@router.post("/orders", response_model=PurchaseOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_purchase_order(
    order_data: PurchaseOrderCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new purchase order"""
    org_id = current_user.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=400, detail="User must belong to an organization")
    
    if current_user["role"] not in ["admin", "kitchen_manager", "procurement_manager", "chef"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get supplier name
    supplier = await db.suppliers.find_one({"id": order_data.supplier_id}, {"_id": 0})
    supplier_name = supplier.get("name") if supplier else None
    
    # Calculate totals
    subtotal = sum(item.total_price for item in order_data.items)
    total = subtotal + order_data.tax + order_data.shipping
    
    order = PurchaseOrder(
        order_number=generate_order_number(),
        supplier_name=supplier_name,
        organization_id=org_id,
        created_by=current_user["id"],
        subtotal=subtotal,
        total=total,
        **order_data.model_dump()
    )
    
    order_dict = order.model_dump()
    order_dict['created_at'] = order_dict['created_at'].isoformat()
    order_dict['updated_at'] = order_dict['updated_at'].isoformat()
    if order_dict.get('approved_at'):
        order_dict['approved_at'] = order_dict['approved_at'].isoformat()
    if order_dict.get('received_at'):
        order_dict['received_at'] = order_dict['received_at'].isoformat()
    
    await db.purchase_orders.insert_one(order_dict)
    
    return PurchaseOrderResponse(**order.model_dump())


@router.get("/orders", response_model=List[PurchaseOrderResponse])
async def list_purchase_orders(
    status: Optional[OrderStatus] = None,
    supplier_id: Optional[str] = None,
    kitchen_id: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List purchase orders"""
    org_id = current_user.get("organization_id")
    
    query = {}
    if current_user["role"] != "admin":
        if org_id:
            query["organization_id"] = org_id
        else:
            return []
    
    if status:
        query["status"] = status.value
    if supplier_id:
        query["supplier_id"] = supplier_id
    if kitchen_id:
        query["kitchen_id"] = kitchen_id
    
    orders = await db.purchase_orders.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    for order in orders:
        if isinstance(order.get('created_at'), str):
            order['created_at'] = datetime.fromisoformat(order['created_at'])
        if isinstance(order.get('updated_at'), str):
            order['updated_at'] = datetime.fromisoformat(order['updated_at'])
        if isinstance(order.get('approved_at'), str):
            order['approved_at'] = datetime.fromisoformat(order['approved_at'])
        if isinstance(order.get('received_at'), str):
            order['received_at'] = datetime.fromisoformat(order['received_at'])
    
    return [PurchaseOrderResponse(**o) for o in orders]


@router.get("/orders/{order_id}", response_model=PurchaseOrderResponse)
async def get_purchase_order(
    order_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get purchase order by ID"""
    order = await db.purchase_orders.find_one({"id": order_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    
    org_id = current_user.get("organization_id")
    if current_user["role"] != "admin" and order.get("organization_id") != org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if isinstance(order.get('created_at'), str):
        order['created_at'] = datetime.fromisoformat(order['created_at'])
    if isinstance(order.get('updated_at'), str):
        order['updated_at'] = datetime.fromisoformat(order['updated_at'])
    if isinstance(order.get('approved_at'), str):
        order['approved_at'] = datetime.fromisoformat(order['approved_at'])
    if isinstance(order.get('received_at'), str):
        order['received_at'] = datetime.fromisoformat(order['received_at'])
    
    return PurchaseOrderResponse(**order)


@router.put("/orders/{order_id}/approve", response_model=PurchaseOrderResponse)
async def approve_order(
    order_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Approve a purchase order"""
    if current_user["role"] not in ["admin", "kitchen_manager", "procurement_manager"]:
        raise HTTPException(status_code=403, detail="Only managers can approve orders")
    
    order = await db.purchase_orders.find_one({"id": order_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    
    if order.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Order must be in pending status to approve")
    
    await db.purchase_orders.update_one(
        {"id": order_id},
        {"$set": {
            "status": "approved",
            "approved_by": current_user["id"],
            "approved_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    updated = await db.purchase_orders.find_one({"id": order_id}, {"_id": 0})
    if isinstance(updated.get('created_at'), str):
        updated['created_at'] = datetime.fromisoformat(updated['created_at'])
    if isinstance(updated.get('updated_at'), str):
        updated['updated_at'] = datetime.fromisoformat(updated['updated_at'])
    if isinstance(updated.get('approved_at'), str):
        updated['approved_at'] = datetime.fromisoformat(updated['approved_at'])
    
    return PurchaseOrderResponse(**updated)


@router.put("/orders/{order_id}/receive", response_model=PurchaseOrderResponse)
async def receive_order(
    order_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Mark order as received and update inventory"""
    order = await db.purchase_orders.find_one({"id": order_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    
    if order.get("status") not in ["approved", "ordered", "partially_received"]:
        raise HTTPException(status_code=400, detail="Order must be approved or ordered to receive")
    
    # Update order status
    await db.purchase_orders.update_one(
        {"id": order_id},
        {"$set": {
            "status": "received",
            "received_by": current_user["id"],
            "received_at": datetime.now(timezone.utc).isoformat(),
            "actual_delivery_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Update inventory for each item
    for item in order.get("items", []):
        # Check if inventory item exists
        existing = await db.inventory.find_one({
            "ingredient_id": item.get("ingredient_id"),
            "kitchen_id": order.get("kitchen_id")
        }, {"_id": 0})
        
        if existing:
            new_qty = existing.get("quantity", 0) + item.get("quantity", 0)
            await db.inventory.update_one(
                {"id": existing["id"]},
                {"$set": {
                    "quantity": new_qty,
                    "cost_per_unit": item.get("unit_price"),
                    "total_value": new_qty * item.get("unit_price", 0),
                    "received_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
    
    updated = await db.purchase_orders.find_one({"id": order_id}, {"_id": 0})
    if isinstance(updated.get('created_at'), str):
        updated['created_at'] = datetime.fromisoformat(updated['created_at'])
    if isinstance(updated.get('updated_at'), str):
        updated['updated_at'] = datetime.fromisoformat(updated['updated_at'])
    if isinstance(updated.get('approved_at'), str):
        updated['approved_at'] = datetime.fromisoformat(updated['approved_at'])
    if isinstance(updated.get('received_at'), str):
        updated['received_at'] = datetime.fromisoformat(updated['received_at'])
    
    return PurchaseOrderResponse(**updated)


@router.put("/orders/{order_id}/cancel", response_model=PurchaseOrderResponse)
async def cancel_order(
    order_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Cancel a purchase order"""
    order = await db.purchase_orders.find_one({"id": order_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    
    if order.get("status") in ["received", "cancelled"]:
        raise HTTPException(status_code=400, detail="Cannot cancel received or already cancelled orders")
    
    await db.purchase_orders.update_one(
        {"id": order_id},
        {"$set": {
            "status": "cancelled",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    updated = await db.purchase_orders.find_one({"id": order_id}, {"_id": 0})
    if isinstance(updated.get('created_at'), str):
        updated['created_at'] = datetime.fromisoformat(updated['created_at'])
    if isinstance(updated.get('updated_at'), str):
        updated['updated_at'] = datetime.fromisoformat(updated['updated_at'])
    
    return PurchaseOrderResponse(**updated)
