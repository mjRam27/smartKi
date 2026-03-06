# Kitchen Intelligence Platform - Routers
from .auth import router as auth_router
from .organizations import router as organizations_router
from .kitchens import router as kitchens_router
from .recipes import router as recipes_router
from .ingredients import router as ingredients_router
from .inventory import router as inventory_router
from .suppliers import router as suppliers_router
from .procurement import router as procurement_router
from .waste import router as waste_router
from .production import router as production_router
from .analytics import router as analytics_router

__all__ = [
    "auth_router",
    "organizations_router", 
    "kitchens_router",
    "recipes_router",
    "ingredients_router",
    "inventory_router",
    "suppliers_router",
    "procurement_router",
    "waste_router",
    "production_router",
    "analytics_router",
]
