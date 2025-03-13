from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlmodel import SQLModel

async def initialize_database(engine):
    SQLModel.metadata.create_all(engine)


def get_sql_sessionmaker(database_string: str = "sqlite:///test.db") -> async_sessionmaker:
    engine = create_async_engine(database_string, echo_property=True)
    initialize_database(engine)

    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)

    return session_maker
