from typing import List, Tuple
import chess
from chess import Color, Board, Square, Piece
from chess import KING, QUEEN, ROOK, BISHOP, KNIGHT, PAWN, WHITE, BLACK


values = { PAWN: 1, KNIGHT: 3, BISHOP: 3, ROOK: 5, QUEEN: 9 }
king_values = { PAWN: 1, KNIGHT: 3, BISHOP: 3, ROOK: 5, QUEEN: 9, KING: 99 }
ray_piece_types = [QUEEN, ROOK, BISHOP]

def piece_type(board: Board, square: Square):
    return board.piece_type_at(square)

def piece_value(piece_type: chess.PieceType) -> int:
    return values[piece_type]

def material_count(board: Board, side: Color) -> int:
    return sum(len(board.pieces(piece_type, side)) * value for piece_type, value in values.items())

def material_diff(board: Board, side: Color) -> int:
    return material_count(board, side) - material_count(board, not side)


def count_light_and_heavy_pieces(board: Board, side: Color):
    light_count = len(board.pieces(KNIGHT, side)) + len(board.pieces(BISHOP, side))
    rooks_count = len(board.pieces(ROOK, side))
    queens_count = len(board.pieces(QUEEN, side))
    return light_count, rooks_count, queens_count

def compare_piece_counts(board:Board) -> bool:
    white_light_count, white_rooks_count, white_queens_count = count_light_and_heavy_pieces(board, WHITE)
    black_light_count, black_rooks_count, black_queens_count = count_light_and_heavy_pieces(board, BLACK)

    return (white_light_count == black_light_count) and (white_rooks_count == black_rooks_count) and (white_queens_count == black_queens_count)


def attacked_opponent_pieces(board: Board, from_square: Square, pov: Color) -> List[Piece]:
    return [piece for (piece, _) in attacked_opponent_squares(board, from_square, pov)]

def attacked_opponent_squares(board: Board, from_square: Square, pov: Color) -> List[Tuple[Piece, Square]]:
    figures = []
    for attacked_square in board.attacks(from_square):
        attacked_piece = board.piece_at(attacked_square)
        if attacked_piece and attacked_piece.color != pov:
            figures.append((attacked_piece, attacked_square))
    return figures

def is_defended(board: Board, piece: Piece, square: Square) -> bool:
    if board.attackers(piece.color, square):
        return True
    for attacker in board.attackers(not piece.color, square):
        attacker_piece = board.piece_at(attacker)
        assert(attacker_piece)
        if attacker_piece.piece_type in ray_piece_types:
            bc = board.copy(stack = False)
            bc.remove_piece_at(attacker)
            if bc.attackers(piece.color, square):
                return True

    return False

def is_hanging(board: Board, piece: Piece, square: Square) -> bool:
    return not is_defended(board, piece, square)

def can_be_taken_by_lower_piece(board: Board, piece: Piece, square: Square) -> bool:
    for attacker_square in board.attackers(not piece.color, square):
        attacker = board.piece_at(attacker_square)
        assert(attacker)
        if attacker.piece_type != chess.KING and values[attacker.piece_type] < values[piece.piece_type]:
            return True
    return False

def can_be_taken_by_same_piece(board: Board, piece: Piece, square: Square) -> bool:
    for attacker_square in board.attackers(not piece.color, square):
        attacker = board.piece_at(attacker_square)
        assert(attacker)
        if attacker.piece_type != chess.KING and values[attacker.piece_type] == values[piece.piece_type]:
            return True
    return False

def is_in_bad_spot(board: Board, square: Square) -> bool:
    # hanging or takeable by lower piece
    piece = board.piece_at(square)
    assert(piece)
    return (bool(board.attackers(not piece.color, square)) and
            (is_hanging(board, piece, square) or can_be_taken_by_lower_piece(board, piece, square)))

def is_trapped(board: Board, square: Square) -> bool:
    if board.is_check() or board.is_pinned(board.turn, square):
        return False
    piece = board.piece_at(square)
    assert(piece)
    if piece.piece_type in [PAWN, KING]:
        return False
    if not is_in_bad_spot(board, square):
        return False
    for escape in board.legal_moves:
        if escape.from_square == square:
            capturing = board.piece_at(escape.to_square)
            if capturing and values[capturing.piece_type] >= values[piece.piece_type]:
                return False
            board.push(escape)
            if not is_in_bad_spot(board, escape.to_square):
                return False
            board.pop()
    return True

def attacker_pieces(board: Board, color: Color, square: Square) -> List[Piece]:
    return [p for p in [board.piece_at(s) for s in board.attackers(color, square)] if p]

# def takers(board: Board, square: Square) -> List[Tuple[Piece, Square]]:
#     # pieces that can legally take on a square
#     t = []
#     for attack in board.legal_moves:
#         if attack.to_square == square:
#             t.append((board.piece_at(attack.from_square), attack.from_square))
#     return t

def may_be_winned_black_pawn(board, square):
    if board.piece_at(square).symbol() != 'p':
        return False

    if not board.is_attacked_by(chess.WHITE, square):
        return False

    if board.is_attacked_by(chess.BLACK, square):

        white_attackers = [board.piece_at(square).symbol() for square in board.attackers(chess.WHITE, square)]
        white_pawns = 0
        white_light_figures = 0
        white_heavy_figures = 0
        white_rooks = 0
        for piece in white_attackers:
            if piece == 'P':
                white_pawns += 1
            elif piece == 'N' or piece == 'B':
                white_light_figures += 1
            elif piece == 'Q' or piece == 'K':
                white_heavy_figures += 1
            elif piece == 'R':
                white_heavy_figures += 1
                white_rooks += 1

        black_attackers = [board.piece_at(square).symbol() for square in board.attackers(chess.BLACK, square)]
        black_pawns = 0
        black_light_figures = 0
        black_heavy_figures = 0
        for piece in black_attackers:
            if piece == 'p':
                black_pawns += 1
            elif piece == 'n' or piece == 'b':
                black_light_figures += 1
            elif piece == 'q' or piece == 'r' or piece == 'k':
                black_heavy_figures += 1
        if black_pawns == white_pawns:
            if white_light_figures > 0:
                if white_light_figures - black_light_figures > 2:
                    return True

                if white_light_figures - black_light_figures >= -1:
                    return len(black_attackers) < len(white_attackers)

                if white_light_figures - black_light_figures < -1:
                    return False
            if black_light_figures > 0:
                return False
            return len(black_attackers) < len(white_attackers)

        if white_pawns - black_pawns == 1:
            if black_light_figures > 0:
                if black_light_figures - white_light_figures > 2:
                    return False

                if black_light_figures - white_light_figures >= -1:
                    return len(black_attackers) < len(white_attackers)

                if black_light_figures - white_light_figures < -1:
                    return True
            if white_light_figures > 0:
                return False
            return len(black_attackers) < len(white_attackers)

        if white_pawns - black_pawns == 2:
            return True

        if black_pawns > white_pawns:
            return False

def may_be_winned_white_pawn(board, square):
    if board.piece_at(square).symbol() != 'P':
        return False

    if not board.is_attacked_by(chess.BLACK, square): # есть ли нападения противника
        return False

    if board.is_attacked_by(chess.WHITE, square): # Есть ли защитники

        white_attackers = [board.piece_at(square).symbol() for square in board.attackers(chess.WHITE, square)]
        white_pawns = 0
        white_light_figures = 0
        white_heavy_figures = 0
        white_rooks = 0
        for piece in white_attackers:
            if piece == 'P':
                white_pawns += 1
            elif piece == 'N' or piece == 'B':
                white_light_figures += 1
            elif piece == 'Q' or piece == 'K':
                white_heavy_figures += 1
            elif piece == 'R':
                white_heavy_figures += 1
                white_rooks += 1

        black_attackers = [board.piece_at(square).symbol() for square in board.attackers(chess.BLACK, square)]
        black_pawns = 0
        black_light_figures = 0
        black_heavy_figures = 0
        for piece in black_attackers:
            if piece == 'p':
                black_pawns += 1
            elif piece == 'n' or piece == 'b':
                black_light_figures += 1
            elif piece == 'q' or piece == 'r' or piece == 'k':
                black_heavy_figures += 1


        if white_pawns == black_pawns:
            if black_light_figures > 0:
                if black_light_figures - white_light_figures > 2:
                    return True

                if black_light_figures - white_light_figures >= -1:
                    return len(black_attackers) > len(white_attackers)

                if black_light_figures - white_light_figures < -1:
                    return False
            if white_light_figures > 0:
                return False
            return len(black_attackers) > len(white_attackers)

        if black_pawns - white_pawns == 1:
            if white_light_figures > 0:
                if white_light_figures - black_light_figures > 2:
                    return False

                if white_light_figures - black_light_figures >= -1:
                    return len(black_attackers) > len(white_attackers)

                if white_light_figures - black_light_figures < -1:
                    return True
            if black_light_figures > 0:
                return False
            return len(black_attackers) > len(white_attackers)

        if black_pawns - white_pawns == 2:
            return True

        if white_pawns > black_pawns:
            return False

def may_be_winned_pawn(board, square, turn_color):
    if turn_color == chess.WHITE:
        return may_be_winned_black_pawn(board, square)
    elif turn_color == chess.BLACK:
        return may_be_winned_white_pawn(board, square)
    else:
        raise ValueError("Неизвестный цвет стороны: используйте chess.WHITE или chess.BLACK")

def merge_intervals(intervals):
    if not intervals:
        return []

    # Сортируем интервалы по левому значению
    intervals.sort(key=lambda x: x[0])
    merged = [intervals[0]]
    for current in intervals[1:]:
        prev = merged[-1]
        # Если интервалы пересекаются (т.е. начало текущего <= конец предыдущего)
        if current[0] <= prev[1]:
            # Объединяем интервалы, беря минимальное лево и максимальное право
            new_interval = (min(prev[0], current[0]), max(prev[1], current[1]))
            merged[-1] = new_interval
        else:
            # Если пересечения нет, просто добавляем текущий интервал
            merged.append(current)
    return merged

def transform_format(moves_intervals):
    if not moves_intervals:
        return []
    new_intervals = []
    for interval in moves_intervals:
        move_left, move_right = interval
        if move_left % 2 == 0:
            move_left = f"{move_left//2 + 1}W"
        else:
            move_left = f"{move_left//2 + 1}B"
        if move_right % 2 == 0:
            move_right = f"{move_right//2 + 1}W"
        else:
            move_right = f"{move_right//2 + 1}B"
        new_intervals.append((move_left, move_right))
    return new_intervals
