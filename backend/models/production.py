from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone
from enum import Enum
import uuid


class ProductionStatus(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ProductionLog(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    kitchen_id: str
    organization_id: str
    recipe_id: str
    recipe_name: str
    planned_quantity: int
    actual_quantity: Optional[int] = None
    servings_produced: Optional[int] = None
    servings_sold: Optional[int] = None
    servings_wasted: Optional[int] = None
    unit_price: Optional[float] = None
    total_revenue: Optional[float] = None
    production_cost: Optional[float] = None
    profit: Optional[float] = None
    status: ProductionStatus = ProductionStatus.PLANNED
    scheduled_date: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProductionLogCreate(BaseModel):
    kitchen_id: str
    recipe_id: str
    recipe_name: str
    planned_quantity: int
    unit_price: Optional[float] = None
    scheduled_date: str
    notes: Optional[str] = None


class ProductionLogResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str
    kitchen_id: str
    organization_id: str
    recipe_id: str
    recipe_name: str
    planned_quantity: int
    actual_quantity: Optional[int] = None
    servings_produced: Optional[int] = None
    servings_sold: Optional[int] = None
    servings_wasted: Optional[int] = None
    unit_price: Optional[float] = None
    total_revenue: Optional[float] = None
    production_cost: Optional[float] = None
    profit: Optional[float] = None
    status: ProductionStatus
    scheduled_date: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_by: str
    created_at: datetime
    updated_at: datetime
