from typing import List, Tuple

from app.core.analysis_base import AbstractAnalysisStrategy
from .heuristic_functions import find_all_moments
from ...config import settings


class AnalyticsStrategy(AbstractAnalysisStrategy):

    async def analyze(self, pgn_data: str,
                      engine_path: str = settings.analysis.engine_path
                      ) -> List[Tuple[str, str]]:
        heuristics = await find_all_moments(pgn_data, engine_path)

        return heuristics
