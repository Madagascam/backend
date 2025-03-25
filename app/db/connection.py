from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core import Base


async def initialize_database(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def async_get_sql_sessionmaker(database_string: str = "sqlite+aiosqlite:///:memory:") -> async_sessionmaker:
    engine = create_async_engine(database_string)
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    return session_maker


def get_sql_sessionmaker(database_string: str = "sqlite+aiosqlite:///test.db") -> async_sessionmaker:
    engine = create_async_engine(database_string)
    # asyncio.run(initialize_database(engine))
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    return session_maker
