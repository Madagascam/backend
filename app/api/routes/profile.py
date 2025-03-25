from typing import Annotated

from fastapi import APIRouter, Depends, Body, HTTPException, status

from app import User, UserRole
from app.api.dependencies import get_current_user, get_uow
from app.core.DTO import UserUpdateSchema, UserResponseSchema
from app.db import SQLAlchemyUnitOfWork

router = APIRouter(
    prefix="/api/profile",
    tags=["Profile"]
)


@router.get("/",
            response_model=UserResponseSchema,
            status_code=status.HTTP_200_OK,
            summary="Get user profile")
async def get_profile(
        current_user: Annotated[User, Depends(get_current_user)]
):
    return UserResponseSchema.model_validate(current_user)


@router.patch("/",
              response_model=UserResponseSchema,
              status_code=status.HTTP_200_OK,
              summary="Update user profile")
async def update_profile(
        update_data: Annotated[UserUpdateSchema, Body()],
        current_user: Annotated[User, Depends(get_current_user)],
        uow: Annotated[SQLAlchemyUnitOfWork, Depends(get_uow)]
):
    user = await uow.user.get(current_user.id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if update_data.username is not None:
        user.username = update_data.username

    if update_data.password is not None:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        user.password_hash = pwd_context.hash(update_data.password)

    if update_data.role is not None and current_user.role == UserRole.ADMIN:
        user.role = update_data.role

    await uow.commit()

    # Return the updated user (excluding sensitive fields)
    return UserUpdateSchema.model_validate(user)
