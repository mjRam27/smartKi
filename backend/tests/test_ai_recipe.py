import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


def test_ai_recipe_generation(authenticated_client, org_id):
    """Test AI recipe generation endpoint"""
    if not org_id:
        pytest.skip("No organization_id for user")
    resp = authenticated_client.post(f"{BASE_URL}/api/recipes/generate", json={
        "recipe_name": "Test Pasta Carbonara",
        "cuisine_type": "Italian",
        "serving_count": 4,
        "include_ingredients": ["pasta", "eggs"],
        "avoid_ingredients": []
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "success" in data
    if data.get("success"):
        assert "recipe" in data
        recipe = data["recipe"]
        assert "title" in recipe or "name" in recipe
        assert "ingredients" in recipe
        assert "instructions" in recipe
    else:
        # AI failure is possible, but endpoint should respond
        assert "error" in data or "recipe" in data
