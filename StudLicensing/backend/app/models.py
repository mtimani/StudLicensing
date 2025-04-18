# ===========================================
# Imports
# ===========================================
from database import Base
from sqlalchemy import ForeignKey, Column, Integer, String, Date, Boolean, DateTime
from sqlalchemy_imageattach.entity import Image, image_attachment
from sqlalchemy.orm import relationship
from sqlalchemy_imageattach.stores.fs import FileSystemStore
from datetime import datetime



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

# Global Users class
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

# User Profile Pictures class
class UserPicture(Base, Image):
    __tablename__ = 'profilePictures'
    
    # Image Store
    store = store
    
    userId = Column(Integer, ForeignKey('users.id'), primary_key=True)
    user = relationship('Users')

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