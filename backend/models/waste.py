from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone
from enum import Enum
import uuid


class WasteReason(str, Enum):
    EXPIRED = "expired"
    SPOILED = "spoiled"
    OVERPRODUCTION = "overproduction"
    PLATE_WASTE = "plate_waste"
    PREP_WASTE = "prep_waste"
    DAMAGED = "damaged"
    QUALITY_ISSUE = "quality_issue"
    OTHER = "other"


class WasteLog(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    kitchen_id: str
    organization_id: str
    ingredient_id: Optional[str] = None
    ingredient_name: str
    recipe_id: Optional[str] = None
    recipe_name: Optional[str] = None
    quantity: float
    unit: str
    reason: WasteReason
    estimated_cost: Optional[float] = None
    notes: Optional[str] = None
    logged_by: str
    logged_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class WasteLogCreate(BaseModel):
    kitchen_id: str
    ingredient_id: Optional[str] = None
    ingredient_name: str
    recipe_id: Optional[str] = None
    recipe_name: Optional[str] = None
    quantity: float
    unit: str
    reason: WasteReason
    estimated_cost: Optional[float] = None
    notes: Optional[str] = None


class WasteLogResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str
    kitchen_id: str
    organization_id: str
    ingredient_id: Optional[str] = None
    ingredient_name: str
    recipe_id: Optional[str] = None
    recipe_name: Optional[str] = None
    quantity: float
    unit: str
    reason: WasteReason
    estimated_cost: Optional[float] = None
    notes: Optional[str] = None
    logged_by: str
    logged_at: datetime
    created_at: datetime
