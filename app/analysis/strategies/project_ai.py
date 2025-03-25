from typing import List, Tuple

from .abstract_strategy import AbstractAnalysisStrategy


class ProjectAIStrategy(AbstractAnalysisStrategy):

    async def analyze(self, pgn_data: str) -> List[Tuple[str, str]]:
        # Implementation will go here
        pass
