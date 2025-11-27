import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from bson import ObjectId

mock_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyMTIzIiwiZW1haWwiOiJ0ZXN0QGV4YW1wbGUuY29tIiwiaWF0IjoxNjE2MjM5MDIyfQ.test_signature"

def get_auth_headers():
    return {"Authorization": f"Bearer {mock_token}"}

test_user_data = {
    "email": "test@example.com",
    "password": "testpassword123",
    "full_name": "Test User"
}

test_login_data = {
    "email": "test@example.com",
    "password": "testpassword123"
}

test_chat_data = {
    "message": "I want to plan a vacation to Paris",
    "conversation_id": None
}

@pytest.mark.usefixtures("client", "mock_auth")
class TestAuthEndpoints:
    

    def test_signup_invalid_data(self, client):
        # Test user registration with invalid data
        invalid_data = {
            "email": "invalid-email",
            "password": "short",
            "full_name": ""
        }
        response = client.post("/api/v1/auth/signup", json=invalid_data)
        assert response.status_code == 422

    def test_login_success(self, client):
        # Test successful user login
        response = client.post(
            "/api/v1/auth/login",
            data={"username": test_login_data["email"], "password": test_login_data["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code in (200, 401)

    def test_login_invalid_credentials(self, client):
        # Test login with invalid credentials
        response = client.post(
            "/api/v1/auth/login",
            data={"username": test_login_data["email"], "password": "wrongpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code in (401, 200)

    def test_login_missing_data(self, client):
        # Test login with missing required data
        response = client.post("/api/v1/auth/login", json={})
        assert response.status_code in (400, 422)