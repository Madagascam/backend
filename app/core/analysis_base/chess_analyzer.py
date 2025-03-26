from typing import Optional, List, Tuple

from .abstract_strategy import AbstractAnalysisStrategy


class ChessAnalyzer:
    def __init__(self, strategy: Optional[AbstractAnalysisStrategy] = None):
        self._strategy = strategy

    @property
    def strategy(self) -> Optional[AbstractAnalysisStrategy]:
        return self._strategy

    @strategy.setter
    def strategy(self, strategy: AbstractAnalysisStrategy) -> None:
        self._strategy = strategy

    async def analyze_game(self, game_data: str) -> List[Tuple[str, str]]:
        if self._strategy is None:
            raise ValueError("Analysis strategy not set")
        return await self._strategy.analyze(game_data)
