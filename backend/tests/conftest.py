import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


@pytest.fixture(scope="session")
def api_client():
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="session")
def auth_data(api_client):
    """Get admin auth token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@kitchen.com",
        "password": "Admin123!"
    })
    if response.status_code == 200:
        data = response.json()
        return data
    pytest.skip(f"Authentication failed — {response.status_code}: {response.text}")


@pytest.fixture(scope="session")
def auth_token(auth_data):
    return auth_data.get("access_token")


@pytest.fixture(scope="session")
def authenticated_client(api_client, auth_token):
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session


@pytest.fixture(scope="session")
def org_id(auth_data):
    """Get organization ID from user data"""
    user = auth_data.get("user", {})
    return user.get("organization_id")


@pytest.fixture(scope="session")
def kitchen_id(authenticated_client, org_id):
    """Get or create a kitchen for testing"""
    if not org_id:
        pytest.skip("No organization_id available")
    response = authenticated_client.get(f"{BASE_URL}/api/kitchens/")
    if response.status_code == 200 and response.json():
        return response.json()[0]["id"]
    pytest.skip("No kitchens available")
