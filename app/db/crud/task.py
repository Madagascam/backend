from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import Task, TaskStatus, TaskType
from app.db import SQLAlchemyRepository


class TaskRepository(SQLAlchemyRepository[Task]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Task)

    async def get(self, task_id: int) -> Optional[Task]:
        statement = select(Task).where(Task.id == task_id).options(
            selectinload(Task.game),
            selectinload(Task.user)
        )
        result = await self.session.execute(statement)
        return result.scalars().first()

    async def get_all(self, **filters) -> Sequence[Task]:
        statement = select(Task).options(
            selectinload(Task.game),
            selectinload(Task.user)
        )

        statement = await super().apply_filters(statement, **filters)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def get_by_status(self, status: TaskStatus) -> Sequence[Task]:
        statement = select(Task).where(Task.status == status).options(
            selectinload(Task.game),
            selectinload(Task.user)
        )
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def get_by_type(self, task_type: TaskType) -> Sequence[Task]:
        statement = select(Task).where(Task.type == task_type).options(
            selectinload(Task.game),
            selectinload(Task.user)
        )
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def get_by_user_id(self, user_id: int) -> Sequence[Task]:
        statement = select(Task).where(Task.user_id == user_id).options(
            selectinload(Task.game)
        )
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def get_by_game_id(self, game_id: int) -> Sequence[Task]:
        statement = select(Task).where(Task.game_id == game_id).options(
            selectinload(Task.user)
        )
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def get_pending_tasks(self) -> Sequence[Task]:
        return await self.get_by_status(TaskStatus.PENDING)

    async def get_processing_tasks(self) -> Sequence[Task]:
        return await self.get_by_status(TaskStatus.PROCESSING)

    async def get_completed_tasks(self) -> Sequence[Task]:
        return await self.get_by_status(TaskStatus.COMPLETED)

    async def get_failed_tasks(self) -> Sequence[Task]:
        return await self.get_by_status(TaskStatus.FAILED)
