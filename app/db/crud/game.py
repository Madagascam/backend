from datetime import datetime
from typing import List, Optional, Sequence

from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app import Game
from app.db import SQLModelRepository


class GameRepository(SQLModelRepository[Game]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Game)

    async def get(self, id: int) -> Optional[Game]:
        statement = select(Game).where(Game.id == id).options(
            selectinload(Game.user),
            selectinload(Game.highlights),
            selectinload(Game.video),
            selectinload(Game.tasks)
        )
        result = await self.session.exec(statement)
        return result.first()

    async def get_all(self, **filters) -> Sequence[Game]:
        statement = select(Game).options(
            selectinload(Game.user),
            selectinload(Game.highlights),
            selectinload(Game.video),
            selectinload(Game.tasks)
        )

        statement = await super().apply_filters(statement, **filters)
        result = await self.session.exec(statement)
        return result.all()

    async def get_by_user_id(self, user_id: int) -> List[Game]:
        statement = select(Game).where(Game.user_id == user_id).options(
            selectinload(Game.highlights),
            selectinload(Game.video),
            selectinload(Game.tasks)
        )
        result = await self.session.exec(statement)
        return result.all()

    async def get_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Game]:
        statement = select(Game).where(
            Game.date >= start_date,
            Game.date <= end_date
        ).options(
            selectinload(Game.user),
            selectinload(Game.highlights),
            selectinload(Game.video),
            selectinload(Game.tasks)
        )
        result = await self.session.exec(statement)
        return result.all()
