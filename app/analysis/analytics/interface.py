from typing import List, Tuple

from app.analysis import AbstractAnalysisStrategy
from .heuristic_functions import find_moments_without_stockfish, stockfish_moments
from .util import merge_intervals, transform_format


class AnalyticsStrategy(AbstractAnalysisStrategy):

    async def analyze(self, pgn_data: str,
                      engine_path: str = "Cock"
                      ) -> List[Tuple[str, str]]:
        heuristics_without_stockfish = find_moments_without_stockfish(pgn_data)
        stockfish_moves = stockfish_moments(pgn_data, engine_path)
        heuristics = heuristics_without_stockfish + stockfish_moves
        heuristics = merge_intervals(heuristics)

        return transform_format(heuristics)
