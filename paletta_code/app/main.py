from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import os
from .models import User
from .database import SessionLocal, engine, Base 
from passlib.context import CryptContext
from pydantic import BaseModel, Field, EmailStr, constr
from enum import Enum

# creates the FastAPI app
app = FastAPI(
    title="Paletta FastAPI Web Application",
    description="A demo web application for the Paletta project using FastAPI",
    version="1.0.0"
)
# creates the tables in the database, only creates if they don't exist
Base.metadata.create_all(bind=engine)
# provides a db session for the application to interact with the db
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        # closes the db session - avoid memory leaks
        db.close()

# render dynamic html templates
templates = Jinja2Templates(directory="templates")

# creates the static path
static_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static")

# mounts the static files directory to the app
app.mount("/static", StaticFiles(directory=static_path), name="static")

# renders the homepage template
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# creates a password context for hashing and verifying passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# hashing the password, using bcrypt
def hash_password(password: str) -> str:
    return pwd_context.hash(password)
# verifying the password, using bcrypt
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# defines the user roles
class UserRole(str, Enum):
    customer = "customer"
    contributor = "contributor"
    admin = "admin"


# defines the user creation schema, BaseModel automatically validates the JSON request parsing
class UserCreate(BaseModel): 
    email: EmailStr
    # password is required, min length of 12
    password: str = Field(..., min_length=12)
    username: str = Field(..., min_length=3, max_length=50) # username is required
    institution: str | None = None # institution is optional
    company: str | None = None # company is optional
    role: str = UserRole.customer  # default role is customer

# creates a user
@app.post("/users/")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    print(f"User created: {user.email}")
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

# reads all users
@app.get("/users/") 
def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    users = db.query(User).offset(skip).limit(limit).all()
    return users

# defines the login request schema, BaseModel automatically validates the JSON request parsing
class LoginRequest(BaseModel):
    email: str
    password: str
# logs in a user
@app.post("/login/")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    return {"message": "Login successful"} # API response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("paletta_code.app.main:app", host="127.0.0.1", port=8000, reload=True)
