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

 # enum to specify user type for class Users
class UserTypeEnum(str, Enum):
    basic="basic"
    sladmin = "sladmin"
    slclient = "slclient"
    slclientadmin = "slclientadmin"
    slcclient = "slcclient"
    slccommercial = "slccommercial"
    slcdevelopper = "slcdevelopper"


# Global Users class
class Users(Base):
    __tablename__='users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    name = Column(String, nullable=False)
    surname = Column(String, nullable=False)
    hashedPassword = Column(String, nullable=False)
    creationDate = Column(DateTime, nullable=False)
    activated = Column(Boolean, default=False, nullable=False)
    userType=Column(SQLAlchemyEnum(UserTypeEnum), default=UserTypeEnum.basic)
    profilePicture = image_attachment('UserPicture')    


# User Profile Pictures class
class UserPicture(Base, Image):
    __tablename__ = 'profilePictures'
    
    # Image Store
    store = store
    
    userId = Column(Integer, ForeignKey('users.id'), primary_key=True)
    user = relationship('Users')

class SLAdmin(Users):
    pass 



class SLClient(Users):
    companyName=Column(String,unique=False)
    # commercials  array commercials to do   
    # admins array admins to do   
    # clients array clients to do   
    # developpers array developpers to do   
    
class SLClientAdmin(Users):
    pass

class SLCClient(Users):
    pass

class SLCCommercial(Users):
    pass 

class SLCDevelopper(Users):
    pass 




functionalities_licenses_correspondance = Table(
    "functionalities_licenses",
    Base.metadata,
    Column("slccfunctionality_id", ForeignKey("slccfunctionality.id"), primary_key=True),
    Column("slcclicense_id", ForeignKey("slcclicense.id"), primary_key=True)
)


machines_licenses_correspondance = Table(
    "machines_licenses",
    Base.metadata,
    Column("slccmachine_id", ForeignKey("slccmachine.id"), primary_key=True),
    Column("slcclicense_id", ForeignKey("slcclicense.id"), primary_key=True)
)



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
    

class SLCCLicense(Base):
    __tablename__='slcclicense'

    id=Column(Integer,primary_key=True,index=True)
    name=Column(String,unique=False)
    consumptionType=Column(SQLAlchemyEnum(LicenseConsumptionType), default=LicenseConsumptionType.basic)
    numberOfUseLeft=Column(String,unique=False)
    maxLicense=Column(String,unique=False)
    # commercials  array commercials to do  
    #client  commercials  array client to do 
    application =Column(Integer,ForeignKey('slccapplication.id'))

    functionalities = relationship("SLCCFunctionality",secondary=functionalities_licenses_correspondance,back_populates='licenses')
    machines=relationship("SLCCMachine",secondary=machines_licenses_correspondance,back_populates='licenses')  


class SLCCFunctionality(Base):
    __tablename__='slccfunctionality'

    id=Column(Integer,primary_key=True,index=True)
    name=Column(String,unique=False)
    applicationId=Column(Integer,ForeignKey('slccapplication.id'))

    licenses = relationship("SLCCLicense",secondary=functionalities_licenses_correspondance,back_populates='functionalities')
    application=relationship("SLCCApplication", backref="slccfunctionality")


class SLCCApplication(Base):
    __tablename__="slccapplication"

    id=Column(Integer,primary_key=True,index=True)
    name=Column(String,unique=False)
    licenceCheckingPeriod=Column(Integer,unique=False)



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




