from typing import List, Optional, Sequence

from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app import Highlight
from app.db import SQLModelRepository


class HighlightRepository(SQLModelRepository[Highlight]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Highlight)

    async def get(self, id: int) -> Optional[Highlight]:
        statement = select(Highlight).where(Highlight.id == id).options(
            selectinload(Highlight.game),
            selectinload(Highlight.video_segment)
        )
        result = await self.session.exec(statement)
        return result.first()

    async def get_all(self, **filters) -> Sequence[Highlight]:
        statement = select(Highlight).options(
            selectinload(Highlight.game),
            selectinload(Highlight.video_segment)
        )

        statement = await super().apply_filters(statement, **filters)
        result = await self.session.exec(statement)
        return result.all()

    async def get_by_game_id(self, game_id: int) -> List[Highlight]:
        statement = select(Highlight).where(Highlight.game_id == game_id).options(
            selectinload(Highlight.video_segment)
        )
        result = await self.session.exec(statement)
        return result.all()

    async def get_by_importance_score(self, min_score: float = 0.0) -> List[Highlight]:
        statement = select(Highlight).where(Highlight.importance_score >= min_score).options(
            selectinload(Highlight.game),
            selectinload(Highlight.video_segment)
        )
        result = await self.session.exec(statement)
        return result.all()
