from fastapi import FastAPI, APIRouter
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL')
db_name = os.environ.get('DB_NAME')
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

# Create the main app
app = FastAPI(
    title="Kitchen Intelligence Platform",
    description="Enterprise SaaS platform for professional kitchen management",
    version="1.0.0"
)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Import and include routers
from routers.auth import router as auth_router
from routers.organizations import router as organizations_router
from routers.kitchens import router as kitchens_router
from routers.recipes import router as recipes_router
from routers.ingredients import router as ingredients_router
from routers.inventory import router as inventory_router
from routers.suppliers import router as suppliers_router
from routers.procurement import router as procurement_router
from routers.waste import router as waste_router
from routers.production import router as production_router
from routers.analytics import router as analytics_router

# Include all routers
api_router.include_router(auth_router)
api_router.include_router(organizations_router)
api_router.include_router(kitchens_router)
api_router.include_router(recipes_router)
api_router.include_router(ingredients_router)
api_router.include_router(inventory_router)
api_router.include_router(suppliers_router)
api_router.include_router(procurement_router)
api_router.include_router(waste_router)
api_router.include_router(production_router)
api_router.include_router(analytics_router)


# Health check endpoint
@api_router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Kitchen Intelligence Platform",
        "version": "1.0.0"
    }


# Root endpoint
@api_router.get("/")
async def root():
    return {
        "message": "Kitchen Intelligence Platform API",
        "version": "1.0.0",
        "docs": "/docs"
    }


# Include the router in the main app
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@app.on_event("startup")
async def startup_db():
    logger.info("Kitchen Intelligence Platform starting up...")
    # Create indexes for better query performance
    await db.users.create_index("email", unique=True)
    await db.users.create_index("id", unique=True)
    await db.organizations.create_index("id", unique=True)
    await db.kitchens.create_index("id", unique=True)
    await db.kitchens.create_index("organization_id")
    await db.recipes.create_index("id", unique=True)
    await db.recipes.create_index("organization_id")
    await db.ingredients.create_index("id", unique=True)
    await db.ingredients.create_index("organization_id")
    await db.inventory.create_index("id", unique=True)
    await db.inventory.create_index([("kitchen_id", 1), ("ingredient_id", 1)])
    await db.suppliers.create_index("id", unique=True)
    await db.suppliers.create_index("organization_id")
    await db.purchase_orders.create_index("id", unique=True)
    await db.purchase_orders.create_index("order_number", unique=True)
    await db.waste_logs.create_index("id", unique=True)
    await db.waste_logs.create_index([("organization_id", 1), ("logged_at", -1)])
    await db.production_logs.create_index("id", unique=True)
    await db.production_logs.create_index([("organization_id", 1), ("scheduled_date", -1)])
    logger.info("Database indexes created")


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
    logger.info("Kitchen Intelligence Platform shutting down...")
