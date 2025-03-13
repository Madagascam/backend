from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import Video
from app.db import SQLAlchemyRepository


class VideoRepository(SQLAlchemyRepository[Video]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Video)

    async def get(self, video_id: int) -> Optional[Video]:
        statement = select(Video).where(Video.id == video_id).options(
            selectinload(Video.game),
            selectinload(Video.segments)
        )
        result = await self.session.execute(statement)
        return result.scalars().first()

    async def get_all(self, **filters) -> Sequence[Video]:
        statement = select(Video).options(
            selectinload(Video.game),
            selectinload(Video.segments)
        )

        statement = await super().apply_filters(statement, **filters)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def get_by_game_id(self, game_id: int) -> Optional[Video]:
        statement = select(Video).where(Video.game_id == game_id).options(
            selectinload(Video.segments)
        )
        result = await self.session.execute(statement)
        return result.scalars().first()

    async def get_by_status(self, status: str) -> Sequence[Video]:
        statement = select(Video).where(Video.status == status).options(
            selectinload(Video.game),
            selectinload(Video.segments)
        )
        result = await self.session.execute(statement)
        return result.scalars().all()
