from abc import ABC, abstractmethod
from typing import List, Tuple


class AbstractAnalysisStrategy(ABC):

    @abstractmethod
    async def analyze(self, pgn_data: str) -> List[Tuple[str, str]]:
        raise NotImplementedError


