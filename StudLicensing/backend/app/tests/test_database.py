# ===========================================
# Imports
# ===========================================
import os
import pytest
from unittest.mock import patch
import app.database

# =====================================================================
# Tests
# =====================================================================

def test_environment_variable_validation(monkeypatch):
    """
    Test that missing environment variables raise ValueError.
    """
    # Mock os.getenv to return None for required environment variables
    def mock_getenv(key, default=None):
        return None  # Simulate missing environment variables

    monkeypatch.setattr("os.getenv", mock_getenv)
    # Mock find_dotenv to return a path
    monkeypatch.setattr("dotenv.find_dotenv", lambda: ".env")
    
    # Reload database module to trigger validation
    with pytest.raises(ValueError) as exc_info:
        from importlib import reload
        reload(app.database)
    # Check for any of the expected environment variable error messages
    error_msg = str(exc_info.value)
    assert any(var in error_msg for var in [
        "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB", "POSTGRES_PORT"
    ]), f"Expected environment variable error, got: {error_msg}"

def test_database_url_construction(monkeypatch):
    """
    Test that SQLALCHEMY_DATABASE_URL is constructed correctly.
    """
    # Set mock environment variables
    monkeypatch.setenv("POSTGRES_USER", "testuser")
    monkeypatch.setenv("POSTGRES_PASSWORD", "testpass")
    monkeypatch.setenv("POSTGRES_DB", "testdb")
    monkeypatch.setenv("POSTGRES_PORT", "5432")
    monkeypatch.setattr("dotenv.find_dotenv", lambda: ".env")
    
    from importlib import reload
    reload(app.database)
    
    expected_url = "postgresql://testuser:testpass@db:5432/testdb"
    assert app.database.SQLALCHEMY_DATABASE_URL == expected_url

def test_engine_and_session_creation():
    """
    Test that engine and SessionLocal are created without errors.
    """
    assert app.database.engine is not None
    assert app.database.SessionLocal is not None
    assert app.database.Base is not None