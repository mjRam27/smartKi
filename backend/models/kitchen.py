from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone
import uuid


class Kitchen(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    organization_id: str
    location: Optional[str] = None
    description: Optional[str] = None
    capacity: Optional[int] = None
    manager_id: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class KitchenCreate(BaseModel):
    name: str = Field(min_length=1)
    location: Optional[str] = None
    description: Optional[str] = None
    capacity: Optional[int] = None
    manager_id: Optional[str] = None


class KitchenResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str
    name: str
    organization_id: str
    location: Optional[str] = None
    description: Optional[str] = None
    capacity: Optional[int] = None
    manager_id: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
