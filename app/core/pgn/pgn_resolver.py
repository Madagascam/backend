import io
from typing import ItemsView, List

import chess.pgn


class PGNResolver:
    def __init__(self, pgn: str):
        self.pgn_str = pgn
        self.game: chess.pgn.Game = chess.pgn.read_game(self.get_io_string(pgn))
        self.board = self.game.board()

    def get_io_string(self, pgn: str) -> io.StringIO:
        return io.StringIO(pgn)

    def get_metadata(self) -> ItemsView[str, str]:
        return self.game.headers.items()

    def get_board_positions(self) -> List[str]:
        pos = []

        for move in self.game.mainline_moves():
            pos.append(self.board.fen().split()[0])
            self.board.push(move)

        return pos



