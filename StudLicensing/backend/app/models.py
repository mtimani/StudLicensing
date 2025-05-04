# ===========================================
# Imports
# ===========================================
from database import Base
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
    sladmin = "sladmin"
    slclientadmin = "slclientadmin"
    slcclient = "slcclient"
    slccommercial = "slccommercial"
    slcdevelopper = "slcdevelopper"



# Many to many relationship tables

functionalities_licenses_correspondance = Table(
    "functionalities_licenses",
    Base.metadata,
    Column("slccfunctionality_id", ForeignKey("slccfunctionality.id"), primary_key=True),
    Column("slclicense_id", ForeignKey("slclicense.id"), primary_key=True)
)

machines_licenses_correspondance = Table(
    "machines_licenses",
    Base.metadata,
    Column("slccmachine_id", ForeignKey("slccmachine.id"), primary_key=True),
    Column("slcclicense_id", ForeignKey("slcclicense.id"), primary_key=True)
)

commercials_licenses_correspondance=Table(
    "commercials_licenses",
    Base.metadata,
    Column("slccommercial_id", ForeignKey("slccommercial.id"), primary_key=True),
    Column("slclicense_id", ForeignKey("slclicense.id"), primary_key=True)
)


companies_clients_correspondance=Table(
    "companies_clients",
    Base.metadata,
    Column("slclient_id", ForeignKey("slclient.id"), primary_key=True),
    Column("slcclient_id", ForeignKey("slcclient.id"), primary_key=True)
)

# Global Users class
class Users(Base):
    __tablename__='users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    name = Column(String, nullable=False)
    surname = Column(String, nullable=False)
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

class SLAdmin(Users):
    __tablename__='sladmin'

    id = Column(Integer, ForeignKey("users.id"), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': UserTypeEnum.sladmin,
    }



class SLCClient(Users):
    __tablename__='slcclient'

    id = Column(Integer, ForeignKey("users.id"), primary_key=True)

    companies=relationship("SLClient",secondary=companies_clients_correspondance,back_populates='clients')
    __mapper_args__ = {
        'polymorphic_identity': UserTypeEnum.slcclient,
    }
    
class SLClientAdmin(Users):
    __tablename__='slclientadmin'

    id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    company_id =Column(Integer,ForeignKey('slclient.id'))

    company=relationship("SLClient", backref="slclientadmin", foreign_keys=[company_id])

    __mapper_args__ = {
        'polymorphic_identity': UserTypeEnum.slclientadmin,
    }

class SLCCommercial(Users):
    __tablename__='slccommercial'

    id = Column(Integer, ForeignKey("users.id"), primary_key=True) 
    company_id =Column(Integer,ForeignKey('slclient.id'))

    company=relationship("SLClient", backref="slccommercial", foreign_keys=[company_id])
    licenses=relationship("SLCLicense",secondary=commercials_licenses_correspondance,back_populates='commercials')
    __mapper_args__ = {
        'polymorphic_identity': UserTypeEnum.slccommercial,
    }

class SLCDevelopper(Users):
    __tablename__='slcdevelopper'

    id = Column(Integer, ForeignKey("users.id"), primary_key=True) 
    company_id =Column(Integer,ForeignKey('slclient.id'))

    company=relationship("SLClient", backref="slcdevelopper", foreign_keys=[company_id])


    __mapper_args__ = {
        'polymorphic_identity': UserTypeEnum.slcdevelopper,
    }

class SLClient(Base):
    __tablename__='slclient'
    
    id = Column(Integer, primary_key=True, index=True)
    companyName=Column(String,unique=False)
    
    clients=relationship("SLCClient",secondary=companies_clients_correspondance,back_populates='companies')



class SLCCMachine(Base):
    __tablename__='slccmachine'

    id=Column(Integer,primary_key=True,index=True)
    macAddress=Column(String,unique=False)
    cpuId=Column(String,unique=False)
    hasLicenseActivated=Column(Boolean,unique=False)
    licenseUsed=Column(Integer,ForeignKey('slcclicense.id'))
    lastVerificationPassed=Column(Date,unique=False)
    lastVerificationTry=Column(Date,unique=False)

    licenses=relationship("SLCCLicense",secondary=machines_licenses_correspondance,back_populates='machines')

class LicenseConsumptionType(str, Enum):
    basic="basic"

class SLCLicense(Base):
    __tablename__='slclicense'

    id=Column(Integer,primary_key=True,index=True)
    name=Column(String,unique=False)
    consumptionType=Column(SQLAlchemyEnum(LicenseConsumptionType), default=LicenseConsumptionType.basic)
    maxLicense=Column(Integer,unique=False)
    company_id =Column(Integer,ForeignKey('slclient.id'))
    application_id =Column(Integer,ForeignKey('slccapplication.id'))

    company=relationship("SLClient", backref="slcclicense")
    application=relationship("SLCCApplication", backref="slcclicense")

    functionalities = relationship("SLCCFunctionality",secondary=functionalities_licenses_correspondance,back_populates='licenses')  
    commercials=relationship("SLCCommercial",secondary=commercials_licenses_correspondance,back_populates='licenses')

class SLCCLicense(Base):
    __tablename__='slcclicense'

    id=Column(Integer,primary_key=True,index=True)
    numberOfUseLeft=Column(String,unique=False)    
    client_id =Column(Integer,ForeignKey('slcclient.id'))
    slclicense_id=Column(Integer,ForeignKey('slclicense.id'))

    client=relationship("SLCClient", backref="slcclicense")
    slclicense=relationship("SLCLicense", backref="slcclicense")

    machines=relationship("SLCCMachine",secondary=machines_licenses_correspondance,back_populates='licenses')  
    


class SLCCFunctionality(Base):
    __tablename__='slccfunctionality'

    id=Column(Integer,primary_key=True,index=True)
    name=Column(String,unique=False)
    application_id=Column(Integer,ForeignKey('slccapplication.id'))

    licenses = relationship("SLCLicense",secondary=functionalities_licenses_correspondance,back_populates='functionalities')
    application=relationship("SLCCApplication", backref="slccfunctionality")

class SLCCApplication(Base):
    __tablename__="slccapplication"

    id=Column(Integer,primary_key=True,index=True)
    name=Column(String,unique=False)
    licenceCheckingPeriod=Column(Integer,unique=False)
    company_id =Column(Integer,ForeignKey('slclient.id'))

    company=relationship("SLClient", backref="slccapplication")

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