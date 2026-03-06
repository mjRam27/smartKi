from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.ingredient import Ingredient, IngredientCreate, IngredientResponse, IngredientCategory
from dependencies import get_db, get_current_user

router = APIRouter(prefix="/ingredients", tags=["Ingredients"])


@router.post("/", response_model=IngredientResponse, status_code=status.HTTP_201_CREATED)
async def create_ingredient(
    ingredient_data: IngredientCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new ingredient"""
    org_id = current_user.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=400, detail="User must belong to an organization")
    
    ingredient = Ingredient(
        **ingredient_data.model_dump(),
        organization_id=org_id
    )
    
    ingredient_dict = ingredient.model_dump()
    ingredient_dict['created_at'] = ingredient_dict['created_at'].isoformat()
    ingredient_dict['updated_at'] = ingredient_dict['updated_at'].isoformat()
    
    await db.ingredients.insert_one(ingredient_dict)
    
    return IngredientResponse(**ingredient.model_dump())


@router.get("/", response_model=List[IngredientResponse])
async def list_ingredients(
    category: Optional[IngredientCategory] = None,
    search: Optional[str] = None,
    is_perishable: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List ingredients with filters"""
    org_id = current_user.get("organization_id")
    
    query = {"is_active": True}
    if current_user["role"] != "admin":
        if org_id:
            query["organization_id"] = org_id
        else:
            return []
    
    if category:
        query["category"] = category.value
    if is_perishable is not None:
        query["is_perishable"] = is_perishable
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]
    
    ingredients = await db.ingredients.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    
    for ing in ingredients:
        if isinstance(ing.get('created_at'), str):
            ing['created_at'] = datetime.fromisoformat(ing['created_at'])
        if isinstance(ing.get('updated_at'), str):
            ing['updated_at'] = datetime.fromisoformat(ing['updated_at'])
    
    return [IngredientResponse(**i) for i in ingredients]


@router.get("/{ingredient_id}", response_model=IngredientResponse)
async def get_ingredient(
    ingredient_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get ingredient by ID"""
    ingredient = await db.ingredients.find_one({"id": ingredient_id}, {"_id": 0})
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    
    org_id = current_user.get("organization_id")
    if current_user["role"] != "admin" and ingredient.get("organization_id") != org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if isinstance(ingredient.get('created_at'), str):
        ingredient['created_at'] = datetime.fromisoformat(ingredient['created_at'])
    if isinstance(ingredient.get('updated_at'), str):
        ingredient['updated_at'] = datetime.fromisoformat(ingredient['updated_at'])
    
    return IngredientResponse(**ingredient)


@router.put("/{ingredient_id}", response_model=IngredientResponse)
async def update_ingredient(
    ingredient_id: str,
    ingredient_data: IngredientCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update ingredient"""
    ingredient = await db.ingredients.find_one({"id": ingredient_id}, {"_id": 0})
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    
    org_id = current_user.get("organization_id")
    if current_user["role"] not in ["admin", "kitchen_manager", "chef", "procurement_manager"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    update_data = ingredient_data.model_dump()
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.ingredients.update_one({"id": ingredient_id}, {"$set": update_data})
    
    updated = await db.ingredients.find_one({"id": ingredient_id}, {"_id": 0})
    if isinstance(updated.get('created_at'), str):
        updated['created_at'] = datetime.fromisoformat(updated['created_at'])
    if isinstance(updated.get('updated_at'), str):
        updated['updated_at'] = datetime.fromisoformat(updated['updated_at'])
    
    return IngredientResponse(**updated)


@router.delete("/{ingredient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ingredient(
    ingredient_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete ingredient (soft delete)"""
    ingredient = await db.ingredients.find_one({"id": ingredient_id}, {"_id": 0})
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    
    if current_user["role"] not in ["admin", "kitchen_manager"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    await db.ingredients.update_one(
        {"id": ingredient_id}, 
        {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
