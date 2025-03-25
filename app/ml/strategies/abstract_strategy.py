from abc import ABC, abstractmethod
from typing import List, Tuple


class AbstractAnalysisStrategy(ABC):

    @abstractmethod
    async def analyze(self, pgn_data: str) -> List[Tuple[str, str]]:
        raise NotImplementedError


class MockStrategy(AbstractAnalysisStrategy):

    async def analyze(self, pgn_data: str) -> List[Tuple[str, str]]:
        return [("12B", "13W"), ("16W", "18B", "Test desc")]
