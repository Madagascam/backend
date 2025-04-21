from enum import Enum
from typing import List, Tuple

from app.analysis import *
from app.config import settings
from .chess_analyzer import ChessAnalyzer


class StrategyType(str, Enum):
    ANALYTICS = "analytics"
    PROJECT_AI = "project_ai"
    THIRD_PARTY_AI = "third_party_ai"
    MOCK = "mock"


class ChessAnalysisInterface:

    def __init__(self):
        self.analyzer = ChessAnalyzer()
        self.available_strategies = {
            StrategyType.THIRD_PARTY_AI: ThirdPartyAIStrategy(),
            StrategyType.PROJECT_AI: ProjectAIStrategy(),
            StrategyType.ANALYTICS: AnalyticsStrategy(),
            StrategyType.MOCK: FakeStrategy()
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
