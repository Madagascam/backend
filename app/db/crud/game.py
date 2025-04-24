from datetime import datetime
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import Game, Highlight
from app.db import SQLAlchemyRepository


class GameRepository(SQLAlchemyRepository[Game]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Game)

    async def get(self, game_id: int) -> Optional[Game]:
        statement = select(Game).where(Game.id == game_id).options(
            selectinload(Game.user),
            selectinload(Game.highlights).selectinload(Highlight.video_segment),
            selectinload(Game.videos),
            selectinload(Game.tasks)
        )
        result = await self.session.execute(statement)
        return result.scalars().first()

    async def get_all(self, **filters) -> Sequence[Game]:
        statement = select(Game).options(
            selectinload(Game.user),
            selectinload(Game.highlights).selectinload(Highlight.video_segment),
            selectinload(Game.videos),
            selectinload(Game.tasks)
        )

        statement = await super().apply_filters(statement, **filters)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def get_by_user_id(self, user_id: int) -> Sequence[Game]:
        statement = select(Game).where(Game.user_id == user_id).options(
            selectinload(Game.highlights).selectinload(Highlight.video_segment),
            selectinload(Game.videos),
            selectinload(Game.tasks)
        )
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def get_by_date_range(self, start_date: datetime, end_date: datetime) -> Sequence[Game]:
        statement = select(Game).where(
            Game.date >= start_date,
            Game.date <= end_date
        ).options(
            selectinload(Game.user),
            selectinload(Game.highlights).selectinload(Highlight.video_segment),
            selectinload(Game.videos),
            selectinload(Game.tasks)
        )
        result = await self.session.execute(statement)
        return result.scalars().all()
