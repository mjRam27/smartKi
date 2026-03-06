from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import uuid


class RecipeStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    PENDING_REVIEW = "pending_review"


class RecipeIngredient(BaseModel):
    ingredient_id: Optional[str] = None
    name: str
    quantity: float
    unit: str
    notes: Optional[str] = None
    estimated_cost: Optional[float] = None


class NutritionInfo(BaseModel):
    calories: Optional[float] = None
    protein: Optional[float] = None
    carbohydrates: Optional[float] = None
    fat: Optional[float] = None
    fiber: Optional[float] = None
    sodium: Optional[float] = None
    sugar: Optional[float] = None


class Recipe(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    cuisine_type: Optional[str] = None
    dietary_preferences: List[str] = Field(default_factory=list)
    servings: int = 1
    prep_time_minutes: Optional[int] = None
    cook_time_minutes: Optional[int] = None
    total_time_minutes: Optional[int] = None
    ingredients: List[RecipeIngredient] = Field(default_factory=list)
    instructions: List[str] = Field(default_factory=list)
    allergens: List[str] = Field(default_factory=list)
    nutrition: Optional[NutritionInfo] = None
    estimated_cost_per_serving: Optional[float] = None
    tags: List[str] = Field(default_factory=list)
    category: Optional[str] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    status: RecipeStatus = RecipeStatus.DRAFT
    is_ai_generated: bool = False
    organization_id: str
    kitchen_id: Optional[str] = None
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RecipeCreate(BaseModel):
    title: str = Field(min_length=1)
    description: Optional[str] = None
    cuisine_type: Optional[str] = None
    dietary_preferences: List[str] = Field(default_factory=list)
    servings: int = 1
    prep_time_minutes: Optional[int] = None
    cook_time_minutes: Optional[int] = None
    ingredients: List[RecipeIngredient] = Field(default_factory=list)
    instructions: List[str] = Field(default_factory=list)
    allergens: List[str] = Field(default_factory=list)
    nutrition: Optional[NutritionInfo] = None
    estimated_cost_per_serving: Optional[float] = None
    tags: List[str] = Field(default_factory=list)
    category: Optional[str] = None
    kitchen_id: Optional[str] = None
    status: RecipeStatus = RecipeStatus.DRAFT


class RecipeResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str
    title: str
    description: Optional[str] = None
    cuisine_type: Optional[str] = None
    dietary_preferences: List[str]
    servings: int
    prep_time_minutes: Optional[int] = None
    cook_time_minutes: Optional[int] = None
    total_time_minutes: Optional[int] = None
    ingredients: List[RecipeIngredient]
    instructions: List[str]
    allergens: List[str]
    nutrition: Optional[NutritionInfo] = None
    estimated_cost_per_serving: Optional[float] = None
    tags: List[str]
    category: Optional[str] = None
    image_url: Optional[str] = None
    status: RecipeStatus
    is_ai_generated: bool
    organization_id: str
    kitchen_id: Optional[str] = None
    created_by: str
    created_at: datetime
    updated_at: datetime


class AIRecipeRequest(BaseModel):
    recipe_name: str = Field(min_length=1, description="Name or title hint for the recipe")
    short_description: Optional[str] = Field(None, description="Brief description of what you want")
    cuisine_type: Optional[str] = Field(None, description="e.g., Italian, Mexican, Asian, Mediterranean")
    dietary_preference: Optional[str] = Field(None, description="e.g., vegetarian, vegan, gluten-free, keto")
    serving_count: int = Field(default=4, ge=1, le=100)
    include_ingredients: List[str] = Field(default_factory=list, description="Ingredients to include")
    avoid_ingredients: List[str] = Field(default_factory=list, description="Ingredients to avoid")
    kitchen_id: Optional[str] = None


class AIRecipeResponse(BaseModel):
    success: bool
    recipe: Optional[RecipeResponse] = None
    error: Optional[str] = None
    raw_ai_response: Optional[Dict[str, Any]] = None
