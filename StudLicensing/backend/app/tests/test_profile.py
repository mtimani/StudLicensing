import io
import os
from datetime import datetime
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base
from app.profile import get_db
from app.profile import router as profile_router
from app.models import Users, UserPicture
from app.auth import get_current_user as original_get_current_user
from PIL import Image, ImageFile
from unittest.mock import patch

# =====================================================================
# Test Database Setup
# =====================================================================
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """
    Create all tables before tests and drop after.
    """
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture()
def db_session():
    """
    Creates a database session and wraps each test in a transaction for isolation.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()

# =====================================================================
# FastAPI Test Client
# =====================================================================
@pytest.fixture()
def client(db_session):
    """
    Provides a TestClient with overridden dependencies for db and auth.
    """
    app = FastAPI()
    app.include_router(profile_router)
    # Override the get_db dependency
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    # Override get_current_user dependency to simulate an authenticated user
    def override_current_user():
        """
        By default refer to a user with ID 1.
        """
        return {"username": "test@example.com", "id": 1, "type": "basic", "jti": "testjti"}
    app.dependency_overrides[original_get_current_user] = override_current_user
    return TestClient(app)

# =====================================================================
# Test Data Fixtures
# =====================================================================
@pytest.fixture()
def test_user(db_session):
    """
    Inserts a basic activated user for authentication.
    """
    user = Users(
        username="test@example.com",
        name="Test",
        surname="User",
        hashedPassword="",
        creationDate=datetime.utcnow(),
        activated=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

# =====================================================================
# Helper Functions
# =====================================================================
def generate_png_bytes(width=10, height=10):
    """
    Create in-memory PNG bytes for testing image uploads.
    """
    buffer = io.BytesIO()
    image = Image.new('RGB', (width, height), color=(73, 109, 137))
    image.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer

def generate_jpeg_bytes(width=10, height=10):
    """
    Create in-memory JPEG bytes for testing image uploads.
    """
    buffer = io.BytesIO()
    image = Image.new('RGB', (width, height), color=(73, 109, 137))
    image.save(buffer, format='JPEG')
    buffer.seek(0)
    return buffer

def generate_gif_bytes(width=10, height=10):
    """
    Create in-memory GIF bytes for testing unsupported image formats.
    """
    buffer = io.BytesIO()
    image = Image.new('RGB', (width, height), color=(73, 109, 137))
    image.save(buffer, format='GIF')
    buffer.seek(0)
    return buffer

def generate_large_png_bytes(size_mb_target=6):
    """
    Create a large in-memory PNG file for testing file size limits.
    Approximate size in MB by adjusting dimensions (rough estimation).
    """
    # Rough calculation: 6000x6000 RGB image to try exceeding 5MB even after compression
    width = 6000
    height = 6000
    buffer = io.BytesIO()
    image = Image.new('RGB', (width, height), color=(73, 109, 137))
    image.save(buffer, format='PNG', quality=100)  # Maximize quality to increase size
    buffer.seek(0)
    # Print actual size for debugging
    actual_size_mb = len(buffer.getvalue()) / (1024 * 1024)
    print(f"Generated large PNG size: {actual_size_mb:.2f} MB")
    return buffer

# =====================================================================
# Happy Path Tests
# =====================================================================
def test_get_profile_info(client, test_user):
    response = client.get("/profile/info")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == test_user.username
    assert data["name"] == test_user.name
    assert data["surname"] == test_user.surname

def test_update_profile_info(client, test_user):
    payload = {"name": "NewName", "surname": "NewSurname"}
    response = client.put("/profile/info", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["detail"] == "Profile updated successfully"
    assert data["user"]["name"] == "NewName"
    assert data["user"]["surname"] == "NewSurname"

def test_profile_picture_upload_and_get(client, test_user):
    img_bytes = generate_png_bytes()
    files = {"new_picture": ("test.png", img_bytes, "image/png")}
    put_resp = client.put("/profile/picture", files=files)
    assert put_resp.status_code == 200
    assert put_resp.json()["detail"] == "Profile picture updated successfully."
    get_resp = client.get("/profile/picture")
    assert get_resp.status_code == 200
    assert get_resp.content.startswith(b"\x89PNG\r\n\x1a\n")
    assert get_resp.headers["content-type"] == "image/png"

# =====================================================================
# Edge Case Tests
# =====================================================================
def test_get_profile_info_user_not_found(client, db_session):
    # Remove all users
    db_session.query(Users).delete()
    db_session.commit()
    # Override auth to non-existent user
    client.app.dependency_overrides[original_get_current_user] = lambda: {"username": "x", "id": 999, "type": "basic", "jti": "t"}
    resp = client.get("/profile/info")
    assert resp.status_code == 403
    assert resp.json()["detail"] == "User not found"

def test_update_profile_info_partial_name_only(client, test_user):
    # Update only name
    payload = {"name": "SoloName"}
    resp = client.put("/profile/info", json=payload)
    assert resp.status_code == 200
    data = resp.json()["user"]
    assert data["name"] == "SoloName"
    assert data["surname"] == test_user.surname  # surname unchanged

def test_update_profile_info_validation_error_long_string(client):
    # Name too long (>50 chars)
    long_name = "n" * 51
    resp = client.put("/profile/info", json={"name": long_name})
    assert resp.status_code == 422  # Pydantic validation error

def test_update_profile_info_validation_error_empty_string(client):
    # Name empty string (violates min_length=1)
    resp = client.put("/profile/info", json={"name": ""})
    assert resp.status_code == 422  # Pydantic validation error

def test_get_profile_picture_no_picture(client, test_user):
    resp = client.get("/profile/picture")
    assert resp.status_code == 403
    assert resp.json()["detail"] == "No profile picture found."

def test_update_profile_picture_invalid_extension(client, test_user):
    # Create a valid PNG but with .exe extension
    img_bytes = generate_png_bytes()
    files = {"new_picture": ("test.exe", img_bytes, "application/octet-stream")}
    resp = client.put("/profile/picture", files=files)
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Uploaded file is not a valid image."

def test_update_profile_picture_corrupted_image(client, test_user):
    # Use text data with .png extension
    fake = io.BytesIO(b"not an image")
    files = {"new_picture": ("fake.png", fake, "image/png")}
    resp = client.put("/profile/picture", files=files)
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Uploaded file is not a valid image."

def test_update_profile_picture_missing_content_type(client, test_user):
    # Omitting content_type => None
    img_bytes = generate_png_bytes()
    # Only filename and fileobj provided
    files = {"new_picture": ("test.png", img_bytes)}
    resp = client.put("/profile/picture", files=files)
    # Should fallback to extension-based mime and succeed
    assert resp.status_code == 200
    assert resp.json()["detail"] == "Profile picture updated successfully."

def test_update_profile_picture_unsupported_format_gif(client, test_user):
    # Use a GIF image (unsupported format but valid image)
    img_bytes = generate_gif_bytes()
    files = {"new_picture": ("test.gif", img_bytes, "image/gif")}
    resp = client.put("/profile/picture", files=files)
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Uploaded file is not a valid image."

def test_update_profile_picture_large_file(client, test_user, monkeypatch):
    # Test uploading a very large file (approximating >5MB, should fail due to size limit)
    large_img_bytes = generate_large_png_bytes()
    
    # Since generating a truly large file might be unreliable due to compression,
    # mock the file size check by patching the profile.py module's MAX_UPLOAD_SIZE_BYTES
    # to a very low value (e.g., 1KB) to simulate exceeding the limit with a small file
    monkeypatch.setattr("app.profile.MAX_UPLOAD_SIZE_BYTES", 1024)  # 1KB, much smaller than any generated file
    monkeypatch.setattr("app.profile.MAX_UPLOAD_SIZE_MB", 0.001)  # For error message consistency
    
    files = {"new_picture": ("large.png", large_img_bytes, "image/png")}
    resp = client.put("/profile/picture", files=files)
    assert resp.status_code == 403
    assert "Uploaded file size exceeds maximum limit of 0.001 MB" in resp.json()["detail"]

def test_get_profile_picture_corrupted_data(client, test_user, monkeypatch):
    # Test retrieval when picture data is corrupted or inaccessible
    img_bytes = generate_png_bytes()
    files = {"new_picture": ("test.png", img_bytes, "image/png")}
    put_resp = client.put("/profile/picture", files=files)
    assert put_resp.status_code == 200

    # Mock store.open to simulate file access failure
    def mock_store_open(*args, **kwargs):
        raise OSError("Cannot access file")

    # Patch the store.open method to raise OSError
    with monkeypatch.context() as m:
        m.setattr("sqlalchemy_imageattach.stores.fs.FileSystemStore.open", mock_store_open)
        get_resp = client.get("/profile/picture")
        assert get_resp.status_code == 500
        assert "Unable to retrieve profile picture due to server error" in get_resp.json()["detail"]