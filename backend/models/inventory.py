from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone, date
from enum import Enum
import uuid


class MovementType(str, Enum):
    RECEIPT = "receipt"
    ISSUE = "issue"
    ADJUSTMENT = "adjustment"
    TRANSFER = "transfer"
    WASTE = "waste"
    RETURN = "return"


class InventoryItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ingredient_id: str
    kitchen_id: str
    organization_id: str
    quantity: float = 0.0
    unit: str
    par_level: Optional[float] = None
    reorder_point: Optional[float] = None
    location: Optional[str] = None
    batch_number: Optional[str] = None
    expiry_date: Optional[str] = None
    received_date: Optional[str] = None
    cost_per_unit: Optional[float] = None
    total_value: Optional[float] = None
    last_count_date: Optional[str] = None
    last_count_by: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class InventoryItemCreate(BaseModel):
    ingredient_id: str
    kitchen_id: str
    quantity: float = 0.0
    unit: str
    par_level: Optional[float] = None
    reorder_point: Optional[float] = None
    location: Optional[str] = None
    batch_number: Optional[str] = None
    expiry_date: Optional[str] = None
    received_date: Optional[str] = None
    cost_per_unit: Optional[float] = None


class InventoryItemResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str
    ingredient_id: str
    kitchen_id: str
    organization_id: str
    quantity: float
    unit: str
    par_level: Optional[float] = None
    reorder_point: Optional[float] = None
    location: Optional[str] = None
    batch_number: Optional[str] = None
    expiry_date: Optional[str] = None
    received_date: Optional[str] = None
    cost_per_unit: Optional[float] = None
    total_value: Optional[float] = None
    last_count_date: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    ingredient_name: Optional[str] = None


class InventoryMovement(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    inventory_item_id: str
    kitchen_id: str
    organization_id: str
    movement_type: MovementType
    quantity: float
    unit: str
    reference_id: Optional[str] = None
    reference_type: Optional[str] = None
    notes: Optional[str] = None
    performed_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
