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
    password: str = Field(..., min_length=8)
    username: str = Field(..., min_length=3, max_length=50)
    institution: str | None = None
    company: str | None = None
    role: UserRole = UserRole.customer

# get the user by email from the database
def get_user(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

# create a new POST user server endpoint
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

# get the current user
@user_router.get("/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

# PUT request to update the user profile
@user_router.put("/me")
async def update_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    email: EmailStr = Body(...),
    username: str = Body(...),
    company: str = Body(...),
    password: str | None = Body(None)
):
    current_user.email = email
    current_user.username = username
    current_user.company = company

    # Check if a new password is provided and hash it
    if password:
        current_user.password_hash = hash_password(password)


    db.commit()
    db.refresh(current_user)
    return current_user
