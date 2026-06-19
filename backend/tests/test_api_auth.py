"""
Tests for authentication API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestAuthentication:
    """Authentication endpoint tests."""
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_user_registration(self):
        """Test user registration."""
        response = client.post("/api/v2/auth/register", json={
            "email": "test@example.com",
            "password": "SecurePass123!",
            "name": "Test User"
        })
        
        assert response.status_code == 201
        assert "id" in response.json()
