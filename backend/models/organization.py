from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone
import uuid


class OrganizationType(str):
    CORPORATE_CAFETERIA = "corporate_cafeteria"
    HOSPITAL = "hospital"
    UNIVERSITY = "university"
    CATERING = "catering"
    RESTAURANT = "restaurant"
    OTHER = "other"


class Organization(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: str = "other"
    description: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None
    owner_id: str
    subscription_tier: str = "free"
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=1)
    type: str = "other"
    description: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None


class OrganizationResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str
    name: str
    type: str
    description: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None
    owner_id: str
    subscription_tier: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
