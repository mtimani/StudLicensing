# ===========================================
# Imports
# ===========================================
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base
from app.models import Company, Users, UserTypeEnum, CompanyAdmin
from app.company import router, get_db
from app.auth import get_current_user
from fastapi import FastAPI
from datetime import datetime
import uuid

# ===========================================
# Test App Setup
# ===========================================
# Create a test app with the company router
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
    Additionally, clear the Company table before each test to ensure isolation.
    """
    SessionTest = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionTest()
    # Clear the Company table before the test to ensure a clean state
    session.query(Company).delete()
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
        return {"id": 1, "type": UserTypeEnum.admin, "name": "Admin", "username": "admin", "jti": "mock_jti"}
    # Apply the override for get_current_user at the app level
    app.dependency_overrides[get_current_user] = override_get_current_user
    return TestClient(app)

# ===========================================
# Helper Functions
# ===========================================
# Helper to create a company in the database for testing
def create_test_company(db_session, name="TestCo"):
    company = Company(companyName=name)
    db_session.add(company)
    db_session.commit()
    db_session.refresh(company)
    return company

# Helper to create a user in the database for testing
def create_test_user(db_session, user_type=UserTypeEnum.admin, company_id=None):
    unique_username = f"test_user_{uuid.uuid4().hex}@example.com"
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
    else:
        user = Users(
            username=unique_username,
            name="Test",
            surname="User",
            hashedPassword="hashed_pass",
            creationDate=datetime.utcnow(),
            activated=True,
            userType=user_type
        )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

# Helper to override get_current_user for a specific test with a custom user type
def override_user_type(client, user_type, user_id=1, username="test_user"):
    """
    Override get_current_user for a specific test to return a user with the specified type.
    """
    def custom_get_current_user():
        return {"id": user_id, "type": user_type, "name": "Test", "username": username, "jti": "mock_jti"}
    app.dependency_overrides[get_current_user] = custom_get_current_user
    return client

# ===========================================
# Tests for /company/create Endpoint
# ===========================================
def test_create_company_as_admin(client, db_session):
    """Test creating a company as an admin user."""
    response = client.post("/company/create", data={"companyName": "NewCo"})
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    assert response.json()["detail"] == "Company created successfully"
    assert response.json()["company"] == "NewCo"

def test_create_company_as_non_admin(client, db_session):
    """Test creating a company as a non-admin user (should fail)."""
    client = override_user_type(client, UserTypeEnum.basic)
    response = client.post("/company/create", data={"companyName": "NewCo"})
    assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
    assert response.json()["detail"] == "Error creating client."

def test_create_company_empty_name(client, db_session):
    """Test creating a company with an empty name (currently accepted by the app)."""
    response = client.post("/company/create", data={"companyName": ""})
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    assert response.json()["detail"] == "Company created successfully"
    assert response.json()["company"] == ""

def test_create_company_max_length_name(client, db_session):
    """Test creating a company with a name at the maximum length (100 characters)."""
    long_name = "A" * 100
    response = client.post("/company/create", data={"companyName": long_name})
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    assert response.json()["company"] == long_name

def test_create_company_over_max_length_name(client, db_session):
    """Test creating a company with a name over the maximum length (should fail)."""
    long_name = "A" * 101
    try:
        response = client.post("/company/create", data={"companyName": long_name})
        assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.text}"
    except Exception as e:
        # TestClient raises an exception for form data validation errors, so we catch it
        # and consider this as expected behavior for validation failure.
        assert "validation error" in str(e).lower(), f"Unexpected exception: {e}"

# ===========================================
# Tests for /company/delete/{client_id} Endpoint
# ===========================================
def test_delete_company_as_admin(client, db_session):
    """Test deleting a company as an admin user."""
    company = create_test_company(db_session)
    response = client.delete(f"/company/delete/{company.id}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    assert response.json()["detail"] == "Company deleted successfully"

def test_delete_company_as_non_admin(client, db_session):
    """Test deleting a company as a non-admin user (should fail)."""
    company = create_test_company(db_session)
    client = override_user_type(client, UserTypeEnum.basic)
    response = client.delete(f"/company/delete/{company.id}")
    assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
    assert response.json()["detail"] == "Error deleting client."

def test_delete_non_existent_company(client, db_session):
    """Test deleting a company that does not exist (should fail)."""
    response = client.delete("/company/delete/9999")
    assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
    assert response.json()["detail"] == "Error deleting client."

def test_delete_company_with_id_zero(client, db_session):
    """Test deleting a company with ID 0 (should fail as invalid)."""
    response = client.delete("/company/delete/0")
    assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
    assert response.json()["detail"] == "Error deleting client."

# ===========================================
# Tests for /company/update/{client_id} Endpoint
# ===========================================
def test_update_company_as_admin(client, db_session):
    """Test updating a company as an admin user."""
    company = create_test_company(db_session)
    response = client.put(f"/company/update/{company.id}", data={"companyName": "UpdatedCo"})
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    assert response.json()["detail"] == "Company updated successfully"
    assert response.json()["companyName"] == "UpdatedCo"

def test_update_company_as_company_admin_same_company(client, db_session):
    """Test updating a company as a CompanyAdmin of the same company."""
    company = create_test_company(db_session)
    user = create_test_user(db_session, user_type=UserTypeEnum.company_admin, company_id=company.id)
    client = override_user_type(client, UserTypeEnum.company_admin, user_id=user.id, username=user.username)
    response = client.put(f"/company/update/{company.id}", data={"companyName": "UpdatedCo"})
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    assert response.json()["companyName"] == "UpdatedCo"

def test_update_company_as_company_admin_different_company(client, db_session):
    """Test updating a company as a CompanyAdmin of a different company (should fail)."""
    company1 = create_test_company(db_session, name="Company1")
    company2 = create_test_company(db_session, name="Company2")
    user = create_test_user(db_session, user_type=UserTypeEnum.company_admin, company_id=company2.id)
    client = override_user_type(client, UserTypeEnum.company_admin, user_id=user.id, username=user.username)
    response = client.put(f"/company/update/{company1.id}", data={"companyName": "UpdatedCo"})
    assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
    assert response.json()["detail"] == "Error modifying client."

def test_update_company_as_non_admin(client, db_session):
    """Test updating a company as a non-admin user (should fail)."""
    company = create_test_company(db_session)
    client = override_user_type(client, UserTypeEnum.basic)
    response = client.put(f"/company/update/{company.id}", data={"companyName": "UpdatedCo"})
    assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
    assert response.json()["detail"] == "Error modifying client."

def test_update_non_existent_company(client, db_session):
    """Test updating a company that does not exist (should fail)."""
    response = client.put("/company/update/9999", data={"companyName": "UpdatedCo"})
    assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
    assert response.json()["detail"] == "Error modifying client."

def test_update_company_empty_name(client, db_session):
    """Test updating a company with an empty name (currently accepted by the app)."""
    company = create_test_company(db_session)
    response = client.put(f"/company/update/{company.id}", data={"companyName": ""})
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    assert response.json()["detail"] == "Company updated successfully"
    assert response.json()["companyName"] == ""

def test_update_company_max_length_name(client, db_session):
    """Test updating a company with a name at the maximum length (100 characters)."""
    company = create_test_company(db_session)
    long_name = "A" * 100
    response = client.put(f"/company/update/{company.id}", data={"companyName": long_name})
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    assert response.json()["companyName"] == long_name

def test_update_company_over_max_length_name(client, db_session):
    """Test updating a company with a name over the maximum length (should fail)."""
    company = create_test_company(db_session)
    long_name = "A" * 101
    try:
        response = client.put(f"/company/update/{company.id}", data={"companyName": long_name})
        assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.text}"
    except Exception as e:
        # TestClient raises an exception for form data validation errors, so we catch it
        # and consider this as expected behavior for validation failure.
        assert "validation error" in str(e).lower(), f"Unexpected exception: {e}"

# ===========================================
# Tests for /company/search Endpoint
# ===========================================
def test_search_company_by_name(client, db_session):
    """Test searching for a company by name as an admin."""
    create_test_company(db_session, name="SearchCo")
    response = client.post("/company/search", data={"company_name": "Search"})
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    assert len(response.json()["companies"]) == 1, f"Expected 1 company, got {len(response.json()['companies'])}"
    assert response.json()["companies"][0]["company_name"] == "SearchCo"

def test_search_company_by_id(client, db_session):
    """Test searching for a company by ID as an admin."""
    company = create_test_company(db_session, name="SearchByIdCo")
    response = client.post("/company/search", data={"company_id": company.id})
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    assert len(response.json()["companies"]) == 1, f"Expected 1 company, got {len(response.json()['companies'])}"
    assert response.json()["companies"][0]["company_name"] == "SearchByIdCo"

def test_search_company_all(client, db_session):
    """Test searching for all companies (no parameters) as an admin."""
    create_test_company(db_session, name="Company1")
    create_test_company(db_session, name="Company2")
    response = client.post("/company/search", data={})
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    assert len(response.json()["companies"]) == 2, f"Expected 2 companies, got {len(response.json()['companies'])}"

def test_search_company_both_parameters(client, db_session):
    """Test searching with both name and ID provided (should fail)."""
    company = create_test_company(db_session, name="SearchCo")
    response = client.post("/company/search", data={"company_name": "Search", "company_id": company.id})
    assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
    assert response.json()["detail"] == "Provide either company_name or company_id, not both."

def test_search_company_as_non_admin(client, db_session):
    """Test searching for a company as a non-admin user (should fail)."""
    create_test_company(db_session, name="SearchCo")
    client = override_user_type(client, UserTypeEnum.basic)
    response = client.post("/company/search", data={"company_name": "Search"})
    assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
    assert response.json()["detail"] == "Search request forbidden"

def test_search_company_id_zero(client, db_session):
    """Test searching for a company with ID 0 (should fail)."""
    response = client.post("/company/search", data={"company_id": 0})
    assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
    assert response.json()["detail"] == "No companies found."

def test_search_company_no_results_by_name(client, db_session):
    """Test searching for a company with a non-matching name (should fail)."""
    create_test_company(db_session, name="SearchCo")
    response = client.post("/company/search", data={"company_name": "NonExistent"})
    assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
    assert response.json()["detail"] == "No companies found."

def test_search_company_no_results_by_id(client, db_session):
    """Test searching for a company with a non-matching ID (should fail)."""
    create_test_company(db_session, name="SearchCo")
    response = client.post("/company/search", data={"company_id": 9999})
    assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
    assert response.json()["detail"] == "No companies found."