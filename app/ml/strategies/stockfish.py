from typing import List, Tuple

from .abstract_strategy import AbstractAnalysisStrategy


class StockfishStrategy(AbstractAnalysisStrategy):

    async def analyze(self, pgn_data: str) -> List[Tuple[str, str]]:
        pass
