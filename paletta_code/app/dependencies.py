from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import jwt
import logging
from .database import get_db
from .models import User
from .config import SECRET_KEY, ALGORITHM  

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        logging.info(f"Decoded email from token: {email}")
        if email is None:
            raise credentials_exception
    except jwt.PyJWTError as e:
        logging.error(f"JWT Error: {e}")
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        logging.error("User not found")
        raise credentials_exception
    return user
