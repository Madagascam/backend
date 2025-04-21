from typing import List, Tuple

from app.core.analysis_base import AbstractAnalysisStrategy


class FakeStrategy(AbstractAnalysisStrategy):

    async def analyze(self, pgn_data: str) -> List[Tuple[str, str]]:
        return [("12B", "13W"), ("16W", "18B", "Test desc")]
