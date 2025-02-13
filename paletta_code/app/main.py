from fastapi import FastAPI, Request, Depends, HTTPException, status, Body
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import os
from .models import User
from .database import SessionLocal, engine, Base 
from passlib.context import CryptContext
from pydantic import BaseModel, Field, EmailStr
from enum import Enum
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
import jwt
import logging
from sqlalchemy.exc import SQLAlchemyError


# configuration, secret key for JWT, algorithm for JWT, and access token expire minutes
# TODO: move to environment variables in production
SECRET_KEY = "962598fab9d6a9ad1947c5097db78436fe941ac066c7a071bbe8cbf674fb226f"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 90

# initialise FastAPI app
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

# Logging Configuration
logging.basicConfig(level=logging.INFO)

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# creates a password context for hashing and verifying passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# hashing the password, using bcrypt
def hash_password(password: str) -> str:
    return pwd_context.hash(password)
# verifying the password, using bcrypt
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# create access token to authenticate user
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# get user from database
def get_user(db: Session, email: str):
    try:
        user = db.query(User).filter(User.email == email).first()
        logging.info(f"User found: {user.email}" if user else "User not found")
        return user
    except SQLAlchemyError as e:
        logging.error(f"Database error: {e}")
        return None

# authenticate user
def authenticate_user(db: Session, email: str, password: str):
    user = get_user(db, email)
    if user and verify_password(password, user.password_hash):
        return user
    return None

# login endpoint to get token
@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    logging.info("login_for_access_token called")
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    
    # log the generated token for debugging
    logging.info(f"Generated token: {access_token}")
    
    return {"access_token": access_token, "token_type": "bearer"}

# configure logging
logging.basicConfig(level=logging.INFO)
# get current user from token
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        logging.info(f"Decoded email from token: {email}")  # Debugging: Log the email
        if email is None:
            raise credentials_exception
    except jwt.PyJWTError as e:
        logging.error(f"JWT Error: {e}")  # Debugging: Log JWT errors
        raise credentials_exception
    user = get_user(db, email=email)
    if user is None:
        logging.error("User not found")  # Debugging: Log if user is not found
        raise credentials_exception
    return user

# endpoint to get current user
@app.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

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
def create_user_endpoint(user: UserCreate, db: Session = Depends(get_db)):
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

# endpoint to get all users for testing purposes
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

# renders the login page template
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Update user profile
@app.put("/users/me")
async def update_user_profile_endpoint(
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("paletta_code.app.main:app", host="127.0.0.1", port=8000, reload=True)
