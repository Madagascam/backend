from typing import List, Tuple

import httpx

from app.core.analysis_base import AbstractAnalysisStrategy


async def move_to_halfmove(move_num: int) -> str:
    full_move = (move_num + 1) // 2
    color = 'w' if move_num % 2 == 1 else 'b'
    return f"{full_move}{color}"


class ProjectAIStrategy(AbstractAnalysisStrategy):
    async def analyze(self, pgn_data: str) -> List[Tuple[str, str]]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8001/upload-pgn/",
                json={"pgn_str": pgn_data}
            )
            response.raise_for_status()
            resp = response.json()
            start = await move_to_halfmove(int(resp['start']))
            end = await move_to_halfmove(int(resp['end']))
            return [(start, end)]
