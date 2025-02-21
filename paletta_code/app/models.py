# this file defines the models for the database
from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime
import enum

# defines the user roles to be used in the database, matches the UserRole enum in Pydantic
class UserRoleEnum(str, enum.Enum):
    admin = "admin"
    contributor = "contributor"
    customer = "customer"

# defines the user model to be used in the database
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, nullable=False)
    institution = Column(String(50)) 
    company = Column(String(50), nullable=True)  # explicitly allows NULL
    role = Column(Enum(UserRoleEnum), nullable=False, default=UserRoleEnum.customer) 
    username = Column(String(20), nullable=False)  # matches Pydantic's required username
    password_hash = Column(String(250), nullable=False)
    created_at = Column(DateTime, default=datetime.now) 

    # Relationships
    videos = relationship("Video", back_populates="uploader")
    uploads = relationship("Upload", back_populates="uploader")

class Category(Base):
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(25), nullable=False)
    description = Column(String(200))
    
    # relationships
    videos = relationship("Video", back_populates="category")

class Video(Base):
    __tablename__ = 'video'
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(25), nullable=False)
    description = Column(String(250))
    category_id = Column(Integer, ForeignKey('categories.id'))
    uploader_id = Column(Integer, ForeignKey('users.id'))
    upload_date = Column(DateTime, default=datetime.now)
    
    # relationships
    category = relationship("Category", back_populates="videos")
    uploader = relationship("User", back_populates="videos")
    tags = relationship("Tag", secondary="video_tags", back_populates="videos")
    uploads = relationship("Upload", back_populates="video")

class Tag(Base):
    __tablename__ = 'tags'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(25))
    
    # relationships
    videos = relationship("Video", secondary="video_tags", back_populates="tags")

class VideoTags(Base):
    __tablename__ = 'video_tags'
    
    video_id = Column(Integer, ForeignKey('video.id'), primary_key=True)
    tag_id = Column(Integer, ForeignKey('tags.id'), primary_key=True)

class Upload(Base):
    __tablename__ = 'uploads'
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey('video.id'))
    uploader_id = Column(Integer, ForeignKey('users.id'))
    upload_date = Column(DateTime, default=datetime.now)
    # status of the upload
    # 0: pending
    # 1: processing
    # 2: completed
    # 3: failed
    # need to define a new enum for the status
        # how does the status get updated? how does the server-side know the status of the upload?
        # need to understand how the upload is processed and how the status is updated!
    status = Column(String)
    
    # relationships
    video = relationship("Video", back_populates="uploads")
    uploader = relationship("User", back_populates="uploads")

