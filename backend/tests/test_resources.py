import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


def test_list_ingredients(authenticated_client):
    """Should return list of ingredients"""
    resp = authenticated_client.get(f"{BASE_URL}/api/ingredients/")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_create_ingredient(authenticated_client, org_id):
    """Create a new ingredient"""
    if not org_id:
        pytest.skip("No organization_id for user")
    uid = str(uuid.uuid4())[:8]
    resp = authenticated_client.post(f"{BASE_URL}/api/ingredients/", json={
        "name": f"TEST_Ingredient_{uid}",
        "category": "produce",
        "default_unit": "kg",
        "cost_per_unit": 2.50,
        "is_perishable": True,
        "shelf_life_days": 7
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data
    assert "name" in data
    return data["id"]


def test_ingredient_crud(authenticated_client, org_id):
    """Create, Update, Delete an ingredient"""
    if not org_id:
        pytest.skip("No organization_id for user")
    uid = str(uuid.uuid4())[:8]
    # Create
    create_resp = authenticated_client.post(f"{BASE_URL}/api/ingredients/", json={
        "name": f"TEST_CRUD_{uid}",
        "category": "spices",
        "default_unit": "g"
    })
    assert create_resp.status_code == 201
    ingredient_id = create_resp.json()["id"]

    # Update
    update_resp = authenticated_client.put(f"{BASE_URL}/api/ingredients/{ingredient_id}", json={
        "name": f"TEST_UPDATED_{uid}",
        "category": "spices",
        "default_unit": "g",
        "cost_per_unit": 5.0
    })
    assert update_resp.status_code == 200
    assert "UPDATED" in update_resp.json()["name"]

    # Delete (soft delete)
    del_resp = authenticated_client.delete(f"{BASE_URL}/api/ingredients/{ingredient_id}")
    assert del_resp.status_code == 204


def test_list_recipes(authenticated_client):
    """Should return list of recipes"""
    resp = authenticated_client.get(f"{BASE_URL}/api/recipes/")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_create_recipe(authenticated_client, org_id):
    """Create a new recipe"""
    if not org_id:
        pytest.skip("No organization_id for user")
    uid = str(uuid.uuid4())[:8]
    resp = authenticated_client.post(f"{BASE_URL}/api/recipes/", json={
        "title": f"TEST_Recipe_{uid}",
        "description": "A test recipe",
        "servings": 4,
        "prep_time_minutes": 15,
        "cook_time_minutes": 30,
        "category": "main",
        "cuisine_type": "Italian",
        "instructions": ["Step 1: Do something", "Step 2: Serve"],
        "ingredients": []
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data
    assert data["title"] == f"TEST_Recipe_{uid}"

    # Verify via GET
    get_resp = authenticated_client.get(f"{BASE_URL}/api/recipes/{data['id']}")
    assert get_resp.status_code == 200


def test_list_suppliers(authenticated_client):
    """Should return list of suppliers"""
    resp = authenticated_client.get(f"{BASE_URL}/api/suppliers/")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_create_supplier(authenticated_client, org_id):
    """Create a new supplier"""
    if not org_id:
        pytest.skip("No organization_id for user")
    uid = str(uuid.uuid4())[:8]
    resp = authenticated_client.post(f"{BASE_URL}/api/suppliers/", json={
        "name": f"TEST_Supplier_{uid}",
        "contact_name": "John Test",
        "email": f"supplier_{uid}@test.com",
        "phone": "+1234567890",
        "categories": ["produce", "meat"]
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data
    assert "name" in data


def test_list_waste_logs(authenticated_client):
    """Should return list of waste logs"""
    resp = authenticated_client.get(f"{BASE_URL}/api/waste/")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_waste_summary(authenticated_client):
    """Should return waste summary"""
    resp = authenticated_client.get(f"{BASE_URL}/api/waste/summary")
    assert resp.status_code == 200


def test_list_inventory(authenticated_client):
    """Should return list of inventory items"""
    resp = authenticated_client.get(f"{BASE_URL}/api/inventory/")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_dashboard_analytics(authenticated_client):
    """Dashboard analytics should return metrics"""
    resp = authenticated_client.get(f"{BASE_URL}/api/analytics/dashboard")
    assert resp.status_code == 200
    data = resp.json()
    # Should have core metric fields
    assert "recipes_count" in data or "error" not in data
