import os
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from dotenv import load_dotenv
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorDatabase

from models.recipe import (
    Recipe, RecipeCreate, RecipeResponse, AIRecipeRequest, AIRecipeResponse,
    RecipeIngredient, NutritionInfo, RecipeStatus
)

ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

logger = logging.getLogger(__name__)


class AIRecipeService:
    """AI-powered recipe generation service using Emergent LLM integration"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.llm_provider = os.getenv('LLM_PROVIDER', 'openai')
        self.llm_model = os.getenv('LLM_MODEL', 'gpt-5.2')
        self.api_key = os.getenv('EMERGENT_LLM_KEY') or os.getenv('LLM_API_KEY')
        
    def _get_system_prompt(self) -> str:
        """Generate system prompt for recipe generation"""
        return """You are an expert professional chef and culinary consultant. Your task is to generate detailed, professional-grade recipes suitable for commercial kitchens.

When generating a recipe, you MUST respond with valid JSON in the following exact structure:
{
    "title": "Recipe Name",
    "summary": "Brief description of the dish",
    "cuisine_type": "Italian/Mexican/Asian/etc",
    "dietary_info": ["vegetarian", "gluten-free", etc],
    "servings": 4,
    "prep_time_minutes": 30,
    "cook_time_minutes": 45,
    "ingredients": [
        {"name": "Ingredient name", "quantity": 2.5, "unit": "cups", "notes": "optional preparation notes"}
    ],
    "instructions": [
        "Step 1: Detailed instruction",
        "Step 2: Detailed instruction"
    ],
    "allergens": ["dairy", "gluten", etc],
    "nutrition_per_serving": {
        "calories": 450,
        "protein": 25,
        "carbohydrates": 35,
        "fat": 18,
        "fiber": 6,
        "sodium": 580
    },
    "estimated_cost_per_serving": 3.50,
    "tags": ["comfort food", "quick meal", etc],
    "category": "Main Course/Appetizer/Dessert/etc",
    "chef_notes": "Professional tips for best results"
}

Ensure all measurements are precise and suitable for commercial kitchen scaling. Include professional culinary terminology where appropriate."""

    def _get_user_prompt(self, request: AIRecipeRequest) -> str:
        """Generate user prompt from request"""
        prompt_parts = [f"Generate a detailed professional recipe for: {request.recipe_name}"]
        
        if request.short_description:
            prompt_parts.append(f"Description: {request.short_description}")
        
        if request.cuisine_type:
            prompt_parts.append(f"Cuisine: {request.cuisine_type}")
        
        if request.dietary_preference:
            prompt_parts.append(f"Dietary requirements: {request.dietary_preference}")
        
        prompt_parts.append(f"Servings: {request.serving_count}")
        
        if request.include_ingredients:
            prompt_parts.append(f"Must include these ingredients: {', '.join(request.include_ingredients)}")
        
        if request.avoid_ingredients:
            prompt_parts.append(f"Must avoid these ingredients: {', '.join(request.avoid_ingredients)}")
        
        prompt_parts.append("\nRespond ONLY with valid JSON matching the specified structure. No additional text.")
        
        return "\n".join(prompt_parts)

    async def generate_recipe(
        self, 
        request: AIRecipeRequest,
        user_id: str,
        organization_id: str
    ) -> AIRecipeResponse:
        """Generate a recipe using AI"""
        
        if not self.api_key:
            return AIRecipeResponse(
                success=False,
                error="AI service not configured. Please set LLM_API_KEY or EMERGENT_LLM_KEY environment variable."
            )
        
        try:
            # Import Emergent integrations
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            
            # Initialize chat with provider configuration
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"recipe-gen-{user_id}-{datetime.now(timezone.utc).timestamp()}",
                system_message=self._get_system_prompt()
            )
            
            # Configure model based on provider
            if self.llm_provider.lower() == 'openai':
                chat.with_model("openai", self.llm_model)
            elif self.llm_provider.lower() == 'anthropic':
                chat.with_model("anthropic", self.llm_model)
            elif self.llm_provider.lower() == 'gemini':
                chat.with_model("gemini", self.llm_model)
            
            # Create user message
            user_message = UserMessage(text=self._get_user_prompt(request))
            
            # Send message and get response
            response_text = await chat.send_message(user_message)
            
            logger.info(f"AI response received for recipe: {request.recipe_name}")
            
            # Parse JSON response
            ai_data = self._parse_ai_response(response_text)
            
            if not ai_data:
                return AIRecipeResponse(
                    success=False,
                    error="Failed to parse AI response. Invalid JSON format.",
                    raw_ai_response={"raw_text": response_text[:1000]}
                )
            
            # Validate and create recipe
            recipe = self._create_recipe_from_ai(ai_data, request, user_id, organization_id)
            
            # Save recipe to database
            recipe_dict = recipe.model_dump()
            recipe_dict['created_at'] = recipe_dict['created_at'].isoformat()
            recipe_dict['updated_at'] = recipe_dict['updated_at'].isoformat()
            
            await self.db.recipes.insert_one(recipe_dict)
            
            recipe_response = RecipeResponse(**recipe.model_dump())
            
            return AIRecipeResponse(
                success=True,
                recipe=recipe_response,
                raw_ai_response=ai_data
            )
            
        except ImportError as e:
            logger.error(f"Emergent integrations not available: {e}")
            return AIRecipeResponse(
                success=False,
                error="AI service integration not available. Please install emergentintegrations package."
            )
        except Exception as e:
            logger.error(f"AI recipe generation failed: {e}")
            return AIRecipeResponse(
                success=False,
                error=f"Recipe generation failed: {str(e)}"
            )

    def _parse_ai_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse AI response text to JSON"""
        try:
            # Try direct JSON parse
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass
        
        # Try to extract JSON from markdown code blocks
        try:
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                json_str = response_text[start:end].strip()
                return json.loads(json_str)
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                json_str = response_text[start:end].strip()
                return json.loads(json_str)
        except (json.JSONDecodeError, ValueError):
            pass
        
        # Try to find JSON object in text
        try:
            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            if start != -1 and end > start:
                json_str = response_text[start:end]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        return None

    def _create_recipe_from_ai(
        self, 
        ai_data: Dict[str, Any],
        request: AIRecipeRequest,
        user_id: str,
        organization_id: str
    ) -> Recipe:
        """Create a Recipe object from AI-generated data"""
        
        # Parse ingredients
        ingredients = []
        for ing in ai_data.get("ingredients", []):
            ingredients.append(RecipeIngredient(
                name=ing.get("name", ""),
                quantity=float(ing.get("quantity", 0)),
                unit=ing.get("unit", "unit"),
                notes=ing.get("notes")
            ))
        
        # Parse nutrition
        nutrition = None
        if "nutrition_per_serving" in ai_data:
            nut = ai_data["nutrition_per_serving"]
            nutrition = NutritionInfo(
                calories=nut.get("calories"),
                protein=nut.get("protein"),
                carbohydrates=nut.get("carbohydrates"),
                fat=nut.get("fat"),
                fiber=nut.get("fiber"),
                sodium=nut.get("sodium"),
                sugar=nut.get("sugar")
            )
        
        # Calculate total time
        prep_time = ai_data.get("prep_time_minutes", 0) or 0
        cook_time = ai_data.get("cook_time_minutes", 0) or 0
        total_time = prep_time + cook_time if prep_time or cook_time else None
        
        # Build dietary preferences
        dietary = ai_data.get("dietary_info", [])
        if request.dietary_preference and request.dietary_preference not in dietary:
            dietary.append(request.dietary_preference)
        
        return Recipe(
            title=ai_data.get("title", request.recipe_name),
            description=ai_data.get("summary", request.short_description),
            cuisine_type=ai_data.get("cuisine_type", request.cuisine_type),
            dietary_preferences=dietary,
            servings=ai_data.get("servings", request.serving_count),
            prep_time_minutes=prep_time if prep_time else None,
            cook_time_minutes=cook_time if cook_time else None,
            total_time_minutes=total_time,
            ingredients=ingredients,
            instructions=ai_data.get("instructions", []),
            allergens=ai_data.get("allergens", []),
            nutrition=nutrition,
            estimated_cost_per_serving=ai_data.get("estimated_cost_per_serving"),
            tags=ai_data.get("tags", []),
            category=ai_data.get("category"),
            status=RecipeStatus.PENDING_REVIEW,
            is_ai_generated=True,
            organization_id=organization_id,
            kitchen_id=request.kitchen_id,
            created_by=user_id
        )
