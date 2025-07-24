# ===========================================
# Imports
# ===========================================
from app.database import Base
from sqlalchemy import Table,ForeignKey,Column,Integer,String,Date,Boolean,DateTime, Enum as SQLAlchemyEnum
from sqlalchemy_imageattach.entity import Image, image_attachment
from sqlalchemy.orm import relationship
from sqlalchemy_imageattach.stores.fs import FileSystemStore
from datetime import datetime
from enum import Enum



# ===========================================
# Store declaration for profile images upload
# ===========================================
store = FileSystemStore(
    path="/uploads",
    base_url="http://localhost:8000/uploads/"
)



# ===========================================
# Database models classes declaration
# ===========================================

# Enum to specify user type for class Users
class UserTypeEnum(str, Enum):
    basic="basic"
    admin = "admin"
    company_admin = "company_admin"
    company_client = "company_client"
    company_commercial = "company_commercial"
    company_developper = "company_developper"



# Many to many relationship tables

functionalities_licenses_correspondance = Table(
    "functionalities_licenses",
    Base.metadata,
    Column("functionality_id", ForeignKey("functionality.id"), primary_key=True),
    Column("license_id", ForeignKey("license_type.id"), primary_key=True)
)

machines_licenses_correspondance = Table(
    "machines_licenses",
    Base.metadata,
    Column("machine_id", ForeignKey("machine.id"), primary_key=True),
    Column("license_id", ForeignKey("license_use.id"), primary_key=True)
)

commercials_licenses_correspondance=Table(
    "commercials_licenses",
    Base.metadata,
    Column("company_commercial_id", ForeignKey("company_commercial.id"), primary_key=True),
    Column("license_id", ForeignKey("license_type.id"), primary_key=True)
)


companies_clients_correspondance=Table(
    "companies_clients",
    Base.metadata,
    Column("company_id", ForeignKey("company.id"), primary_key=True),
    Column("company_client_id", ForeignKey("company_client.id"), primary_key=True)
)

# Global Users class
class Users(Base):
    __tablename__='users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    name = Column(String, nullable=False)
    surname = Column(String, nullable=False)
    phoneNumber = Column(String(50), nullable=True)
    hashedPassword = Column(String, nullable=True)
    creationDate = Column(DateTime, nullable=False)
    activated = Column(Boolean, default=False, nullable=False)
    userType=Column(SQLAlchemyEnum(UserTypeEnum), default=UserTypeEnum.basic)
    profilePicture = image_attachment('UserPicture', back_populates="user")    
    __mapper_args__ = {
        'polymorphic_identity': UserTypeEnum.basic,
        'polymorphic_on': userType,
        'with_polymorphic': '*'
    }

# User Profile Pictures class
class UserPicture(Base, Image):
    __tablename__ = 'profilePictures'
    
    # Image Store
    store = store
    
    userId = Column(Integer, ForeignKey('users.id'), primary_key=True)
    user = relationship('Users', overlaps="profilePicture")

class Admin(Users):
    __tablename__='admin'

    id = Column(Integer, ForeignKey("users.id"), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': UserTypeEnum.admin,
    }

class CompanyClient(Users):
    __tablename__='company_client'

    id = Column(Integer, ForeignKey("users.id"), primary_key=True)

    companies=relationship("Company",secondary=companies_clients_correspondance,back_populates='clients')
    __mapper_args__ = {
        'polymorphic_identity': UserTypeEnum.company_client,
    }
    
class CompanyAdmin(Users):
    __tablename__='company_admin'

    id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    company_id =Column(Integer,ForeignKey('company.id'))

    company=relationship("Company", backref="companyadmin", foreign_keys=[company_id])

    __mapper_args__ = {
        'polymorphic_identity': UserTypeEnum.company_admin,
    }

class CompanyCommercial(Users):
    __tablename__='company_commercial'

    id = Column(Integer, ForeignKey("users.id"), primary_key=True) 
    company_id =Column(Integer,ForeignKey('company.id'))

    company=relationship("Company", backref="company_commercial", foreign_keys=[company_id])
    licenses=relationship("LicenseType",secondary=commercials_licenses_correspondance,back_populates='commercials')
    __mapper_args__ = {
        'polymorphic_identity': UserTypeEnum.company_commercial,
    }

class CompanyDevelopper(Users):
    __tablename__='company_developper'

    id = Column(Integer, ForeignKey("users.id"), primary_key=True) 
    company_id =Column(Integer,ForeignKey('company.id'))

    company=relationship("Company", backref="company_developper", foreign_keys=[company_id])


    __mapper_args__ = {
        'polymorphic_identity': UserTypeEnum.company_developper,
    }

class Company(Base):
    __tablename__='company'
    
    id = Column(Integer, primary_key=True, index=True)
    companyName=Column(String, unique=False)
    
    clients=relationship("CompanyClient",secondary=companies_clients_correspondance,back_populates='companies')



class Machine(Base):
    __tablename__='machine'

    id=Column(Integer,primary_key=True,index=True)
    macAddress=Column(String,unique=False)
    cpuId=Column(String,unique=False)
    hasLicenseActivated=Column(Boolean,unique=False)
    licenseUsed=Column(Integer,ForeignKey('license_use.id'))
    lastVerificationPassed=Column(Date,unique=False)
    lastVerificationTry=Column(Date,unique=False)

    licenses=relationship("LicenseUse",secondary=machines_licenses_correspondance,back_populates='machines')

class LicenseConsumptionType(str, Enum):
    basic="basic"

class LicenseType(Base):
    __tablename__='license_type'

    id=Column(Integer,primary_key=True,index=True)
    name=Column(String,unique=False)
    consumptionType=Column(SQLAlchemyEnum(LicenseConsumptionType), default=LicenseConsumptionType.basic)
    maxLicense=Column(Integer,unique=False)
    company_id =Column(Integer,ForeignKey('company.id'))
    application_id =Column(Integer,ForeignKey('application.id'))

    company=relationship("Company", backref="license")
    application=relationship("Application", backref="license")

    functionalities = relationship("Functionality",secondary=functionalities_licenses_correspondance,back_populates='licenses')  
    commercials=relationship("CompanyCommercial",secondary=commercials_licenses_correspondance,back_populates='licenses')

class LicenseUse(Base):
    __tablename__='license_use'

    id=Column(Integer,primary_key=True,index=True)
    numberOfUseLeft=Column(String,unique=False)    
    client_id =Column(Integer,ForeignKey('company_client.id'))
    license_id=Column(Integer,ForeignKey('license_type.id'))

    client=relationship("CompanyClient", backref="license")
    license_type=relationship("LicenseType", backref="license_use")

    machines=relationship("Machine",secondary=machines_licenses_correspondance,back_populates='licenses')  
    


class Functionality(Base):
    __tablename__='functionality'

    id=Column(Integer,primary_key=True,index=True)
    name=Column(String,unique=False)
    application_id=Column(Integer,ForeignKey('application.id'))

    licenses = relationship("LicenseType",secondary=functionalities_licenses_correspondance,back_populates='functionalities')
    application=relationship("Application", backref="functionality")

class Application(Base):
    __tablename__="application"

    id=Column(Integer,primary_key=True,index=True)
    name=Column(String,unique=False)
    licenceCheckingPeriod=Column(Integer,unique=False)
    company_id =Column(Integer,ForeignKey('company.id'))

    company=relationship("Company", backref="application")

# Tokens used for JWT Session tokens => To maintain authenticated user connection
class SessionTokens(Base):
    __tablename__ = 'session_tokens'
    
    id = Column(Integer, primary_key=True, index=True)
    jti = Column(String, unique=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)

    user = relationship("Users", backref="session_tokens")

# Tokens used for email validation
class ValidationTokens(Base):
    __tablename__ = 'validation_tokens'
    
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)
    
    user = relationship("Users", backref="validation_tokens")

# Tokens used for password reset
class PasswordResetTokens(Base):
    __tablename__ = 'password_reset_tokens'
    
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)
    
    user = relationship("Users", backref="password_reset_tokens")

# Table used to track login attempts => used for preventing bruteforce attacks
class LoginAttempt(Base):
    __tablename__ = "login_attempts"
    
    id = Column(Integer, primary_key=True)
    username = Column(String, index=True)
    ip_address = Column(String, index=True)
    success = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)