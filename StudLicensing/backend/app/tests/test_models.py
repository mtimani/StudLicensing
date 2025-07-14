# ===========================================
# Imports
# ===========================================
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base
from app.models import (
    Users, UserTypeEnum, Admin, CompanyClient, CompanyAdmin,
    CompanyCommercial, CompanyDevelopper, Company, Machine,
    LicenseType, LicenseUse, Functionality, Application, UserPicture,
    SessionTokens, ValidationTokens, PasswordResetTokens, store,
    LicenseConsumptionType
)
from datetime import datetime, timedelta
import uuid
from io import BytesIO



# =====================================================================
# Tests
# =====================================================================

# Fixture for in-memory database
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
    """
    SessionTest = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionTest()
    yield session
    session.rollback()
    session.close()

def test_users_model_creation(db_session):
    """
    Test basic creation of a Users model instance and its attributes.
    """
    unique_username = f"test_user_{uuid.uuid4().hex}@example.com"
    user = Users(
        username=unique_username,
        name="Test",
        surname="User",
        hashedPassword="hashed_pass",
        creationDate=datetime.utcnow(),
        activated=False,
        userType=UserTypeEnum.basic
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    assert user.id is not None
    assert user.username == unique_username
    assert user.activated is False
    assert user.userType == UserTypeEnum.basic

def test_users_polymorphic_inheritance(db_session):
    """
    Test polymorphic inheritance for user types.
    """
    unique_username = f"admin_{uuid.uuid4().hex}@example.com"
    admin = Admin(
        username=unique_username,
        name="Admin",
        surname="User",
        hashedPassword="hashed_pass",
        creationDate=datetime.utcnow(),
        activated=True
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    assert admin.userType == UserTypeEnum.admin
    assert isinstance(admin, Users)

def test_user_picture_relationship(db_session):
    """
    Test relationship between Users and UserPicture.
    """
    unique_username = f"picture_user_{uuid.uuid4().hex}@example.com"
    user = Users(
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
    # Simulate adding a picture with mock file data
    mock_file = BytesIO(b"mock image data")
    picture = UserPicture(
        userId=user.id,
        mimetype="image/png",
        width=100,
        height=100,
        store=store
    )
    picture.file = mock_file  # Assign mock file to satisfy sqlalchemy_imageattach
    user.profilePicture = [picture]
    db_session.commit()
    db_session.refresh(user)
    assert len(list(user.profilePicture)) == 1
    assert user.profilePicture[0].userId == user.id

def test_many_to_many_relationships(db_session):
    """
    Test many-to-many relationships (e.g., Company and CompanyClient).
    """
    company = Company(companyName="TestCo")
    unique_username = f"client_{uuid.uuid4().hex}@example.com"
    client = CompanyClient(
        username=unique_username,
        name="Client",
        surname="User",
        hashedPassword="hashed_pass",
        creationDate=datetime.utcnow(),
        activated=True
    )
    db_session.add(company)
    db_session.add(client)
    db_session.commit()
    db_session.refresh(company)
    db_session.refresh(client)
    company.clients.append(client)
    db_session.commit()
    db_session.refresh(company)
    assert len(company.clients) == 1
    assert company.clients[0].username == unique_username
    assert len(client.companies) == 1
    assert client.companies[0].companyName == "TestCo"

def test_company_admin_relationship(db_session):
    """
    Test one-to-one relationship between Company and CompanyAdmin.
    """
    company = Company(companyName="AdminCo")
    unique_username = f"company_admin_{uuid.uuid4().hex}@example.com"
    admin = CompanyAdmin(
        username=unique_username,
        name="Company",
        surname="Admin",
        hashedPassword="hashed_pass",
        creationDate=datetime.utcnow(),
        activated=True,
        company=company
    )
    db_session.add(company)
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(company)
    db_session.refresh(admin)
    assert admin.company.companyName == "AdminCo"
    assert admin.userType == UserTypeEnum.company_admin

def test_license_type_and_functionality_relationship(db_session):
    """
    Test many-to-many relationship between LicenseType and Functionality.
    """
    company = Company(companyName="LicenseCo")
    app = Application(name="TestApp", licenceCheckingPeriod=30, company=company)
    license_type = LicenseType(
        name="TestLicense",
        consumptionType=LicenseConsumptionType.basic,
        maxLicense=10,
        company=company,
        application=app
    )
    functionality = Functionality(name="TestFunc", application=app)
    license_type.functionalities.append(functionality)
    db_session.add(company)
    db_session.add(app)
    db_session.add(license_type)
    db_session.add(functionality)
    db_session.commit()
    db_session.refresh(license_type)
    assert len(license_type.functionalities) == 1
    assert license_type.functionalities[0].name == "TestFunc"
    assert len(functionality.licenses) == 1
    assert functionality.licenses[0].name == "TestLicense"

def test_machine_and_license_use_relationship(db_session):
    """
    Test many-to-many relationship between Machine and LicenseUse.
    """
    company = Company(companyName="MachineCo")
    app = Application(name="MachineApp", licenceCheckingPeriod=30, company=company)
    license_type = LicenseType(
        name="MachineLicense",
        consumptionType=LicenseConsumptionType.basic,
        maxLicense=5,
        company=company,
        application=app
    )
    unique_username = f"client_machine_{uuid.uuid4().hex}@example.com"
    client = CompanyClient(
        username=unique_username,
        name="Client",
        surname="Machine",
        hashedPassword="hashed_pass",
        creationDate=datetime.utcnow(),
        activated=True
    )
    license_use = LicenseUse(numberOfUseLeft="5", client=client, license_type=license_type)
    machine = Machine(
        macAddress="00:00:0C:9F:F0:01",
        cpuId="CPU123",
        hasLicenseActivated=False
    )
    license_use.machines.append(machine)
    db_session.add(company)
    db_session.add(app)
    db_session.add(license_type)
    db_session.add(client)
    db_session.add(license_use)
    db_session.add(machine)
    db_session.commit()
    db_session.refresh(license_use)
    assert len(license_use.machines) == 1
    assert license_use.machines[0].macAddress == "00:00:0C:9F:F0:01"
    assert len(machine.licenses) == 1
    assert machine.licenses[0].numberOfUseLeft == "5"

def test_session_tokens_creation(db_session):
    """
    Test creation of SessionTokens and relationship with Users.
    """
    unique_username = f"session_user_{uuid.uuid4().hex}@example.com"
    user = Users(
        username=unique_username,
        name="Session",
        surname="User",
        hashedPassword="hashed_pass",
        creationDate=datetime.utcnow(),
        activated=True
    )
    token = SessionTokens(
        jti=str(uuid.uuid4()),
        user=user,
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )
    db_session.add(user)
    db_session.add(token)
    db_session.commit()
    db_session.refresh(user)
    assert len(user.session_tokens) == 1
    assert user.session_tokens[0].jti == token.jti
    assert token.is_active is True

def test_validation_tokens_creation(db_session):
    """
    Test creation of ValidationTokens and relationship with Users.
    """
    unique_username = f"validation_user_{uuid.uuid4().hex}@example.com"
    user = Users(
        username=unique_username,
        name="Validation",
        surname="User",
        hashedPassword="hashed_pass",
        creationDate=datetime.utcnow(),
        activated=False
    )
    token = ValidationTokens(
        token=str(uuid.uuid4()),
        user=user,
        expires_at=datetime.utcnow() + timedelta(days=1)
    )
    db_session.add(user)
    db_session.add(token)
    db_session.commit()
    db_session.refresh(user)
    assert len(user.validation_tokens) == 1
    assert user.validation_tokens[0].token == token.token
    assert token.is_used is False

def test_password_reset_tokens_creation(db_session):
    """
    Test creation of PasswordResetTokens and relationship with Users.
    """
    unique_username = f"reset_user_{uuid.uuid4().hex}@example.com"
    user = Users(
        username=unique_username,
        name="Reset",
        surname="User",
        hashedPassword="hashed_pass",
        creationDate=datetime.utcnow(),
        activated=True
    )
    token = PasswordResetTokens(
        token=str(uuid.uuid4()),
        user=user,
        expires_at=datetime.utcnow() + timedelta(hours=2)
    )
    db_session.add(user)
    db_session.add(token)
    db_session.commit()
    db_session.refresh(user)
    assert len(user.password_reset_tokens) == 1
    assert user.password_reset_tokens[0].token == token.token
    assert token.is_used is False