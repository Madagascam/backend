from typing import Optional, Sequence

from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app import User
from app.db import SQLModelRepository


class UserRepository(SQLModelRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def get(self, id: int) -> Optional[User]:
        statement = select(User).where(User.id == id).options(
            selectinload(User.games),
            selectinload(User.tasks)
        )
        result = await self.session.exec(statement)
        return result.first()

    async def get_all(self, **filters) -> Sequence[User]:
        statement = select(User).options(
            selectinload(User.games),
            selectinload(User.tasks)
        )

        statement = await super().apply_filters(statement, **filters)
        result = await self.session.exec(statement)

        return result.all()

    async def get_by_username(self, username: str) -> Optional[User]:
        statement = select(User).where(User.username == username).options(
            selectinload(User.games),
            selectinload(User.tasks)
        )
        result = await self.session.exec(statement)
        return result.first()
