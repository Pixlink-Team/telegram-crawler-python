"""
Test configuration
"""
import pytest
import os


@pytest.fixture
def test_env():
    """Set up test environment"""
    os.environ["TELEGRAM_API_ID"] = "12345"
    os.environ["TELEGRAM_API_HASH"] = "test_hash"
    os.environ["API_SECRET_KEY"] = "test_key"
    os.environ["LARAVEL_BASE_URL"] = "http://localhost:8000"
    os.environ["WEBHOOK_SECRET_TOKEN"] = "test_token"
    yield
    # Cleanup if needed
