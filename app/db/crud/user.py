from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import User
from app.db import SQLAlchemyRepository


class UserRepository(SQLAlchemyRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def get_by_username(self, username: str) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalars().first()

    async def get(self, user_id: int) -> Optional[User]:
        statement = select(User).where(User.id == user_id).options(
            selectinload(User.games),
            selectinload(User.tasks)
        )
        result = await self.session.execute(statement)
        return result.scalars().first()

    async def get_all(self, **filters) -> Sequence[User]:
        statement = select(User).options(
            selectinload(User.games),
            selectinload(User.tasks)
        )

        statement = await super().apply_filters(statement, **filters)

        result = await self.session.execute(statement)
        return result.scalars().all()

    async def get_by_username(self, username: str) -> Optional[User]:
        statement = select(User).where(User.username == username).options(
            selectinload(User.games),
            selectinload(User.tasks)
        )
        result = await self.session.execute(statement)
        return result.scalars().first()
