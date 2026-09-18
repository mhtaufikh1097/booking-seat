from collections.abc import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id = int(str(payload["sub"]))
    except (ValueError, TypeError, KeyError, RuntimeError) as error:
        raise credentials_error from error

    user = db.scalar(select(User).options(joinedload(User.role)).where(User.id == user_id))
    if user is None or user.status != "active":
        raise credentials_error
    return user


def require_role(*allowed_roles: str):
    allowed = {role.casefold() for role in allowed_roles}

    def role_dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.name.casefold() not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role permissions")
        return current_user

    return role_dependency