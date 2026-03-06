from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone
from enum import Enum
import uuid


class OrderStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    ORDERED = "ordered"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class PurchaseOrderItem(BaseModel):
    ingredient_id: str
    ingredient_name: str
    quantity: float
    unit: str
    unit_price: float
    total_price: float
    received_quantity: float = 0.0
    notes: Optional[str] = None


class PurchaseOrder(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    order_number: str
    supplier_id: str
    supplier_name: Optional[str] = None
    kitchen_id: str
    organization_id: str
    items: List[PurchaseOrderItem] = Field(default_factory=list)
    subtotal: float = 0.0
    tax: float = 0.0
    shipping: float = 0.0
    total: float = 0.0
    status: OrderStatus = OrderStatus.DRAFT
    notes: Optional[str] = None
    expected_delivery_date: Optional[str] = None
    actual_delivery_date: Optional[str] = None
    created_by: str
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    received_by: Optional[str] = None
    received_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PurchaseOrderCreate(BaseModel):
    supplier_id: str
    kitchen_id: str
    items: List[PurchaseOrderItem] = Field(default_factory=list)
    tax: float = 0.0
    shipping: float = 0.0
    notes: Optional[str] = None
    expected_delivery_date: Optional[str] = None


class PurchaseOrderResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str
    order_number: str
    supplier_id: str
    supplier_name: Optional[str] = None
    kitchen_id: str
    organization_id: str
    items: List[PurchaseOrderItem]
    subtotal: float
    tax: float
    shipping: float
    total: float
    status: OrderStatus
    notes: Optional[str] = None
    expected_delivery_date: Optional[str] = None
    actual_delivery_date: Optional[str] = None
    created_by: str
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
