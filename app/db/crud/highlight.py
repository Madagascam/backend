from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import Highlight
from app.db import SQLAlchemyRepository


class HighlightRepository(SQLAlchemyRepository[Highlight]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Highlight)

    async def get(self, highlight_id: int) -> Optional[Highlight]:
        statement = select(Highlight).where(Highlight.id == highlight_id).options(
            selectinload(Highlight.game),
            selectinload(Highlight.video_segment)
        )
        result = await self.session.execute(statement)
        return result.scalars().first()

    async def get_all(self, **filters) -> Sequence[Highlight]:
        statement = select(Highlight).options(
            selectinload(Highlight.game),
            selectinload(Highlight.video_segment)
        )

        statement = await super().apply_filters(statement, **filters)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def get_by_game_id(self, game_id: int) -> Sequence[Highlight]:
        statement = select(Highlight).where(Highlight.game_id == game_id).options(
            selectinload(Highlight.video_segment)
        )
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def get_by_importance_score(self, min_score: float = 0.0) -> Sequence[Highlight]:
        statement = select(Highlight).where(Highlight.importance_score >= min_score).options(
            selectinload(Highlight.game),
            selectinload(Highlight.video_segment)
        )
        result = await self.session.execute(statement)
        return result.scalars().all()
