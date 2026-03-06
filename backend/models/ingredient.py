from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone
from enum import Enum
import uuid


class IngredientCategory(str, Enum):
    PRODUCE = "produce"
    MEAT = "meat"
    SEAFOOD = "seafood"
    DAIRY = "dairy"
    GRAINS = "grains"
    SPICES = "spices"
    OILS = "oils"
    SAUCES = "sauces"
    BEVERAGES = "beverages"
    FROZEN = "frozen"
    CANNED = "canned"
    DRY_GOODS = "dry_goods"
    OTHER = "other"


class Ingredient(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    category: IngredientCategory = IngredientCategory.OTHER
    description: Optional[str] = None
    default_unit: str = "unit"
    cost_per_unit: Optional[float] = None
    allergens: List[str] = Field(default_factory=list)
    nutritional_info: Optional[dict] = None
    storage_instructions: Optional[str] = None
    shelf_life_days: Optional[int] = None
    is_perishable: bool = False
    minimum_order_quantity: Optional[float] = None
    supplier_ids: List[str] = Field(default_factory=list)
    organization_id: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class IngredientCreate(BaseModel):
    name: str = Field(min_length=1)
    category: IngredientCategory = IngredientCategory.OTHER
    description: Optional[str] = None
    default_unit: str = "unit"
    cost_per_unit: Optional[float] = None
    allergens: List[str] = Field(default_factory=list)
    nutritional_info: Optional[dict] = None
    storage_instructions: Optional[str] = None
    shelf_life_days: Optional[int] = None
    is_perishable: bool = False
    minimum_order_quantity: Optional[float] = None
    supplier_ids: List[str] = Field(default_factory=list)


class IngredientResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str
    name: str
    category: IngredientCategory
    description: Optional[str] = None
    default_unit: str
    cost_per_unit: Optional[float] = None
    allergens: List[str]
    nutritional_info: Optional[dict] = None
    storage_instructions: Optional[str] = None
    shelf_life_days: Optional[int] = None
    is_perishable: bool
    minimum_order_quantity: Optional[float] = None
    supplier_ids: List[str]
    organization_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
