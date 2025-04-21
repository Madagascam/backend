import asyncio

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.config import settings
from app.core import Base


async def initialize_database(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def get_sql_sessionmaker() -> async_sessionmaker:
    engine = create_async_engine(settings.database.connection_string)

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(initialize_database(engine))
        else:
            loop.run_until_complete(initialize_database(engine))
    except RuntimeError:
        asyncio.run(initialize_database(engine))

    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    return session_maker
