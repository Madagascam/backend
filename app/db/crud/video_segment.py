from typing import List, Optional, Sequence

from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app import VideoSegment
from app.db import SQLModelRepository


class VideoSegmentRepository(SQLModelRepository[VideoSegment]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, VideoSegment)

    async def get(self, id: int) -> Optional[VideoSegment]:
        statement = select(VideoSegment).where(VideoSegment.id == id).options(
            selectinload(VideoSegment.video),
            selectinload(VideoSegment.highlight)
        )
        result = await self.session.exec(statement)
        return result.first()

    async def get_all(self, **filters) -> Sequence[VideoSegment]:
        statement = select(VideoSegment).options(
            selectinload(VideoSegment.video),
            selectinload(VideoSegment.highlight)
        )

        statement = await super().apply_filters(statement, **filters)
        result = await self.session.exec(statement)
        return result.all()

    async def get_by_video_id(self, video_id: int) -> List[VideoSegment]:
        statement = select(VideoSegment).where(VideoSegment.video_id == video_id).options(
            selectinload(VideoSegment.highlight)
        ).order_by(VideoSegment.sequence_order)
        result = await self.session.exec(statement)
        return result.all()

    async def get_by_highlight_id(self, highlight_id: int) -> Optional[VideoSegment]:
        statement = select(VideoSegment).where(VideoSegment.highlight_id == highlight_id).options(
            selectinload(VideoSegment.video)
        )
        result = await self.session.exec(statement)
        return result.first()
