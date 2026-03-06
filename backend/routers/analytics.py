from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
from dependencies import get_db, get_current_user

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard")
async def get_dashboard_metrics(
    kitchen_id: Optional[str] = None,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get main dashboard metrics"""
    org_id = current_user.get("organization_id")
    
    query = {}
    if current_user["role"] != "admin":
        if org_id:
            query["organization_id"] = org_id
        else:
            return {"error": "No organization"}
    
    if kitchen_id:
        query["kitchen_id"] = kitchen_id
    
    # Count metrics
    recipes_count = await db.recipes.count_documents({**query, "status": {"$ne": "archived"}})
    ingredients_count = await db.ingredients.count_documents({**query, "is_active": True})
    suppliers_count = await db.suppliers.count_documents({**query, "is_active": True})
    kitchens_count = await db.kitchens.count_documents({"organization_id": org_id, "is_active": True}) if org_id else 0
    
    # Inventory value
    inventory_query = query.copy()
    inventory_items = await db.inventory.find(inventory_query, {"_id": 0}).to_list(1000)
    total_inventory_value = sum(item.get("total_value", 0) or 0 for item in inventory_items)
    low_stock_count = sum(1 for item in inventory_items if item.get("reorder_point") and item.get("quantity", 0) <= item["reorder_point"])
    
    # Recent orders
    orders_query = query.copy()
    pending_orders = await db.purchase_orders.count_documents({**orders_query, "status": "pending"})
    
    # Waste this week
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    waste_query = query.copy()
    waste_logs = await db.waste_logs.find({**waste_query}, {"_id": 0}).to_list(1000)
    weekly_waste_cost = sum(log.get("estimated_cost", 0) or 0 for log in waste_logs)
    
    # Production stats
    prod_query = query.copy()
    prod_logs = await db.production_logs.find({**prod_query, "status": "completed"}, {"_id": 0}).to_list(1000)
    total_revenue = sum(log.get("total_revenue", 0) or 0 for log in prod_logs)
    total_profit = sum(log.get("profit", 0) or 0 for log in prod_logs if log.get("profit"))
    
    return {
        "overview": {
            "recipes": recipes_count,
            "ingredients": ingredients_count,
            "suppliers": suppliers_count,
            "kitchens": kitchens_count
        },
        "inventory": {
            "total_value": round(total_inventory_value, 2),
            "low_stock_items": low_stock_count,
            "items_count": len(inventory_items)
        },
        "orders": {
            "pending": pending_orders
        },
        "waste": {
            "weekly_cost": round(weekly_waste_cost, 2),
            "entries_count": len(waste_logs)
        },
        "production": {
            "total_revenue": round(total_revenue, 2),
            "total_profit": round(total_profit, 2),
            "batches_completed": len(prod_logs)
        }
    }


@router.get("/waste-trends")
async def get_waste_trends(
    kitchen_id: Optional[str] = None,
    days: int = Query(30, ge=7, le=365),
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get waste trends over time"""
    org_id = current_user.get("organization_id")
    
    query = {}
    if current_user["role"] != "admin":
        if org_id:
            query["organization_id"] = org_id
        else:
            return {"trends": [], "by_reason": {}}
    
    if kitchen_id:
        query["kitchen_id"] = kitchen_id
    
    logs = await db.waste_logs.find(query, {"_id": 0}).to_list(10000)
    
    # Group by date
    by_date = {}
    by_reason = {}
    
    for log in logs:
        logged_at = log.get("logged_at")
        if isinstance(logged_at, str):
            date_key = logged_at[:10]
        else:
            date_key = logged_at.strftime("%Y-%m-%d") if logged_at else "unknown"
        
        cost = log.get("estimated_cost", 0) or 0
        reason = log.get("reason", "other")
        
        if date_key not in by_date:
            by_date[date_key] = {"date": date_key, "cost": 0, "count": 0}
        by_date[date_key]["cost"] += cost
        by_date[date_key]["count"] += 1
        
        if reason not in by_reason:
            by_reason[reason] = {"cost": 0, "count": 0}
        by_reason[reason]["cost"] += cost
        by_reason[reason]["count"] += 1
    
    trends = sorted(by_date.values(), key=lambda x: x["date"])[-days:]
    
    return {
        "trends": trends,
        "by_reason": by_reason,
        "total_cost": sum(t["cost"] for t in trends),
        "total_entries": sum(t["count"] for t in trends)
    }


@router.get("/profitability")
async def get_profitability_analytics(
    kitchen_id: Optional[str] = None,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get profitability analytics"""
    org_id = current_user.get("organization_id")
    
    query = {"status": "completed"}
    if current_user["role"] != "admin":
        if org_id:
            query["organization_id"] = org_id
        else:
            return {"by_recipe": [], "summary": {}}
    
    if kitchen_id:
        query["kitchen_id"] = kitchen_id
    
    logs = await db.production_logs.find(query, {"_id": 0}).to_list(10000)
    
    # Group by recipe
    by_recipe = {}
    
    for log in logs:
        recipe_id = log.get("recipe_id")
        recipe_name = log.get("recipe_name", "Unknown")
        
        if recipe_id not in by_recipe:
            by_recipe[recipe_id] = {
                "recipe_id": recipe_id,
                "recipe_name": recipe_name,
                "total_produced": 0,
                "total_sold": 0,
                "total_wasted": 0,
                "total_revenue": 0,
                "total_cost": 0,
                "total_profit": 0,
                "batches": 0
            }
        
        by_recipe[recipe_id]["total_produced"] += log.get("servings_produced", 0) or 0
        by_recipe[recipe_id]["total_sold"] += log.get("servings_sold", 0) or 0
        by_recipe[recipe_id]["total_wasted"] += log.get("servings_wasted", 0) or 0
        by_recipe[recipe_id]["total_revenue"] += log.get("total_revenue", 0) or 0
        by_recipe[recipe_id]["total_cost"] += log.get("production_cost", 0) or 0
        by_recipe[recipe_id]["total_profit"] += log.get("profit", 0) or 0
        by_recipe[recipe_id]["batches"] += 1
    
    # Calculate margins
    for recipe in by_recipe.values():
        if recipe["total_revenue"] > 0:
            recipe["margin_percent"] = round((recipe["total_profit"] / recipe["total_revenue"]) * 100, 1)
        else:
            recipe["margin_percent"] = 0
    
    recipes_list = sorted(by_recipe.values(), key=lambda x: x["total_profit"], reverse=True)
    
    return {
        "by_recipe": recipes_list,
        "summary": {
            "total_revenue": sum(r["total_revenue"] for r in recipes_list),
            "total_cost": sum(r["total_cost"] for r in recipes_list),
            "total_profit": sum(r["total_profit"] for r in recipes_list),
            "total_servings_produced": sum(r["total_produced"] for r in recipes_list),
            "total_servings_sold": sum(r["total_sold"] for r in recipes_list),
            "total_servings_wasted": sum(r["total_wasted"] for r in recipes_list)
        }
    }


@router.get("/supplier-performance")
async def get_supplier_performance(
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get supplier performance analytics"""
    org_id = current_user.get("organization_id")
    
    query = {}
    if current_user["role"] != "admin":
        if org_id:
            query["organization_id"] = org_id
        else:
            return {"suppliers": []}
    
    # Get all suppliers
    suppliers = await db.suppliers.find(query, {"_id": 0}).to_list(500)
    
    # Get orders by supplier
    orders = await db.purchase_orders.find(query, {"_id": 0}).to_list(10000)
    
    supplier_stats = {}
    for supplier in suppliers:
        supplier_stats[supplier["id"]] = {
            "supplier_id": supplier["id"],
            "name": supplier.get("name"),
            "rating": supplier.get("rating"),
            "lead_time_days": supplier.get("lead_time_days"),
            "total_orders": 0,
            "total_spent": 0,
            "on_time_deliveries": 0,
            "late_deliveries": 0
        }
    
    for order in orders:
        supplier_id = order.get("supplier_id")
        if supplier_id in supplier_stats:
            supplier_stats[supplier_id]["total_orders"] += 1
            supplier_stats[supplier_id]["total_spent"] += order.get("total", 0)
            
            # Check delivery timing
            if order.get("status") == "received":
                expected = order.get("expected_delivery_date")
                actual = order.get("actual_delivery_date")
                if expected and actual:
                    if actual <= expected:
                        supplier_stats[supplier_id]["on_time_deliveries"] += 1
                    else:
                        supplier_stats[supplier_id]["late_deliveries"] += 1
    
    # Calculate on-time rate
    for stats in supplier_stats.values():
        total_delivered = stats["on_time_deliveries"] + stats["late_deliveries"]
        if total_delivered > 0:
            stats["on_time_rate"] = round((stats["on_time_deliveries"] / total_delivered) * 100, 1)
        else:
            stats["on_time_rate"] = None
    
    return {
        "suppliers": sorted(supplier_stats.values(), key=lambda x: x["total_spent"], reverse=True)
    }


@router.get("/inventory-alerts")
async def get_inventory_alerts(
    kitchen_id: Optional[str] = None,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get inventory alerts (low stock, expiring)"""
    org_id = current_user.get("organization_id")
    
    query = {"is_active": True}
    if current_user["role"] != "admin":
        if org_id:
            query["organization_id"] = org_id
        else:
            return {"low_stock": [], "expiring_soon": []}
    
    if kitchen_id:
        query["kitchen_id"] = kitchen_id
    
    items = await db.inventory.find(query, {"_id": 0}).to_list(1000)
    
    # Get ingredient names
    ingredient_ids = list(set(item.get("ingredient_id") for item in items if item.get("ingredient_id")))
    ingredients = await db.ingredients.find({"id": {"$in": ingredient_ids}}, {"_id": 0}).to_list(500)
    ingredient_map = {i["id"]: i["name"] for i in ingredients}
    
    low_stock = []
    expiring_soon = []
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    week_later = (datetime.now(timezone.utc) + timedelta(days=7)).strftime("%Y-%m-%d")
    
    for item in items:
        item["ingredient_name"] = ingredient_map.get(item.get("ingredient_id"))
        
        # Check low stock
        if item.get("reorder_point") and item.get("quantity", 0) <= item["reorder_point"]:
            low_stock.append({
                "id": item["id"],
                "ingredient_name": item.get("ingredient_name"),
                "quantity": item.get("quantity"),
                "unit": item.get("unit"),
                "reorder_point": item.get("reorder_point"),
                "kitchen_id": item.get("kitchen_id")
            })
        
        # Check expiring
        expiry = item.get("expiry_date")
        if expiry and expiry <= week_later:
            expiring_soon.append({
                "id": item["id"],
                "ingredient_name": item.get("ingredient_name"),
                "quantity": item.get("quantity"),
                "unit": item.get("unit"),
                "expiry_date": expiry,
                "kitchen_id": item.get("kitchen_id"),
                "is_expired": expiry < today
            })
    
    return {
        "low_stock": low_stock,
        "expiring_soon": sorted(expiring_soon, key=lambda x: x["expiry_date"])
    }
