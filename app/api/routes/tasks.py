from typing import Annotated

from fastapi import APIRouter, Path, Depends, HTTPException
from starlette import status

from app import User
from app.api.dependencies import get_uow, get_current_user
from app.core.DTO import TaskStatusResponseSchema
from app.db import SQLAlchemyUnitOfWork

router = APIRouter(tags=["Tasks"], prefix="/api/tasks")


@router.get("/status/{task_id}",
            response_model=TaskStatusResponseSchema,
            summary="Check task status by ID")
async def get_task_status(
        task_id: Annotated[int, Path(title='ID задачи для проверки')],
        uow: Annotated[SQLAlchemyUnitOfWork, Depends(get_uow)],
        current_user: Annotated[User, Depends(get_current_user)]
):
    task = await uow.task.get(task_id)

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")

    if task.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к этой задаче")

    return task
