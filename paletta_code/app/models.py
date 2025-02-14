from sqlalchemy import Column, Integer, String, Enum, DateTime
from .database import Base
from datetime import datetime
import enum

# defines the user roles to be used in the database, matches the UserRole enum in Pydantic
class UserRoleEnum(str, enum.Enum):
    admin = "admin"
    contributor = "contributor"
    customer = "customer"

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
