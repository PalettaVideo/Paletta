from sqlalchemy import Column, Integer, String, Enum, DateTime
from .database import Base
from datetime import datetime

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, nullable=False)
    institution = Column(String(50))
    role = Column(String(20), nullable=False, default="user")
    username = Column(String(20))
    password_hash = Column(String(250), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

