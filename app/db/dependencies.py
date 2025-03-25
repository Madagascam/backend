from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_sql_sessionmaker, SQLAlchemyUnitOfWork


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    session_factory = get_sql_sessionmaker()
    session = session_factory()
    try:
        yield session
    finally:
        await session.close()


async def get_unit_of_work(
        session: AsyncSession = Depends(get_async_session)
) -> AsyncGenerator[SQLAlchemyUnitOfWork, None]:
    # Create a session factory that will return our existing session
    def session_factory():
        return session

    uow = SQLAlchemyUnitOfWork(session_factory)
    async with uow:
        yield uow
