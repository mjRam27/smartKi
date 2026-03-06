from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.recipe import (
    Recipe, RecipeCreate, RecipeResponse, RecipeStatus,
    AIRecipeRequest, AIRecipeResponse
)
from services.ai_service import AIRecipeService
from dependencies import get_db, get_current_user

router = APIRouter(prefix="/recipes", tags=["Recipes"])


@router.post("/", response_model=RecipeResponse, status_code=status.HTTP_201_CREATED)
async def create_recipe(
    recipe_data: RecipeCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new recipe"""
    org_id = current_user.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=400, detail="User must belong to an organization")
    
    # Calculate total time
    prep_time = recipe_data.prep_time_minutes or 0
    cook_time = recipe_data.cook_time_minutes or 0
    total_time = prep_time + cook_time if prep_time or cook_time else None
    
    recipe = Recipe(
        **recipe_data.model_dump(),
        total_time_minutes=total_time,
        organization_id=org_id,
        created_by=current_user["id"]
    )
    
    recipe_dict = recipe.model_dump()
    recipe_dict['created_at'] = recipe_dict['created_at'].isoformat()
    recipe_dict['updated_at'] = recipe_dict['updated_at'].isoformat()
    
    await db.recipes.insert_one(recipe_dict)
    
    return RecipeResponse(**recipe.model_dump())


@router.get("/", response_model=List[RecipeResponse])
async def list_recipes(
    status: Optional[RecipeStatus] = None,
    cuisine_type: Optional[str] = None,
    category: Optional[str] = None,
    is_ai_generated: Optional[bool] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List recipes with filters"""
    org_id = current_user.get("organization_id")
    
    query = {}
    if current_user["role"] != "admin":
        if org_id:
            query["organization_id"] = org_id
        else:
            return []
    
    if status:
        query["status"] = status.value
    if cuisine_type:
        query["cuisine_type"] = cuisine_type
    if category:
        query["category"] = category
    if is_ai_generated is not None:
        query["is_ai_generated"] = is_ai_generated
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
            {"tags": {"$in": [search]}}
        ]
    
    recipes = await db.recipes.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    
    for recipe in recipes:
        if isinstance(recipe.get('created_at'), str):
            recipe['created_at'] = datetime.fromisoformat(recipe['created_at'])
        if isinstance(recipe.get('updated_at'), str):
            recipe['updated_at'] = datetime.fromisoformat(recipe['updated_at'])
    
    return [RecipeResponse(**r) for r in recipes]


@router.get("/{recipe_id}", response_model=RecipeResponse)
async def get_recipe(
    recipe_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get recipe by ID"""
    recipe = await db.recipes.find_one({"id": recipe_id}, {"_id": 0})
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    org_id = current_user.get("organization_id")
    if current_user["role"] != "admin" and recipe.get("organization_id") != org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if isinstance(recipe.get('created_at'), str):
        recipe['created_at'] = datetime.fromisoformat(recipe['created_at'])
    if isinstance(recipe.get('updated_at'), str):
        recipe['updated_at'] = datetime.fromisoformat(recipe['updated_at'])
    
    return RecipeResponse(**recipe)


@router.put("/{recipe_id}", response_model=RecipeResponse)
async def update_recipe(
    recipe_id: str,
    recipe_data: RecipeCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update recipe"""
    recipe = await db.recipes.find_one({"id": recipe_id}, {"_id": 0})
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    org_id = current_user.get("organization_id")
    if current_user["role"] not in ["admin", "kitchen_manager", "chef"] and recipe.get("organization_id") != org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    update_data = recipe_data.model_dump()
    prep_time = update_data.get('prep_time_minutes') or 0
    cook_time = update_data.get('cook_time_minutes') or 0
    update_data["total_time_minutes"] = prep_time + cook_time if prep_time or cook_time else None
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.recipes.update_one({"id": recipe_id}, {"$set": update_data})
    
    updated = await db.recipes.find_one({"id": recipe_id}, {"_id": 0})
    if isinstance(updated.get('created_at'), str):
        updated['created_at'] = datetime.fromisoformat(updated['created_at'])
    if isinstance(updated.get('updated_at'), str):
        updated['updated_at'] = datetime.fromisoformat(updated['updated_at'])
    
    return RecipeResponse(**updated)


@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recipe(
    recipe_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete recipe (archive)"""
    recipe = await db.recipes.find_one({"id": recipe_id}, {"_id": 0})
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    if current_user["role"] not in ["admin", "kitchen_manager", "chef"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    await db.recipes.update_one(
        {"id": recipe_id}, 
        {"$set": {"status": "archived", "updated_at": datetime.now(timezone.utc).isoformat()}}
    )


@router.post("/{recipe_id}/approve", response_model=RecipeResponse)
async def approve_recipe(
    recipe_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Approve a recipe (change from pending_review to active)"""
    if current_user["role"] not in ["admin", "kitchen_manager", "chef"]:
        raise HTTPException(status_code=403, detail="Only managers and chefs can approve recipes")
    
    recipe = await db.recipes.find_one({"id": recipe_id}, {"_id": 0})
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    await db.recipes.update_one(
        {"id": recipe_id},
        {"$set": {"status": "active", "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    updated = await db.recipes.find_one({"id": recipe_id}, {"_id": 0})
    if isinstance(updated.get('created_at'), str):
        updated['created_at'] = datetime.fromisoformat(updated['created_at'])
    if isinstance(updated.get('updated_at'), str):
        updated['updated_at'] = datetime.fromisoformat(updated['updated_at'])
    
    return RecipeResponse(**updated)


@router.post("/generate", response_model=AIRecipeResponse)
async def generate_ai_recipe(
    request: AIRecipeRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Generate a recipe using AI"""
    org_id = current_user.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=400, detail="User must belong to an organization")
    
    ai_service = AIRecipeService(db)
    result = await ai_service.generate_recipe(request, current_user["id"], org_id)
    
    return result
