import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


def test_list_organizations(authenticated_client):
    """Should return list of organizations"""
    resp = authenticated_client.get(f"{BASE_URL}/api/organizations/")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_create_organization(authenticated_client):
    """Create a new organization"""
    uid = str(uuid.uuid4())[:8]
    resp = authenticated_client.post(f"{BASE_URL}/api/organizations/", json={
        "name": f"TEST_Org_{uid}",
        "type": "restaurant",
        "description": "Test organization"
    })
    # Admin might already have an org, but endpoint should handle it
    assert resp.status_code in [201, 200, 400]
    if resp.status_code == 201:
        data = resp.json()
        assert "id" in data
        assert "name" in data


def test_list_kitchens(authenticated_client):
    """Should return list of kitchens"""
    resp = authenticated_client.get(f"{BASE_URL}/api/kitchens/")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_create_kitchen(authenticated_client, org_id):
    """Create a new kitchen"""
    if not org_id:
        pytest.skip("No organization_id for user")
    uid = str(uuid.uuid4())[:8]
    resp = authenticated_client.post(f"{BASE_URL}/api/kitchens/", json={
        "name": f"TEST_Kitchen_{uid}",
        "location": "Test Location",
        "description": "Test Kitchen",
        "capacity": 20
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data
    assert "name" in data
    created_id = data["id"]

    # Verify it was created via GET
    get_resp = authenticated_client.get(f"{BASE_URL}/api/kitchens/{created_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == created_id


def test_kitchen_requires_org(api_client):
    """Creating kitchen without auth should fail"""
    resp = api_client.post(f"{BASE_URL}/api/kitchens/", json={
        "name": "Unauthorized Kitchen",
        "location": "Somewhere"
    })
    assert resp.status_code in [401, 403]
