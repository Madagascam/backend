from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app import User, UserRole
from app.db import get_sql_sessionmaker, SQLAlchemyUnitOfWork
from app.utils import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_uow(session_factory=Depends(get_sql_sessionmaker)):
    async with SQLAlchemyUnitOfWork(session_factory) as uow:
        yield uow


async def get_current_user(
        token: str = Depends(oauth2_scheme),
        uow: SQLAlchemyUnitOfWork = Depends(get_uow)
) -> User:
    """Gets the current user based on the JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_data = decode_token(token)
    if token_data is None:
        raise credentials_exception

    user = await uow.user.get_by_username(token_data.username)
    if user is None:
        raise credentials_exception

    return user


async def get_current_admin_user(
        current_user: User = Depends(get_current_user),
) -> User:
    """Verifies the user is an admin"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    return current_user
