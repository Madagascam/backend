# repositories/task_repository.py
from typing import List, Optional, Sequence

from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from app import Task, TaskStatus, TaskType
from app.db import SQLModelRepository


class TaskRepository(SQLModelRepository[Task]):
    def __init__(self, session: Session):
        super().__init__(session, Task)

    async def get(self, id: int) -> Optional[Task]:
        statement = select(Task).where(Task.id == id).options(
            selectinload(Task.game),
            selectinload(Task.user)
        )
        result = await self.session.exec(statement)
        return result.first()

    async def get_all(self, **filters) -> Sequence[Task]:
        statement = select(Task).options(
            selectinload(Task.game),
            selectinload(Task.user)
        )

        statement = await super().apply_filters(statement, **filters)
        result = await self.session.exec(statement)
        return result.all()

    async def get_by_status(self, status: TaskStatus) -> List[Task]:
        statement = select(Task).where(Task.status == status).options(
            selectinload(Task.game),
            selectinload(Task.user)
        )
        result = await self.session.exec(statement)
        return result.all()

    async def get_by_type(self, type: TaskType) -> List[Task]:
        statement = select(Task).where(Task.type == type).options(
            selectinload(Task.game),
            selectinload(Task.user)
        )
        result = await self.session.exec(statement)
        return result.all()

    async def get_by_user_id(self, user_id: int) -> List[Task]:
        statement = select(Task).where(Task.user_id == user_id).options(
            selectinload(Task.game)
        )
        result = await self.session.exec(statement)
        return result.all()

    async def get_by_game_id(self, game_id: int) -> List[Task]:
        statement = select(Task).where(Task.game_id == game_id).options(
            selectinload(Task.user)
        )
        result = await self.session.exec(statement)
        return result.all()

    async def get_pending_tasks(self) -> List[Task]:
        return await self.get_by_status(TaskStatus.PENDING)

    async def get_processing_tasks(self) -> List[Task]:
        return await self.get_by_status(TaskStatus.PROCESSING)

    async def get_completed_tasks(self) -> List[Task]:
        return await self.get_by_status(TaskStatus.COMPLETED)

    async def get_failed_tasks(self) -> List[Task]:
        return await self.get_by_status(TaskStatus.FAILED)
