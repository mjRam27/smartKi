from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone
from enum import Enum
import uuid


class SupplierStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"


class Supplier(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    code: Optional[str] = None
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    website: Optional[str] = None
    payment_terms: Optional[str] = None
    lead_time_days: Optional[int] = None
    minimum_order_value: Optional[float] = None
    rating: Optional[float] = None
    categories: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    status: SupplierStatus = SupplierStatus.ACTIVE
    organization_id: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SupplierCreate(BaseModel):
    name: str = Field(min_length=1)
    code: Optional[str] = None
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    website: Optional[str] = None
    payment_terms: Optional[str] = None
    lead_time_days: Optional[int] = None
    minimum_order_value: Optional[float] = None
    categories: List[str] = Field(default_factory=list)
    notes: Optional[str] = None


class SupplierResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str
    name: str
    code: Optional[str] = None
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    website: Optional[str] = None
    payment_terms: Optional[str] = None
    lead_time_days: Optional[int] = None
    minimum_order_value: Optional[float] = None
    rating: Optional[float] = None
    categories: List[str]
    notes: Optional[str] = None
    status: SupplierStatus
    organization_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
