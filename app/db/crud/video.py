from typing import List, Optional, Sequence

from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app import Video
from app.db import SQLModelRepository


class VideoRepository(SQLModelRepository[Video]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Video)

    async def get(self, id: int) -> Optional[Video]:
        statement = select(Video).where(Video.id == id).options(
            selectinload(Video.game),
            selectinload(Video.segments)
        )
        result = await self.session.exec(statement)
        return result.first()

    async def get_all(self, **filters) -> Sequence[Video]:
        statement = select(Video).options(
            selectinload(Video.game),
            selectinload(Video.segments)
        )

        statement = await super().apply_filters(statement, **filters)
        result = await self.session.exec(statement)
        return result.all()

    async def get_by_game_id(self, game_id: int) -> Optional[Video]:
        statement = select(Video).where(Video.game_id == game_id).options(
            selectinload(Video.segments)
        )
        result = await self.session.exec(statement)
        return result.first()

    async def get_by_status(self, status: str) -> List[Video]:
        statement = select(Video).where(Video.status == status).options(
            selectinload(Video.game),
            selectinload(Video.segments)
        )
        result = await self.session.exec(statement)
        return result.all()
