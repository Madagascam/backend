from typing import List, Tuple

from app.analysis import AbstractAnalysisStrategy


class ProjectAIStrategy(AbstractAnalysisStrategy):
    async def analyze(self, pgn_data: str) -> List[Tuple[str, str]]:
        pass
