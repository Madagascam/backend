from enum import Enum
from typing import Optional, List, Tuple

from app.analysis import *
from app.config import settings


class StrategyType(str, Enum):
    ANALYTICS = "analytics"
    PROJECT_AI = "project_ai"
    THIRD_PARTY_AI = "third_party_ai"
    MOCK = "mock"


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


class ChessAnalysisInterface:

    def __init__(self):
        self.analyzer = ChessAnalyzer()
        self.available_strategies = {
            StrategyType.THIRD_PARTY_AI: ThirdPartyAIStrategy(),
            StrategyType.PROJECT_AI: ProjectAIStrategy(),
            StrategyType.ANALYTICS: AnalyticsStrategy(),
            StrategyType.MOCK: MockStrategy()
        }
        self.current_strategy = None
        self.default_strategy = StrategyType(settings.analysis.default_strategy)

    def set_strategy(self, strategy_name: StrategyType) -> None:
        if strategy_name not in self.available_strategies:
            raise ValueError(f"Unknown strategy: {strategy_name}")

        self.current_strategy = strategy_name
        self.analyzer.strategy = self.available_strategies[strategy_name]

    async def analyze_game(self, game_data: str) -> List[Tuple[str, str]]:
        if self.current_strategy is None:
            self.set_strategy(self.default_strategy)

        return await self.analyzer.analyze_game(game_data)
