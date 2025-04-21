from database import Base
from sqlalchemy import ForeignKey,Column,Integer,String,Date,Boolean, Enum as SQLAlchemyEnum
from sqlalchemy_imageattach.entity import Image, image_attachment
from sqlalchemy.orm import relationship




from enum import Enum

class UserTypeEnum(str, Enum):
    basic="basic"
    sladmin = "sladmin"
    slclient = "slclient"
    slclientadmin = "slclientadmin"
    slcclient = "slcclient"
    slccommercial = "slccommercial"
    slcdevelopper = "slcdevelopper"


class Users(Base):
    __tablename__='users'

    id=Column(Integer,primary_key=True,index=True)
    username=Column(String,unique=True)
    name=Column(String,unique=False)
    surname=Column(String,unique=False)
    hashedPassword=Column(String,unique=False)
    creationDate=Column(Date,unique=False)
    profilePicture=image_attachment('UserPicture')
    userType=Column(SQLAlchemyEnum(UserTypeEnum), default=UserTypeEnum.basic)


class UserPicture(Base, Image):
    __tablename__ = 'profilePictures'

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


class SLCCMachine(Base):
    __tablename__='slccmachine'

    id=Column(Integer,primary_key=True,index=True)
    macAddress=Column(String,unique=False)
    cpuId=Column(String,unique=False)
    hasLicenseActivated=Column(Boolean,unique=False)
    licenseUsed=Column(String,ForeignKey('licence.id'))
    lastVerificationPassed=Column(Date,unique=False)
    lastVerificationTry=Column(Date,unique=False)



class LicenseConsumptionType(str, Enum):
    basic="basic"
    

class SLCCLicense:
    __tablename__='slcclicense'

    id=Column(Integer,primary_key=True,index=True)
    name=Column(String,unique=False)
    consumptionType==Column(SQLAlchemyEnum(LicenseConsumptionType), default=LicenseConsumptionType.basic)
    numberOfUseLeft=Column(String,unique=False)
    maxLicense=Column(String,unique=False)
    #machineList array licence to do   
    #commercial  array Commerical to do   
    client =Column(String,ForeignKey('users.id'))
    application =Column(String,ForeignKey('slccapplication.id'))
    #functionnality array Functionnality to do 


class SLCCFunctionality:
    __tablename__='slccfunctionality'

    id=Column(Integer,primary_key=True,index=True)
    name=Column(String,unique=False)
    application=Column(String,ForeignKey('slccapplication.id'))


class SLCCApplication: 
    __tablename__="slccapplication"

    id=Column(Integer,primary_key=True,index=True)
    name=Column(String,unique=False)
    licenceCheckingPeriod=Column(Integer,unique=False)
    #functionnality array Functionnality to do 