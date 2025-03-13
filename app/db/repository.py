from abc import ABC, abstractmethod
from typing import Generic, List, Optional, TypeVar, Type, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

T = TypeVar('T')
S = TypeVar('S', bound=DeclarativeBase)


class AbstractRepository(Generic[T], ABC):
    @abstractmethod
    async def create(self, obj: T) -> T:
        raise NotImplementedError

    @abstractmethod
    async def get(self, id: int) -> Optional[T]:
        raise NotImplementedError

    @abstractmethod
    async def get_all(self, **filters) -> List[T]:
        raise NotImplementedError

    @abstractmethod
    async def update(self, obj: T) -> T:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, id: int) -> None:
        raise NotImplementedError


class SQLAlchemyRepository(AbstractRepository[S], Generic[S]):
    def __init__(self, session: AsyncSession, model_class: Type[S]):
        self.session = session
        self.model_class = model_class

    async def apply_filters(self, statement, **filters):
        for attr, value in filters.items():
            if hasattr(self.model_class, attr):
                statement = statement.where(getattr(self.model_class, attr) == value)
        return statement

    async def create(self, obj: S) -> S:
        self.session.add(obj)
        await self.session.flush()

        return obj

    async def get(self, id: int) -> Optional[S]:
        return await self.session.get(self.model_class, id)

    async def get_all(self, **filters) -> Sequence[S]:
        statement = select(self.model_class)

        statement = await self.apply_filters(statement, **filters)

        result = await self.session.execute(statement)
        return result.scalars().all()

    async def update(self, obj: S) -> S:
        self.session.add(obj)

        return obj

    async def delete(self, id: int) -> None:
        obj = await self.get(id)
        if obj:
            await self.session.delete(obj)
