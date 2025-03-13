from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.log import echo_property
from sqlmodel import SQLModel

async def initialize_database(engine):
    SQLModel.metadata.create_all(engine)


def get_sql_session_maker(database_string: str="sqlite:///test.db") -> async_sessionmaker:
    engine = create_async_engine(database_string, echo_property=True)
    initialize_database(engine)

    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    return session_maker
