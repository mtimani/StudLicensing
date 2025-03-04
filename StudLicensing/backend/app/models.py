from database import Base
from sqlalchemy import ForeignKey,Column,Integer,String,Date
from sqlalchemy_imageattach.entity import Image, image_attachment
from sqlalchemy.orm import relationship



class Users(Base):
    __tablename__='users'

    id=Column(Integer,primary_key=True,index=True)
    username=Column(String,unique=True)
    name=Column(String,unique=False)
    surname=Column(String,unique=False)
    hashedPassword=Column(String,unique=False)
    creationDate=Column(Date,unique=False)
    profilePicture=image_attachment('UserPicture')



class UserPicture(Base, Image):
    __tablename__ = 'profilePictures'

    userId = Column(Integer, ForeignKey('users.id'), primary_key=True)
    user = relationship('Users')


