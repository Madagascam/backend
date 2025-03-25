from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import VideoSegment
from app.db import SQLAlchemyRepository


class VideoSegmentRepository(SQLAlchemyRepository[VideoSegment]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, VideoSegment)

    async def get(self, video_segment_id: int) -> Optional[VideoSegment]:
        statement = select(VideoSegment).where(VideoSegment.id == video_segment_id).options(
            selectinload(VideoSegment.video),
            selectinload(VideoSegment.highlight)
        )
        result = await self.session.execute(statement)
        return result.scalars().first()

    async def get_all(self, **filters) -> Sequence[VideoSegment]:
        statement = select(VideoSegment).options(
            selectinload(VideoSegment.video),
            selectinload(VideoSegment.highlight)
        )

        statement = await super().apply_filters(statement, **filters)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def get_by_video_id(self, video_id: int) -> Sequence[VideoSegment]:
        statement = select(VideoSegment).where(VideoSegment.video_id == video_id).options(
            selectinload(VideoSegment.highlight)
        ).order_by(VideoSegment.sequence_order)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def get_by_highlight_id(self, highlight_id: int) -> Optional[VideoSegment]:
        statement = select(VideoSegment).where(VideoSegment.highlight_id == highlight_id).options(
            selectinload(VideoSegment.video)
        )
        result = await self.session.execute(statement)
        return result.scalars().first()
