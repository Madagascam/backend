from abc import ABC, abstractmethod
from typing import Generic, List, Optional, TypeVar, Type, Sequence

from sqlmodel import select, SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

T = TypeVar('T')
S = TypeVar('S', bound=SQLModel)


class AbstractRepository(Generic[T], ABC):
    @abstractmethod
    async def create(self, obj: T) -> T:
        pass

    @abstractmethod
    async def get(self, id: int) -> Optional[T]:
        pass

    @abstractmethod
    async def get_all(self, **filters) -> List[T]:
        pass

    @abstractmethod
    async def update(self, obj: T) -> T:
        pass

    @abstractmethod
    async def delete(self, id: int) -> None:
        pass


class SQLModelRepository(AbstractRepository[S], Generic[S]):
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

        await self.session.commit()
        await self.session.refresh(obj)

        return obj

    async def get(self, id: int) -> Optional[S]:
        return await self.session.get(self.model_class, id)

    async def get_all(self, **filters) -> Sequence[S]:
        statement = select(self.model_class)

        statement = await self.apply_filters(statement, **filters)

        result = await self.session.exec(statement)
        return result.all()

    async def update(self, obj: S) -> S:
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def delete(self, id: int) -> None:
        obj = self.get(id)
        if obj:
            await self.session.delete(obj)
            await self.session.commit()
