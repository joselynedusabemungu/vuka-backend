import os
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_db
from vuka.models.registration import Registration

SECRET_KEY = os.getenv("JWT_SECRET_KEY") or os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM") or os.getenv("ALGORITHM", "HS256")
if not SECRET_KEY or len(SECRET_KEY) < 32 or SECRET_KEY in {"your_secret_key_here", "change_me_in_production"}:
    raise RuntimeError("A strong JWT_SECRET_KEY must be configured")

bearer_scheme = HTTPBearer(auto_error=True)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)) -> Registration:
    exc = HTTPException(status_code=401, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM], options={"require": ["sub", "exp", "iat", "token_type"]})
        if payload.get("token_type") != "access": raise exc
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, ValueError, TypeError, KeyError):
        raise exc
    user = db.get(Registration, user_id)
    if not user or not user.is_active:
        raise exc
    return user


def require_role(*roles):
    def dependency(current_user: Registration = Depends(get_current_user)):
        if current_user.user_type not in roles:
            raise HTTPException(status_code=403, detail="Insufficient privileges")
        return current_user
    return dependency


def require_admin(current_user: Registration = Depends(get_current_user)) -> Registration:
    if current_user.user_type != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current_user


def require_verifier(current_user: Registration = Depends(get_current_user)) -> Registration:
    if current_user.user_type not in {"admin", "verifier"}:
        raise HTTPException(status_code=403, detail="Verifier privileges required")
    return current_user


def require_self(user_id: int, current_user: Registration = Depends(get_current_user)) -> Registration:
    if current_user.user_type != "admin" and current_user.user_id != user_id:
        raise HTTPException(status_code=403, detail="You are not allowed to access this account")
    return current_user
