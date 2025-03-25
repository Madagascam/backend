import io

import chess
import chess.engine
import chess.pgn
from chess import KING, ROOK, QUEEN, PAWN

from . import util
from .safe1 import get_all_positions


def fork(board: chess.Board, move: chess.Move, turn_color):
    flag = False
    if util.piece_type(board, move.to_square) == KING:
        return False
    if util.is_in_bad_spot(board, move.to_square) or util.can_be_taken_by_same_piece(board, board.piece_at(move.to_square), move.to_square):
        return False
    elif board.piece_at(move.to_square).piece_type == 1 and util.may_be_winned_pawn(board, move.to_square, turn_color):
        return False
    else:
        forked_figures = []
        for piece, square in util.attacked_opponent_squares(board, move.to_square, turn_color):
            if piece.piece_type == PAWN:
                continue
            if (util.king_values[piece.piece_type] > util.king_values[util.piece_type(board, move.to_square)]
                #or util.is_hanging(board, piece, square)
            ):
                forked_figures.append(square)
        if len(forked_figures) > 1:
            flag = True
    if flag == False:
        return False
    if flag == True:
        return forked_figures

def fork_check(moves, attacked_figures_squares, figure_square):
    for i in range(len(moves)):
        move = moves[i]
        # Если фигура, объявившая вилку, сделала ход
        if move.from_square == figure_square:
            if move.to_square in attacked_figures_squares:
                if i != len(moves) - 1:
                    return i + 1
                else:
                    return i

            return False
        # Если съели фигуру, объявившуя вилку
        if move.to_square == figure_square:
            return False
        if move.from_square in attacked_figures_squares:
            attacked_figures_squares.remove(move.from_square)
        if len(attacked_figures_squares) == 0:
            return False
    return False


def bishop_pin_to_king(board: chess.Board, figure_positions):
    # if util.piece_type(board, move.to_square) != BISHOP:
    #     return False

    turn_color = not board.turn
    if turn_color:

        bishop_positions = figure_positions['B']
    else:
        bishop_positions = figure_positions['b']

    for bishop_square in bishop_positions:
        if util.is_in_bad_spot(board, bishop_square) or util.can_be_taken_by_same_piece(board, board.piece_at(bishop_square), bishop_square):
            continue

        attacked_figures_positions = []
        for piece, square in util.attacked_opponent_squares(board, bishop_square, turn_color):
            if piece.piece_type == ROOK or piece.piece_type == QUEEN:
                attacked_figures_positions.append((piece, square))

        if len(attacked_figures_positions) == 0:
            continue

        for piece, square in attacked_figures_positions:
            if board.is_pinned(not turn_color, square):
                return (square, bishop_square)

    return False

def check_bishop_pin_to_king(prev_board, moves, attacked_square, bishop_square):
    board = prev_board.copy()
    turn_color = board.turn
    for i in range(len(moves)):
        move = moves[i]
        board.push(move)
        # Пошла фигура, делающая связку
        if move.from_square == bishop_square:
            if move.to_square == attacked_square:
                if i != len(moves) - 1:
                    return i + 1
                else:
                    return i
            if not board.is_pinned(turn_color, attacked_square):
                return False
            bishop_square = move.to_square
            if attacked_square not in board.attacks(bishop_square):
                return False

        # Пошла связанная фигура
        if move.from_square == attacked_square:
            if move.to_square == bishop_square:
                if util.is_in_bad_spot(board, move.to_square):
                    if i != len(moves) - 1:
                        return i + 1
                    else:
                        return i
                return False
            if not board.is_pinned(turn_color, move.to_square):
                return False
            attacked_square = move.to_square
        if not board.is_pinned(turn_color, attacked_square):
                return False
    return False


def stockfish_moments(pgn_string, engine_path, threshold=290, analysis_depth=16):
    """
    Проходит по ходам партии и с помощью Stockfish определяет оценку каждой позиции.
    Если разница между соседними оценками превышает threshold,
    считается, что наступил опорный момент.

    При обнаружении опорного момента:
      - В список добавляются два хода, давшие скачок в оценке.
      - Затем последовательно добавляются следующие ходы, если они являются взятием или дают шах.
        Если ход даёт шах, то следующий за ним (защита от шаха) добавляется автоматически
        без проверки, и обработка продолжается уже со следующего хода.
      - Если итоговый список для опорного момента содержит более 3 ходов, он сохраняется.

    Аргументы:
      pgn_file_path: путь к PGN-файлу с партией.
      engine_path: путь к исполняемому файлу Stockfish.
      threshold: порог разницы оценок.
      analysis_depth: глубина анализа для Stockfish.

    Возвращает:
      Список из интервалов интересных ходов.
    """
    engine = chess.engine.SimpleEngine.popen_uci(engine_path)

    game = chess.pgn.read_game(io.StringIO(pgn_string))

    board = game.board()
    moves = list(game.mainline_moves())
    evaluations = []

    # Получаем оценки для каждой позиции после каждого хода.
    for move in moves:
        board.push(move)
        info = engine.analyse(board, chess.engine.Limit(depth=analysis_depth))
        score = info["score"].white().score(mate_score=10000)
        #print(score)
        evaluations.append(score)

    heuristic_moments = []
    board = game.board()  # сбрасываем позицию
    num_moves = len(moves)

    for i, move in enumerate(moves):
        board.push(move)
        # Если это не первый ход, сравниваем оценку текущей и предыдущей позиции
        if i > 0:
            diff = evaluations[i] - evaluations[i - 1]
            if abs(diff) > threshold:
                # Опорный момент обнаружен: добавляем два хода, давшие скачок.
                moment_moves = [moves[i - 1], move]
                temp_board = board.copy()

                j = i + 1
                while j < num_moves:
                    next_move = moves[j]
                    # Если ход не является легальным в текущей позиции temp_board – прерываем обработку.
                    if next_move not in temp_board.legal_moves:
                        break
                    # Определяем, дает ли следующий ход шах.
                    gives_chk = temp_board.gives_check(next_move)
                    # Если ход является взятием или дает шах – добавляем его.
                    if temp_board.is_capture(next_move) or gives_chk:
                        moment_moves.append(next_move)
                        temp_board.push(next_move)
                        # Если ход дал шах, то следующий ход (защита от шаха) добавляется автоматически.
                        if gives_chk:
                            if j + 1 < num_moves:
                                auto_move = moves[j + 1]
                                if auto_move in temp_board.legal_moves:
                                    moment_moves.append(auto_move)
                                    temp_board.push(auto_move)
                                    j += 2
                                    continue
                                else:
                                    break
                        j += 1
                    else:
                        break
                if len(moment_moves) > 3:
                    heuristic_moments.append((i-1, j))

    engine.quit()
    return heuristic_moments

def find_moments_without_stockfish(pgn_string):
    heuristic_moves = []

    game = chess.pgn.read_game(io.StringIO(pgn_string))
    board = game.board()
    moves = list(game.mainline_moves())
    for move_number in range(len(moves)):
        turn_color = board.turn # Передается цвет стороны, совершающей ход
        move = moves[move_number]
        board.push(move)

        figure_positions = get_all_positions(board)
        forked_squares = fork(board, move, turn_color)
        if forked_squares != False:
            result_fork = fork_check(moves[move_number + 1:], forked_squares, move.to_square)
            if result_fork != False:
                if move_number > 1:
                    result_fork += move_number
                    #print(f"Найдена вилка с полухода {move_number - 1} до {result_fork}")
                    heuristic_moves.append((move_number - 1, result_fork))
                else:
                    result_fork += move_number
                    #print(f"Найдена вилка с полухода {move_number} до {result_fork}")
                    heuristic_moves.append((move_number, result_fork))
        squares_in_pin = bishop_pin_to_king(board, figure_positions)
        if squares_in_pin != False:
            pinned_square, bishop_square = squares_in_pin
            result_of_pin = check_bishop_pin_to_king(board, moves[move_number + 1:], pinned_square, bishop_square)
            if result_of_pin != False:
                if move_number > 1:
                    result_of_pin += move_number
                    #print(f"Найдена связка с полухода {move_number - 2} до {result_of_pin}")
                    heuristic_moves.append((move_number - 2, result_of_pin))
                elif move_number > 0:
                    result_of_pin += move_number
                    #print(f"Найдена связка с полухода {move_number - 1} до {result_of_pin}")
                    heuristic_moves.append((move_number - 1, result_of_pin))
                else:
                    result_of_pin += move_number
                    #print(f"Найдена связка с полухода {move_number} до {result_of_pin}")
                    heuristic_moves.append((move_number, result_of_pin))

    heuristic_moves = util.merge_intervals(heuristic_moves)
    #print(heuristic_moves)
    return heuristic_moves
