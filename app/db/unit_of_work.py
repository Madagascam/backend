from abc import ABC, abstractmethod
from typing import AsyncContextManager, Optional, Type, Any

from sqlalchemy.ext.asyncio import async_sessionmaker

from .crud import *


class AbstractUnitOfWork(AsyncContextManager, ABC):
    user: UserRepository
    game: GameRepository
    highlight: HighlightRepository
    video: VideoRepository
    video_segment: VideoSegmentRepository
    task: TaskRepository

    @abstractmethod
    async def __aenter__(self):
        raise NotImplementedError

    async def __aexit__(self, exc_type: Optional[Type[BaseException]],
                        exc_val: Optional[BaseException],
                        exc_tb: Optional[Any]) -> Optional[bool]:
        raise NotImplementedError

    @abstractmethod
    async def commit(self):
        raise NotImplementedError

    @abstractmethod
    async def rollback(self):
        raise NotImplementedError


class SQLAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self, session_factory: async_sessionmaker):
        self.session_factory = session_factory

    async def __aenter__(self):
        self.session = self.session_factory()

        # Initialize repositories with the active session
        self.user = UserRepository(self.session)
        self.game = GameRepository(self.session)
        self.highlight = HighlightRepository(self.session)
        self.video = VideoRepository(self.session)
        self.video_segment = VideoSegmentRepository(self.session)
        self.task = TaskRepository(self.session)

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # If there's an exception during the transaction, rollback
        if exc_type:
            await self.rollback()

        # Always close the session, regardless of success or failure
        await self.session.close()

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()
        self.session.expire_all()
