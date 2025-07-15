# test_admin.py
# ===========================================
# Imports
# ===========================================
import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base
from app.models import Company, Users, UserTypeEnum, CompanyAdmin, CompanyClient, CompanyCommercial, CompanyDevelopper, Admin, SessionTokens
from app.admin import router, get_db
from app.auth import get_current_user
from fastapi import FastAPI
from datetime import datetime, timedelta
import os
import tempfile
from PIL import Image
import io

# ===========================================
# Test App Setup
# ===========================================
# Create a test app with the admin router
app = FastAPI()
app.include_router(router)

# ===========================================
# Database Fixtures
# ===========================================
@pytest.fixture(scope="session", autouse=True)
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=eng)
    yield eng
    Base.metadata.drop_all(bind=eng)

@pytest.fixture(scope="function")
def db_session(engine):
    """
    Create a new database session for each test and roll back changes after.
    Additionally, clear all relevant tables before each test to ensure isolation.
    """
    SessionTest = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionTest()
    # Clear all relevant tables before the test to ensure a clean state
    for table in [Users, Company, CompanyAdmin, CompanyClient, CompanyCommercial, CompanyDevelopper, Admin, SessionTokens]:
        session.query(table).delete()
    session.commit()
    yield session
    session.rollback()
    session.close()

@pytest.fixture(scope="function")
def client(db_session):
    """
    Create a TestClient with overridden dependencies for testing.
    """
    def override_get_db():
        yield db_session
    # Override the get_db dependency directly
    app.dependency_overrides[get_db] = override_get_db
    # Override get_current_user to return a default admin user for all tests
    def override_get_current_user():
        return {"id": 1, "type": UserTypeEnum.admin, "name": "Admin", "username": "admin@example.com", "jti": "mock_jti"}
    # Apply the override for get_current_user at the app level
    app.dependency_overrides[get_current_user] = override_get_current_user
    return TestClient(app)

@pytest.fixture(scope="function")
def tmp_file():
    """Fixture to create a temporary file for testing file uploads."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        yield f.name
    os.unlink(f.name)

# ===========================================
# Helper Functions
# ===========================================
def create_test_company(db_session, name="TestCo"):
    """Helper to create a company in the database for testing."""
    company = Company(companyName=name)
    db_session.add(company)
    db_session.commit()
    db_session.refresh(company)
    return company

def create_test_user(db_session, user_type=UserTypeEnum.admin, company_id=None, username=None):
    """Helper to create a user in the database for testing."""
    unique_username = username if username else f"test_user_{uuid.uuid4().hex}@example.com"
    if user_type == UserTypeEnum.company_admin:
        user = CompanyAdmin(
            username=unique_username,
            name="Test",
            surname="User",
            hashedPassword="hashed_pass",
            creationDate=datetime.utcnow(),
            activated=True,
            company_id=company_id
        )
    elif user_type == UserTypeEnum.company_client:
        user = CompanyClient(
            username=unique_username,
            name="Test",
            surname="User",
            hashedPassword="hashed_pass",
            creationDate=datetime.utcnow(),
            activated=True
        )
    elif user_type == UserTypeEnum.company_commercial:
        user = CompanyCommercial(
            username=unique_username,
            name="Test",
            surname="User",
            hashedPassword="hashed_pass",
            creationDate=datetime.utcnow(),
            activated=True,
            company_id=company_id
        )
    elif user_type == UserTypeEnum.company_developper:
        user = CompanyDevelopper(
            username=unique_username,
            name="Test",
            surname="User",
            hashedPassword="hashed_pass",
            creationDate=datetime.utcnow(),
            activated=True,
            company_id=company_id
        )
    else:
        user = Admin(
            username=unique_username,
            name="Test",
            surname="User",
            hashedPassword="hashed_pass",
            creationDate=datetime.utcnow(),
            activated=True
        )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    # Associate company with CompanyClient only if company_id is explicitly provided
    if user_type == UserTypeEnum.company_client and company_id is not None:
        company = db_session.query(Company).filter(Company.id == company_id).first()
        if company and company not in getattr(user, 'companies', []):
            user.companies.append(company)
            db_session.commit()
            db_session.refresh(user)
    return user

def override_user_type(client, user_type, user_id=1, username="test_user@example.com"):
    """Helper to override get_current_user for a specific test with a custom user type."""
    def custom_get_current_user():
        return {"id": user_id, "type": user_type, "name": "Test", "username": username, "jti": "mock_jti"}
    app.dependency_overrides[get_current_user] = custom_get_current_user
    return client

def create_test_image(tmp_file, format="JPEG", size=(100, 100)):
    """Helper to create a test image file for profile picture uploads."""
    img = Image.new("RGB", size, color="red")
    img.save(tmp_file, format=format)
    return tmp_file

# ===========================================
# Tests for /admin/account_create Endpoint
# ===========================================
def test_create_user_as_admin_success(client, db_session):
    """Test creating a user as an admin with valid data (company must be specified)."""
    company = create_test_company(db_session)
    response = client.post(
        "/admin/account_create",
        data={
            "username": "newuser@example.com",
            "name": "New",
            "surname": "User",
            "user_type": UserTypeEnum.company_admin.value,
            "company_id": company.id
        }
    )
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    assert response.json()["username"] == "newuser@example.com"

def test_create_user_as_admin_no_company_id_for_non_admin(client, db_session):
    """Test creating a non-admin user without company_id as admin (should fail)."""
    response = client.post(
        "/admin/account_create",
        data={
            "username": "newuser@example.com",
            "name": "New",
            "surname": "User",
            "user_type": UserTypeEnum.company_admin.value
        }
    )
    assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
    assert response.json()["detail"] == "Account creation forbidden."

def test_create_user_as_admin_invalid_company_id(client, db_session):
    """Test creating a user with invalid company_id as admin (should fail)."""
    response = client.post(
        "/admin/account_create",
        data={
            "username": "newuser@example.com",
            "name": "New",
            "surname": "User",
            "user_type": UserTypeEnum.company_admin.value,
            "company_id": 9999
        }
    )
    assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
    assert response.json()["detail"] == "Account creation forbidden."

def test_create_user_as_non_admin_with_company_id(client, db_session):
    """Test creating a user with company_id as non-admin (should fail)."""
    client = override_user_type(client, UserTypeEnum.company_admin)
    company = create_test_company(db_session)
    response = client.post(
        "/admin/account_create",
        data={
            "username": "newuser@example.com",
            "name": "New",
            "surname": "User",
            "user_type": UserTypeEnum.company_client.value,
            "company_id": company.id
        }
    )
    assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
    assert response.json()["detail"] == "Account creation forbidden."

def test_create_user_as_company_admin_success(client, db_session):
    """Test creating a company client as company admin (should succeed with inherited company)."""
    company = create_test_company(db_session)
    user = create_test_user(db_session, user_type=UserTypeEnum.company_admin, company_id=company.id)
    client = override_user_type(client, UserTypeEnum.company_admin, user_id=user.id, username=user.username)
    unique_username = f"newclient_{uuid.uuid4().hex}@example.com"
    response = client.post(
        "/admin/account_create",
        data={
            "username": unique_username,
            "name": "New",
            "surname": "Client",
            "user_type": UserTypeEnum.company_client.value
        }
    )
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    assert response.json()["username"] == unique_username

def test_create_user_as_company_commercial_success(client, db_session):
    """Test creating a company client as company commercial (should succeed with inherited company)."""
    company = create_test_company(db_session)
    user = create_test_user(db_session, user_type=UserTypeEnum.company_commercial, company_id=company.id)
    client = override_user_type(client, UserTypeEnum.company_commercial, user_id=user.id, username=user.username)
    unique_username = f"newclient_{uuid.uuid4().hex}@example.com"
    response = client.post(
        "/admin/account_create",
        data={
            "username": unique_username,
            "name": "New",
            "surname": "Client",
            "user_type": UserTypeEnum.company_client.value
        }
    )
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    assert response.json()["username"] == unique_username

def test_create_user_as_company_developper_success(client, db_session):
    """Test creating a company client as company developper (should succeed with inherited company)."""
    company = create_test_company(db_session)
    user = create_test_user(db_session, user_type=UserTypeEnum.company_developper, company_id=company.id)
    client = override_user_type(client, UserTypeEnum.company_developper, user_id=user.id, username=user.username)
    unique_username = f"newclient_{uuid.uuid4().hex}@example.com"
    response = client.post(
        "/admin/account_create",
        data={
            "username": unique_username,
            "name": "New",
            "surname": "Client",
            "user_type": UserTypeEnum.company_client.value
        }
    )
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    assert response.json()["username"] == unique_username

def test_create_basic_user_forbidden(client, db_session):
    """Test creating a basic user (should fail)."""
    response = client.post(
        "/admin/account_create",
        data={
            "username": "basicuser@example.com",
            "name": "Basic",
            "surname": "User",
            "user_type": UserTypeEnum.basic.value
        }
    )
    assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
    assert response.json()["detail"] == "Account creation forbidden."

def test_create_user_duplicate_email(client, db_session):
    """Test creating a user with duplicate email (should fail)."""
    company = create_test_company(db_session)
    user = create_test_user(db_session, user_type=UserTypeEnum.admin)
    response = client.post(
        "/admin/account_create",
        data={
            "username": user.username,
            "name": "New",
            "surname": "User",
            "user_type": UserTypeEnum.company_admin.value,
            "company_id": company.id
        }
    )
    assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
    assert response.json()["detail"] == "Account creation forbidden."

def test_create_user_with_profile_picture_valid(client, db_session, tmp_file):
    """Test creating a user with a valid profile picture."""
    company = create_test_company(db_session)
    create_test_image(tmp_file, format="JPEG")
    with open(tmp_file, "rb") as f:
        response = client.post(
            "/admin/account_create",
            data={
                "username": "userwithpic@example.com",
                "name": "User",
                "surname": "WithPic",
                "user_type": UserTypeEnum.company_admin.value,
                "company_id": company.id
            },
            files={"profilePicture": ("test_image.jpg", f, "image/jpeg")}
        )
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    assert response.json()["username"] == "userwithpic@example.com"

def test_create_user_with_profile_picture_invalid_format(client, db_session, tmp_file):
    """Test creating a user with an invalid profile picture format (should fail)."""
    company = create_test_company(db_session)
    with open(tmp_file, "wb") as f:
        f.write(b"not an image")
    with open(tmp_file, "rb") as f:
        response = client.post(
            "/admin/account_create",
            data={
                "username": "userwithpic@example.com",
                "name": "User",
                "surname": "WithPic",
                "user_type": UserTypeEnum.company_admin.value,
                "company_id": company.id
            },
            files={"profilePicture": ("test_file.txt", f, "text/plain")}
        )
    assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
    assert "not a valid image" in response.json()["detail"].lower()

def test_create_user_with_profile_picture_large_file(client, db_session, tmp_file):
    """Test creating a user with a very large profile picture (should fail if size limit exists)."""
    company = create_test_company(db_session)
    # Create a large image (e.g., 10MB)
    large_data = b"0" * (10 * 1024 * 1024)  # 10MB of data
    with open(tmp_file, "wb") as f:
        f.write(large_data)
    with open(tmp_file, "rb") as f:
        response = client.post(
            "/admin/account_create",
            data={
                "username": "userwithlargepic@example.com",
                "name": "User",
                "surname": "WithLargePic",
                "user_type": UserTypeEnum.company_admin.value,
                "company_id": company.id
            },
            files={"profilePicture": ("large_image.jpg", f, "image/jpeg")}
        )
    assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"

def test_create_user_with_invalid_email_format(client, db_session):
    """Test creating a user with an invalid email format (should fail)."""
    company = create_test_company(db_session)
    response = client.post(
        "/admin/account_create",
        data={
            "username": "invalid-email",
            "name": "Invalid",
            "surname": "Email",
            "user_type": UserTypeEnum.company_admin.value,
            "company_id": company.id
        }
    )
    assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.text}"

def test_create_admin_with_company_id_forbidden(client, db_session):
    """Test creating an admin user with a company ID (should fail)."""
    company = create_test_company(db_session)
    response = client.post(
        "/admin/account_create",
        data={
            "username": "adminuser@example.com",
            "name": "Admin",
            "surname": "User",
            "user_type": UserTypeEnum.admin.value,
            "company_id": company.id
        }
    )
    assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
    assert response.json()["detail"] == "Account creation forbidden."

def test_create_user_with_boundary_name_surname(client, db_session):
    """Test creating a user with boundary values for name and surname (min/max length)."""
    company = create_test_company(db_session)
    response = client.post(
        "/admin/account_create",
        data={
            "username": "boundary@example.com",
            "name": "A",  # Minimum length
            "surname": "B" * 50,  # Maximum length as per Form validation
            "user_type": UserTypeEnum.company_admin.value,
            "company_id": company.id
        }
    )
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    assert response.json()["username"] == "boundary@example.com"

def test_create_user_with_special_characters(client, db_session):
    """Test creating a user with special characters in name and surname."""
    company = create_test_company(db_session)
    response = client.post(
        "/admin/account_create",
        data={
            "username": "specialchar@example.com",
            "name": "Test@#$%",
            "surname": "User&*()",
            "user_type": UserTypeEnum.company_admin.value,
            "company_id": company.id
        }
    )
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    assert response.json()["username"] == "specialchar@example.com"

def test_create_user_with_very_long_email(client, db_session):
    """Test creating a user with a very long email (should fail if length validation exists)."""
    company = create_test_company(db_session)
    long_email = f"{'a' * 200}@example.com"  # Very long email
    response = client.post(
        "/admin/account_create",
        data={
            "username": long_email,
            "name": "Long",
            "surname": "Email",
            "user_type": UserTypeEnum.company_admin.value,
            "company_id": company.id
        }
    )
    assert response.status_code in [422, 403], f"Expected 422 or 403, got {response.status_code}: {response.text}"

def test_create_existing_company_client_add_company(client, db_session):
    """Test adding an existing company client to a new company (should update associations)."""
    company1 = create_test_company(db_session, name="Company1")
    company2 = create_test_company(db_session, name="Company2")
    user = create_test_user(db_session, user_type=UserTypeEnum.company_client, company_id=company1.id)
    admin_user = create_test_user(db_session, user_type=UserTypeEnum.admin)
    client = override_user_type(client, UserTypeEnum.admin, user_id=admin_user.id, username=admin_user.username)
    print(f"Debug: Admin user ID={admin_user.id}, Username={admin_user.username}")
    response = client.post(
        "/admin/account_create",
        data={
            "username": user.username,
            "name": user.name,
            "surname": user.surname,
            "user_type": UserTypeEnum.company_client.value,
            "company_id": company2.id
        }
    )
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    assert "updated successfully" in response.json()["detail"].lower()
    db_session.refresh(user)
    assert len(user.companies) == 2, "User should be associated with both companies"

def test_create_user_with_empty_profile_picture(client, db_session, tmp_file):
    """Test creating a user with an empty profile picture file (should fail)."""
    company = create_test_company(db_session)
    with open(tmp_file, "wb") as f:
        f.write(b"")  # Empty file
    with open(tmp_file, "rb") as f:
        response = client.post(
            "/admin/account_create",
            data={
                "username": "userwithemptypic@example.com",
                "name": "User",
                "surname": "EmptyPic",
                "user_type": UserTypeEnum.company_admin.value,
                "company_id": company.id
            },
            files={"profilePicture": ("empty.jpg", f, "image/jpeg")}
        )
    assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
    assert "not a valid image" in response.json()["detail"].lower()

def test_create_user_with_special_email_characters(client, db_session):
    """Test creating a user with special characters in email (should succeed if validation allows)."""
    company = create_test_company(db_session)
    response = client.post(
        "/admin/account_create",
        data={
            "username": "user+test@example.com",
            "name": "Special",
            "surname": "Email",
            "user_type": UserTypeEnum.company_admin.value,
            "company_id": company.id
        }
    )
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    assert response.json()["username"] == "user+test@example.com"

def test_create_user_with_allowed_extension_invalid_content(client, db_session, tmp_file):
    """Test creating a user with a file having allowed extension but invalid content (should fail)."""
    company = create_test_company(db_session)
    with open(tmp_file, "wb") as f:
        f.write(b"This is not an image file")  # Invalid content for an image
    with open(tmp_file, "rb") as f:
        response = client.post(
            "/admin/account_create",
            data={
                "username": "userwithinvalidcontent@example.com",
                "name": "User",
                "surname": "InvalidContent",
                "user_type": UserTypeEnum.company_admin.value,
                "company_id": company.id
            },
            files={"profilePicture": ("fake_image.jpg", f, "image/jpeg")}
        )
    assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
    assert "not a valid image" in response.json()["detail"].lower()

def test_create_user_with_unusual_dimensions(client, db_session, tmp_file):
    """Test creating a user with an image having unusual dimensions (should succeed if no dimension limit)."""
    company = create_test_company(db_session)
    create_test_image(tmp_file, format="JPEG", size=(1, 10000))  # Extremely tall image
    with open(tmp_file, "rb") as f:
        response = client.post(
            "/admin/account_create",
            data={
                "username": "userwithunusualdim@example.com",
                "name": "User",
                "surname": "UnusualDim",
                "user_type": UserTypeEnum.company_admin.value,
                "company_id": company.id
            },
            files={"profilePicture": ("tall_image.jpg", f, "image/jpeg")}
        )
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    assert response.json()["username"] == "userwithunusualdim@example.com"

def test_create_user_with_long_domain_email(client, db_session):
    """Test creating a user with a very long domain name in email (should succeed if validation allows)."""
    company = create_test_company(db_session)
    long_domain_email = f"user@{'subdomain.' * 5}example.com"  # Very long domain with multiple subdomains
    response = client.post(
        "/admin/account_create",
        data={
            "username": long_domain_email,
            "name": "Long",
            "surname": "Domain",
            "user_type": UserTypeEnum.company_admin.value,
            "company_id": company.id
        }
    )
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    assert response.json()["username"] == long_domain_email

# ===========================================
# Tests for /admin/delete_user Endpoint
# ===========================================
def test_delete_user_as_admin_success(client, db_session):
    """Test deleting a user as admin (should succeed)."""
    user = create_test_user(db_session, user_type=UserTypeEnum.company_admin)
    # Ensure current_user ID is different from the user being deleted
    client = override_user_type(client, UserTypeEnum.admin, user_id=999, username="admin@example.com")
    response = client.post(
        "/admin/delete_user",
        data={"username": user.username, "confirm_username": user.username}
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    assert response.json()["detail"] == "Account deleted successfully."

def test_delete_user_as_company_admin_same_company(client, db_session):
    """Test deleting a user as company admin from same company (should succeed)."""
    company = create_test_company(db_session)
    admin_user = create_test_user(db_session, user_type=UserTypeEnum.company_admin, company_id=company.id)
    client_user = create_test_user(db_session, user_type=UserTypeEnum.company_client, company_id=company.id)
    client = override_user_type(client, UserTypeEnum.company_admin, user_id=admin_user.id, username=admin_user.username)
    response = client.post(
        "/admin/delete_user",
        data={"username": client_user.username, "confirm_username": client_user.username}
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    assert response.json()["detail"] == "Account deleted successfully."

def test_delete_user_as_company_admin_different_company(client, db_session):
    """Test deleting a user as company admin from different company (should fail)."""
    company1 = create_test_company(db_session, name="Company1")
    company2 = create_test_company(db_session, name="Company2")
    admin_user = create_test_user(db_session, user_type=UserTypeEnum.company_admin, company_id=company1.id)
    client_user = create_test_user(db_session, user_type=UserTypeEnum.company_client, company_id=company2.id)
    client = override_user_type(client, UserTypeEnum.company_admin, user_id=admin_user.id, username=admin_user.username)
    response = client.post(
        "/admin/delete_user",
        data={"username": client_user.username, "confirm_username": client_user.username}
    )
    assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
    assert response.json()["detail"] == "Delete user account forbidden."

def test_delete_user_mismatch_username(client, db_session):
    """Test deleting a user with mismatched username and confirm_username (should fail)."""
    user = create_test_user(db_session, user_type=UserTypeEnum.company_admin)
    response = client.post(
        "/admin/delete_user",
        data={"username": user.username, "confirm_username": "wrong@example.com"}
    )
    assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"

def test_delete_nonexistent_user(client, db_session):
    """Test deleting a nonexistent user (should fail)."""
    response = client.post(
        "/admin/delete_user",
        data={"username": "nonexistent@example.com", "confirm_username": "nonexistent@example.com"}
    )
    assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
    assert response.json()["detail"] == "Delete user account forbidden."

def test_delete_user_self_as_admin(client, db_session):
    """Test deleting self as admin (should fail as per current policy)."""
    user = create_test_user(db_session, user_type=UserTypeEnum.admin)
    client = override_user_type(client, UserTypeEnum.admin, user_id=user.id, username=user.username)
    response = client.post(
        "/admin/delete_user",
        data={"username": user.username, "confirm_username": user.username}
    )
    assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
    assert response.json()["detail"] == "Delete user account forbidden."

def test_delete_user_with_multiple_companies_partial(client, db_session):
    """Test deleting a company client with multiple companies as company admin (should remove from company only)."""
    company1 = create_test_company(db_session, name="Company1")
    company2 = create_test_company(db_session, name="Company2")
    admin_user = create_test_user(db_session, user_type=UserTypeEnum.company_admin, company_id=company1.id)
    client_user = create_test_user(db_session, user_type=UserTypeEnum.company_client, company_id=company1.id)
    if company2 not in client_user.companies:
        client_user.companies.append(company2)
        db_session.commit()
    client = override_user_type(client, UserTypeEnum.company_admin, user_id=admin_user.id, username=admin_user.username)
    response = client.post(
        "/admin/delete_user",
        data={"username": client_user.username, "confirm_username": client_user.username}
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    db_session.refresh(client_user)
    assert len(client_user.companies) == 1, "User should remain associated with one company"
    assert company2 in client_user.companies, "User should remain associated with the other company"

def test_delete_user_with_active_tokens(client, db_session):
    """Test deleting a user with active session tokens (should clean up tokens)."""
    user = create_test_user(db_session, user_type=UserTypeEnum.company_admin)
    token = SessionTokens(
        jti="test_jti",
        user_id=user.id,
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=1),
        is_active=True
    )
    db_session.add(token)
    db_session.commit()
    # Ensure current_user ID is different from the user being deleted
    client = override_user_type(client, UserTypeEnum.admin, user_id=999, username="admin@example.com")
    response = client.post(
        "/admin/delete_user",
        data={"username": user.username, "confirm_username": user.username}
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    assert db_session.query(SessionTokens).filter_by(user_id=user.id).first() is None, "Tokens should be deleted"

def test_delete_user_self_as_non_admin(client, db_session):
    """Test deleting self as non-admin (should succeed as per current policy)."""
    company = create_test_company(db_session)
    user = create_test_user(db_session, user_type=UserTypeEnum.company_admin, company_id=company.id)
    client = override_user_type(client, UserTypeEnum.company_admin, user_id=user.id, username=user.username)
    response = client.post(
        "/admin/delete_user",
        data={"username": user.username, "confirm_username": user.username}
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    assert response.json()["detail"] == "Account deleted successfully."

# ===========================================
# Tests for /admin/update_username Endpoint
# ===========================================
def test_update_username_as_admin_success(client, db_session):
    """Test updating username as admin (should succeed)."""
    user = create_test_user(db_session, user_type=UserTypeEnum.company_admin)
    response = client.post(
        "/admin/update_username",
        data={
            "old_username": user.username,
            "new_username": "updated@example.com",
            "confirm_new_username": "updated@example.com"
        }
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    assert response.json()["detail"] == "Username updated successfully"
    assert response.json()["user"]["username"] == "updated@example.com"

def test_update_username_mismatch_new_username(client, db_session):
    """Test updating username with mismatched new_username and confirm_new_username (should fail)."""
    user = create_test_user(db_session, user_type=UserTypeEnum.company_admin)
    response = client.post(
        "/admin/update_username",
        data={
            "old_username": user.username,
            "new_username": "updated@example.com",
            "confirm_new_username": "wrong@example.com"
        }
    )
    assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"

def test_update_username_same_as_old(client, db_session):
    """Test updating username to the same value as old_username (should fail)."""
    user = create_test_user(db_session, user_type=UserTypeEnum.company_admin)
    response = client.post(
        "/admin/update_username",
        data={
            "old_username": user.username,
            "new_username": user.username,
            "confirm_new_username": user.username
        }
    )
    assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"

def test_update_username_duplicate_email(client, db_session):
    """Test updating username to an existing email (should fail)."""
    user1 = create_test_user(db_session, user_type=UserTypeEnum.company_admin)
    user2 = create_test_user(db_session, user_type=UserTypeEnum.company_client)
    response = client.post(
        "/admin/update_username",
        data={
            "old_username": user1.username,
            "new_username": user2.username,
            "confirm_new_username": user2.username
        }
    )
    assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
    assert response.json()["detail"] == "Username modification forbidden."

def test_update_username_company_client_multiple_companies(client, db_session):
    """Test updating username of company_client with multiple companies (should fail)."""
    company1 = create_test_company(db_session, name="Company1")
    company2 = create_test_company(db_session, name="Company2")
    user = create_test_user(db_session, user_type=UserTypeEnum.company_client, company_id=company1.id)
    if company2 not in user.companies:
        user.companies.append(company2)
        db_session.commit()
    response = client.post(
        "/admin/update_username",
        data={
            "old_username": user.username,
            "new_username": "updated@example.com",
            "confirm_new_username": "updated@example.com"
        }
    )
    assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
    assert response.json()["detail"] == "Username modification forbidden."

def test_update_username_with_invalid_format(client, db_session):
    """Test updating username to an invalid email format (should fail)."""
    user = create_test_user(db_session, user_type=UserTypeEnum.company_admin)
    response = client.post(
        "/admin/update_username",
        data={
            "old_username": user.username,
            "new_username": "invalid-email",
            "confirm_new_username": "invalid-email"
        }
    )
    assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.text}"

def test_update_username_company_client_single_company_same_company(client, db_session):
    """Test updating username for a company client with a single company as company admin (should succeed)."""
    company = create_test_company(db_session)
    admin_user = create_test_user(db_session, user_type=UserTypeEnum.company_admin, company_id=company.id)
    client_user = create_test_user(db_session, user_type=UserTypeEnum.company_client, company_id=company.id)
    client = override_user_type(client, UserTypeEnum.company_admin, user_id=admin_user.id, username=admin_user.username)
    response = client.post(
        "/admin/update_username",
        data={
            "old_username": client_user.username,
            "new_username": "updatedclient@example.com",
            "confirm_new_username": "updatedclient@example.com"
        }
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    assert response.json()["detail"] == "Username updated successfully"

def test_update_username_with_very_long_email(client, db_session):
    """Test updating username to a very long email (should fail if length validation exists)."""
    user = create_test_user(db_session, user_type=UserTypeEnum.company_admin)
    long_email = f"{'a' * 200}@example.com"
    response = client.post(
        "/admin/update_username",
        data={
            "old_username": user.username,
            "new_username": long_email,
            "confirm_new_username": long_email
        }
    )
    assert response.status_code in [422, 403], f"Expected 422 or 403, got {response.status_code}: {response.text}"

def test_update_username_with_special_email_characters(client, db_session):
    """Test updating username with special characters in email (should succeed if validation allows)."""
    user = create_test_user(db_session, user_type=UserTypeEnum.company_admin)
    response = client.post(
        "/admin/update_username",
        data={
            "old_username": user.username,
            "new_username": "updated+test@example.com",
            "confirm_new_username": "updated+test@example.com"
        }
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    assert response.json()["detail"] == "Username updated successfully"

def test_update_username_case_sensitivity(client, db_session):
    """Test updating username to a different case (should succeed, with domain normalized to lowercase)."""
    user = create_test_user(db_session, user_type=UserTypeEnum.company_admin)
    original_email = user.username
    new_email = original_email.upper()  # Change case to uppercase
    # Split the email to handle local part and domain separately
    local_part, domain = new_email.split('@')
    expected_email = f"{local_part}@example.com"  # Domain is expected to be lowercase
    response = client.post(
        "/admin/update_username",
        data={
            "old_username": original_email,
            "new_username": new_email,
            "confirm_new_username": new_email
        }
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    assert response.json()["detail"] == "Username updated successfully"
    assert response.json()["user"]["username"] == expected_email, f"Expected {expected_email}, got {response.json()['user']['username']}"

# ===========================================
# Tests for /admin/update_user_profile_info Endpoint
# ===========================================
def test_update_user_profile_info_as_admin_success(client, db_session):
    """Test updating user profile info as admin (should succeed)."""
    user = create_test_user(db_session, user_type=UserTypeEnum.company_admin)
    response = client.post(
        "/admin/update_user_profile_info",
        data={
            "username": user.username,
            "confirm_username": user.username,
            "name": "UpdatedName",
            "surname": "UpdatedSurname"
        }
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    assert response.json()["detail"] == "User profile information updated successfully"
    assert response.json()["user"]["name"] == "UpdatedName"
    assert response.json()["user"]["surname"] == "UpdatedSurname"

def test_update_user_profile_info_mismatch_username(client, db_session):
    """Test updating user profile with mismatched username (should fail)."""
    user = create_test_user(db_session, user_type=UserTypeEnum.company_admin)
    response = client.post(
        "/admin/update_user_profile_info",
        data={
            "username": user.username,
            "confirm_username": "wrong@example.com",
            "name": "UpdatedName"
        }
    )
    assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"

def test_update_user_profile_info_nonexistent_user(client, db_session):
    """Test updating profile info for nonexistent user (should fail)."""
    response = client.post(
        "/admin/update_user_profile_info",
        data={
            "username": "nonexistent@example.com",
            "confirm_username": "nonexistent@example.com",
            "name": "UpdatedName"
        }
    )
    assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
    assert response.json()["detail"] == "User profile modification forbidden."

def test_update_user_profile_info_boundary_values(client, db_session):
    """Test updating user profile info with boundary values for name and surname."""
    user = create_test_user(db_session, user_type=UserTypeEnum.company_admin)
    response = client.post(
        "/admin/update_user_profile_info",
        data={
            "username": user.username,
            "confirm_username": user.username,
            "name": "A",  # Min length
            "surname": "B" * 50  # Max length (assuming 50 as per Form validation)
        }
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    assert response.json()["user"]["name"] == "A"
    assert response.json()["user"]["surname"] == "B" * 50

def test_update_user_profile_info_partial_update(client, db_session):
    """Test updating only one field of user profile info."""
    user = create_test_user(db_session, user_type=UserTypeEnum.company_admin)
    response = client.post(
        "/admin/update_user_profile_info",
        data={
            "username": user.username,
            "confirm_username": user.username,
            "name": "UpdatedName"
        }
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    assert response.json()["user"]["name"] == "UpdatedName"
    assert response.json()["user"]["surname"] is None  # Should not be updated

def test_update_user_profile_info_special_characters(client, db_session):
    """Test updating user profile info with special characters."""
    user = create_test_user(db_session, user_type=UserTypeEnum.company_admin)
    response = client.post(
        "/admin/update_user_profile_info",
        data={
            "username": user.username,
            "confirm_username": user.username,
            "name": "Test@#$%",
            "surname": "User&*()"
        }
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    assert response.json()["user"]["name"] == "Test@#$%"
    assert response.json()["user"]["surname"] == "User&*()"

def test_update_user_profile_info_company_client_multiple_companies(client, db_session):
    """Test updating profile info of company_client with multiple companies (should fail)."""
    company1 = create_test_company(db_session, name="Company1")
    company2 = create_test_company(db_session, name="Company2")
    user = create_test_user(db_session, user_type=UserTypeEnum.company_client, company_id=company1.id)
    if company2 not in user.companies:
        user.companies.append(company2)
        db_session.commit()
    response = client.post(
        "/admin/update_user_profile_info",
        data={
            "username": user.username,
            "confirm_username": user.username,
            "name": "UpdatedName"
        }
    )
    assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
    assert response.json()["detail"] == "Username profile modification forbidden."

def test_update_user_profile_info_empty_strings(client, db_session):
    """Test updating user profile info with empty strings (should fail due to validation)."""
    user = create_test_user(db_session, user_type=UserTypeEnum.company_admin)
    response = client.post(
        "/admin/update_user_profile_info",
        data={
            "username": user.username,
            "confirm_username": user.username,
            "name": "",
            "surname": ""
        }
    )
    assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.text}"
    assert "string_too_short" in str(response.json()), "Error should indicate string length validation failure"

# ===========================================
# Tests for /admin/add_client_user_to_company Endpoint
# ===========================================
def test_add_client_user_to_company_as_admin_success(client, db_session):
    """Test adding a company client to a company as admin (should succeed)."""
    company = create_test_company(db_session)
    # Explicitly create user without company association
    user = create_test_user(db_session, user_type=UserTypeEnum.company_client, company_id=None)
    associated_companies = getattr(user, 'companies', [])
    # Debug: Print associated companies to verify
    print(f"Debug: Associated companies before test: {len(associated_companies)} - {associated_companies}")
    # Ensure no companies are associated
    if associated_companies:
        user.companies.clear()
        db_session.commit()
        db_session.refresh(user)
    assert len(getattr(user, 'companies', [])) == 0, "User should not be associated with any company initially"
    response = client.post(
        "/admin/add_client_user_to_company",
        data={
            "username": user.username,
            "confirm_username": user.username,
            "company_id": company.id
        }
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    assert "successfully been added" in response.json()["detail"]

def test_add_client_user_to_company_as_non_admin(client, db_session):
    """Test adding a company client to a company as non-admin (should fail)."""
    company = create_test_company(db_session)
    user = create_test_user(db_session, user_type=UserTypeEnum.company_client, company_id=None)
    client = override_user_type(client, UserTypeEnum.company_admin)
    response = client.post(
        "/admin/add_client_user_to_company",
        data={
            "username": user.username,
            "confirm_username": user.username,
            "company_id": company.id
        }
    )
    assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
    assert response.json()["detail"] == "Add user to company forbidden."

def test_add_non_client_user_to_company(client, db_session):
    """Test adding a non-client user to a company (should fail)."""
    company = create_test_company(db_session)
    user = create_test_user(db_session, user_type=UserTypeEnum.company_admin)
    response = client.post(
        "/admin/add_client_user_to_company",
        data={
            "username": user.username,
            "confirm_username": user.username,
            "company_id": company.id
        }
    )
    assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
    assert response.json()["detail"] == "Add user to company forbidden."

def test_add_client_user_to_company_already_associated(client, db_session):
    """Test adding a client user to a company they are already associated with (should return message)."""
    company = create_test_company(db_session)
    user = create_test_user(db_session, user_type=UserTypeEnum.company_client, company_id=company.id)
    response = client.post(
        "/admin/add_client_user_to_company",
        data={
            "username": user.username,
            "confirm_username": user.username,
            "company_id": company.id
        }
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    assert "already part of" in response.json()["detail"]

def test_add_client_user_to_company_invalid_company_id(client, db_session):
    """Test adding a client user to a company with invalid company ID (should fail)."""
    user = create_test_user(db_session, user_type=UserTypeEnum.company_client, company_id=None)
    response = client.post(
        "/admin/add_client_user_to_company",
        data={
            "username": user.username,
            "confirm_username": user.username,
            "company_id": 9999
        }
    )
    assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
    assert response.json()["detail"] == "Add user to company forbidden."

def test_add_client_user_to_company_mismatch_username(client, db_session):
    """Test adding a client user with mismatched username (should fail)."""
    company = create_test_company(db_session)
    user = create_test_user(db_session, user_type=UserTypeEnum.company_client, company_id=None)
    response = client.post(
        "/admin/add_client_user_to_company",
        data={
            "username": user.username,
            "confirm_username": "wrong@example.com",
            "company_id": company.id
        }
    )
    assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"

def test_add_client_user_to_company_max_associations(client, db_session):
    """Test adding a client user to many companies (check if there's a limit, if applicable)."""
    company1 = create_test_company(db_session, name="Company1")
    company2 = create_test_company(db_session, name="Company2")
    company3 = create_test_company(db_session, name="Company3")
    user = create_test_user(db_session, user_type=UserTypeEnum.company_client, company_id=company1.id)
    # Add to second company
    response = client.post(
        "/admin/add_client_user_to_company",
        data={
            "username": user.username,
            "confirm_username": user.username,
            "company_id": company2.id
        }
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    # Add to third company
    response = client.post(
        "/admin/add_client_user_to_company",
        data={
            "username": user.username,
            "confirm_username": user.username,
            "company_id": company3.id
        }
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    db_session.refresh(user)
    assert len(user.companies) == 3, "User should be associated with all three companies"

# ===========================================
# Tests for /admin/remove_client_user_from_company Endpoint
# ===========================================
def test_remove_client_user_from_company_as_admin_success(client, db_session):
    """Test removing a company client from a company as admin (should succeed)."""
    company = create_test_company(db_session)
    company2 = create_test_company(db_session, name="Company2")
    user = create_test_user(db_session, user_type=UserTypeEnum.company_client, company_id=company.id)
    if company2 not in user.companies:
        user.companies.append(company2)
        db_session.commit()
    response = client.post(
        "/admin/remove_client_user_from_company",
        data={
            "username": user.username,
            "confirm_username": user.username,
            "company_id": company.id
        }
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    assert "successfully been removed" in response.json()["detail"]

def test_remove_client_user_from_company_last_company(client, db_session):
    """Test removing a company client from their last company (should fail)."""
    company = create_test_company(db_session)
    user = create_test_user(db_session, user_type=UserTypeEnum.company_client, company_id=company.id)
    response = client.post(
        "/admin/remove_client_user_from_company",
        data={
            "username": user.username,
            "confirm_username": user.username,
            "company_id": company.id
        }
    )
    assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
    assert response.json()["detail"] == "Remove user from company forbidden."

def test_remove_client_user_from_company_not_associated(client, db_session):
    """Test removing a client user from a company they are not associated with (should fail)."""
    company = create_test_company(db_session)
    user = create_test_user(db_session, user_type=UserTypeEnum.company_client, company_id=None)
    response = client.post(
        "/admin/remove_client_user_from_company",
        data={
            "username": user.username,
            "confirm_username": user.username,
            "company_id": company.id
        }
    )
    assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
    assert response.json()["detail"] == "Remove user from company forbidden."

def test_remove_client_user_from_company_as_non_admin(client, db_session):
    """Test removing a client user as non-admin (should fail)."""
    company = create_test_company(db_session)
    admin_user = create_test_user(db_session, user_type=UserTypeEnum.company_admin, company_id=company.id)
    client_user = create_test_user(db_session, user_type=UserTypeEnum.company_client, company_id=company.id)
    client = override_user_type(client, UserTypeEnum.company_admin, user_id=admin_user.id, username=admin_user.username)
    response = client.post(
        "/admin/remove_client_user_from_company",
        data={
            "username": client_user.username,
            "confirm_username": client_user.username,
            "company_id": company.id
        }
    )
    assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
    assert response.json()["detail"] == "Remove user from company forbidden."

def test_remove_client_user_from_company_invalid_company_id(client, db_session):
    """Test removing a client user from a company with invalid company ID (should fail)."""
    user = create_test_user(db_session, user_type=UserTypeEnum.company_client, company_id=None)
    response = client.post(
        "/admin/remove_client_user_from_company",
        data={
            "username": user.username,
            "confirm_username": user.username,
            "company_id": 9999
        }
    )
    assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
    assert response.json()["detail"] == "Remove user from company forbidden."

# ===========================================
# Tests for /admin/search_user Endpoint
# ===========================================
def test_search_user_as_admin_success(client, db_session):
    """Test searching for a user as admin (should succeed)."""
    user = create_test_user(db_session, user_type=UserTypeEnum.company_admin)
    response = client.post(
        "/admin/search_user",
        data={"searched_user": user.name}
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    assert len(response.json()["users"]) == 1
    assert response.json()["users"][0]["username"] == user.username

def test_search_user_as_company_admin_same_company(client, db_session):
    """Test searching for a user as company admin in same company (should succeed)."""
    company = create_test_company(db_session)
    admin_user = create_test_user(db_session, user_type=UserTypeEnum.company_admin, company_id=company.id)
    client_user = create_test_user(db_session, user_type=UserTypeEnum.company_client, company_id=company.id)
    client = override_user_type(client, UserTypeEnum.company_admin, user_id=admin_user.id, username=admin_user.username)
    response = client.post(
        "/admin/search_user",
        data={"searched_user": client_user.name}
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    assert len(response.json()["users"]) >= 1, f"Expected at least 1 user, got {len(response.json()['users'])}"

def test_search_user_as_non_admin_forbidden(client, db_session):
    """Test searching for a user as basic user (should fail)."""
    client = override_user_type(client, UserTypeEnum.basic)
    response = client.post(
        "/admin/search_user",
        data={"searched_user": "test"}
    )
    assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
    assert response.json()["detail"] == "Search request forbidden"

def test_search_user_no_results(client, db_session):
    """Test searching for a non-existent user (should fail)."""
    response = client.post(
        "/admin/search_user",
        data={"searched_user": "NonExistentUser"}
    )
    assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
    assert response.json()["detail"] == "No users found."

def test_search_user_case_insensitive(client, db_session):
    """Test searching for a user with case-insensitive match."""
    user = create_test_user(db_session, user_type=UserTypeEnum.company_admin)
    response = client.post(
        "/admin/search_user",
        data={"searched_user": user.name.upper()}
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    assert len(response.json()["users"]) == 1
    assert response.json()["users"][0]["username"] == user.username

def test_search_user_partial_match_name_surname(client, db_session):
    """Test searching with partial match for name and surname combination."""
    user = create_test_user(db_session, user_type=UserTypeEnum.company_admin)
    search_str = f"{user.name[:3]} {user.surname[:3]}"  # Partial match
    response = client.post(
        "/admin/search_user",
        data={"searched_user": search_str}
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    assert len(response.json()["users"]) == 1
    assert response.json()["users"][0]["username"] == user.username

def test_search_user_with_special_characters(client, db_session):
    """Test searching with special characters in the search string."""
    user = create_test_user(db_session, user_type=UserTypeEnum.company_admin, username="special@example.com")
    response = client.post(
        "/admin/search_user",
        data={"searched_user": "Test@#$%"}
    )
    assert response.status_code == 403, f"Expected 403 (or 200 if special chars are handled), got {response.status_code}: {response.text}"

def test_search_user_empty_string(client, db_session):
    """Test searching with an empty string (should fail)."""
    create_test_user(db_session, user_type=UserTypeEnum.company_admin)
    response = client.post(
        "/admin/search_user",
        data={"searched_user": ""}
    )
    assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
    assert response.json()["detail"] == "Search query cannot be empty."

def test_search_user_very_long_string(client, db_session):
    """Test searching with a very long string (should handle gracefully)."""
    create_test_user(db_session, user_type=UserTypeEnum.company_admin)
    long_string = "a" * 1000
    response = client.post(
        "/admin/search_user",
        data={"searched_user": long_string}
    )
    assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
    assert response.json()["detail"] == "No users found."

def test_search_user_as_company_commercial_non_client(client, db_session):
    """Test searching as company commercial for non-client user (should filter out)."""
    company = create_test_company(db_session)
    commercial_user = create_test_user(db_session, user_type=UserTypeEnum.company_commercial, company_id=company.id)
    admin_user = create_test_user(db_session, user_type=UserTypeEnum.company_admin, company_id=company.id)
    client = override_user_type(client, UserTypeEnum.company_commercial, user_id=commercial_user.id, username=commercial_user.username)
    response = client.post(
        "/admin/search_user",
        data={"searched_user": admin_user.name}
    )
    assert response.status_code == 403, f"Expected 403 (or 200 with filtered results), got {response.status_code}: {response.text}"
    if response.status_code == 200:
        assert len(response.json()["users"]) == 0, "Non-client users should be filtered out for company commercial"

def test_search_user_with_sql_injection_attempt(client, db_session):
    """Test searching with potential SQL injection string (should be safely handled)."""
    create_test_user(db_session, user_type=UserTypeEnum.company_admin)
    response = client.post(
        "/admin/search_user",
        data={"searched_user": "'; DROP TABLE users; --"}
    )
    assert response.status_code == 403, f"Expected 403 (or 200 with no results), got {response.status_code}: {response.text}"
    if response.status_code == 200:
        assert len(response.json()["users"]) == 0, "Should not return results for malicious input"

def test_search_user_with_unicode_characters(client, db_session):
    """Test searching with Unicode characters (should succeed if supported)."""
    user = create_test_user(db_session, user_type=UserTypeEnum.company_admin)
    user.name = "Тест"  # Cyrillic characters
    db_session.commit()
    response = client.post(
        "/admin/search_user",
        data={"searched_user": "Тест"}
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    assert len(response.json()["users"]) == 1, "Should return the user with Unicode name"
    assert response.json()["users"][0]["name"] == "Тест"