"""
Basic test for API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "Telegram Service"


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_request_qr_without_api_key():
    """Test request QR without API key"""
    response = client.post(
        "/api/telegram/request-qr",
        json={"agent_id": 123}
    )
    assert response.status_code == 401


# Add more tests as needed
