from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, EmailStr
from enum import Enum
from .database import get_db
from .models import User
from .dependencies import get_current_user 
from .authentication import hash_password

# initialise Router
user_router = APIRouter()

# user roles
class UserRole(str, Enum):
    customer = "customer"
    contributor = "contributor"
    admin = "admin"

# user creation schema
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=12)
    username: str = Field(..., min_length=3, max_length=50)
    institution: str | None = None
    company: str | None = None
    role: UserRole = UserRole.customer

def get_user(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

@user_router.post("/")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    if get_user(db, user.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = hash_password(user.password)
    db_user = User(
        email=user.email,
        password_hash=hashed_password,
        username=user.username,
        institution=user.institution,
        company=user.company,
        role=user.role,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@user_router.get("/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@user_router.put("/me")
async def update_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    email: EmailStr = Body(...),
    username: str = Body(...),
    institution: str = Body(...)
):
    current_user.email = email
    current_user.username = username
    current_user.institution = institution
    db.commit()
    db.refresh(current_user)
    return current_user
