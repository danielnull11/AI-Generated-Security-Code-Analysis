import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, Request, status
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models import Admin

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
ALGORITHM = "HS256"
TOKEN_TTL_MINUTES = int(os.getenv("TOKEN_TTL_MINUTES", "720"))
COOKIE_NAME = "access_token"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(username: str) -> str:
    payload = {
        "sub": username,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=TOKEN_TTL_MINUTES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def authenticate_admin(db: Session, username: str, password: str) -> Admin | None:
    admin = db.scalar(select(Admin).where(Admin.username == username))
    if admin and verify_password(password, admin.hashed_password):
        return admin
    return None


def _token_from_request(request: Request) -> str | None:
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        return header.removeprefix("Bearer ").strip()
    return request.cookies.get(COOKIE_NAME)


def get_current_admin(
    request: Request, db: Session = Depends(get_db)
) -> Admin:
    """Resolve the admin from a JWT in the Authorization header or session cookie."""
    token = _token_from_request(request)
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_error

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        raise credentials_error

    username = payload.get("sub")
    if not username:
        raise credentials_error

    admin = db.scalar(select(Admin).where(Admin.username == username))
    if not admin:
        raise credentials_error
    return admin
