import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


def test_health_check():
    """API health check should return healthy"""
    resp = requests.get(f"{BASE_URL}/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "Kitchen Intelligence Platform" in data["service"]


def test_login_success(api_client):
    """Login with valid credentials should return tokens"""
    resp = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@kitchen.com",
        "password": "Admin123!"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert "user" in data
    assert data["user"]["email"] == "admin@kitchen.com"


def test_login_invalid_credentials(api_client):
    """Login with wrong credentials should return 401"""
    resp = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@kitchen.com",
        "password": "wrongpassword"
    })
    assert resp.status_code == 401


def test_register_duplicate_email(api_client, auth_token):
    """Registering with existing email should fail with 400"""
    resp = api_client.post(f"{BASE_URL}/api/auth/register", json={
        "email": "admin@kitchen.com",
        "password": "Admin123!",
        "first_name": "Admin",
        "last_name": "User",
        "role": "chef"
    })
    assert resp.status_code == 400


def test_register_new_user(api_client):
    """Register new user should succeed"""
    uid = str(uuid.uuid4())[:8]
    resp = api_client.post(f"{BASE_URL}/api/auth/register", json={
        "email": f"test_{uid}@kitchen.com",
        "password": "Test123!",
        "first_name": "Test",
        "last_name": "User",
        "role": "chef"
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert "user" in data


def test_get_me(authenticated_client):
    """GET /auth/me should return current user info"""
    resp = authenticated_client.get(f"{BASE_URL}/api/auth/me")
    assert resp.status_code == 200
    data = resp.json()
    assert "email" in data
    assert data["email"] == "admin@kitchen.com"
    assert "id" in data
    assert "role" in data


def test_me_unauthenticated(api_client):
    """GET /auth/me without token should return 401 or 403"""
    resp = api_client.get(f"{BASE_URL}/api/auth/me")
    assert resp.status_code in [401, 403]
