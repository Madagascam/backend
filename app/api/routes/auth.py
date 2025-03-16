from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm

from app import User
from app.core.DTO import UserCreateSchema, TokenSchema
from app.db import SQLAlchemyUnitOfWork
from app.utils import verify_password, create_access_token, get_password_hash
from ..dependencies import get_uow

router = APIRouter(tags=["authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
        user_data: Annotated[UserCreateSchema, Body()],
        uow: Annotated[SQLAlchemyUnitOfWork, Depends(get_uow)]
):
    # Check if username exists
    existing_user = await uow.user.get_by_username(user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        password_hash=hashed_password
    )
    user = await uow.user.create(new_user)
    await uow.commit()

    # Return user info (without password)
    return {
        "id": user.id,
        "username": user.username,
        "role": user.role
    }


@router.post("/token", response_model=TokenSchema)
async def login_for_access_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        uow: Annotated[SQLAlchemyUnitOfWork, Depends(get_uow)]
):
    user = await uow.user.get_by_username(form_data.username)

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token = create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "role": user.role
        }
    )

    return {"access_token": access_token, "token_type": "bearer"}
