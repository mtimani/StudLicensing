from database import Base
from sqlalchemy import ForeignKey, Column, Integer, String, Date, Boolean
from sqlalchemy_imageattach.entity import Image, image_attachment
from sqlalchemy.orm import relationship
from sqlalchemy_imageattach.stores.fs import FileSystemStore

# Store for profile images
store = FileSystemStore(
    path="/uploads",
    base_url="http://localhost:8000/uploads/"
)

class Users(Base):
    __tablename__='users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    name = Column(String, nullable=False)
    surname = Column(String, nullable=False)
    hashedPassword = Column(String, nullable=False)
    creationDate = Column(Date, nullable=False)
    activated = Column(Boolean, default=False, nullable=False)
    profilePicture = image_attachment('UserPicture')



class UserPicture(Base, Image):
    __tablename__ = 'profilePictures'
    
    # Image Store
    store = store
    
    userId = Column(Integer, ForeignKey('users.id'), primary_key=True)
    user = relationship('Users')


