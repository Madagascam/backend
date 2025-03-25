import chess

# fen = "rnbq2k1/pp3rpp/2P2n2/4pp2/1bB5/2NP1P2/PPPBN1PP/R2QK2R b KQ - 0 9"
# board = chess.Board(fen)
#print(board)


# Определяем ценность фигур
piece_values = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 200
}

white_figures = ['K', 'Q', 'R', 'B', 'N', 'P']
black_figures = ['k', 'q', 'r', 'b', 'n', 'p']
def get_all_positions(board):
    figure_positions = {
        'K' : [],
        'Q' : [],
        'R' : [],
        'B' : [],
        'N' : [],
        'P' : [],
        'k' : [],
        'q' : [],
        'r' : [],
        'b' : [],
        'n' : [],
        'p' : []
    }
    for square in chess.SQUARES:
        if board.piece_at(square):
            figure_positions[board.piece_at(square).symbol()].append(square)
    return figure_positions
#print(get_all_positions(board))

def is_white_protected(board, square, figure_positions):
    # white_positions = figure_positions['K'] + figure_positions['Q'] + figure_positions['R'] + figure_positions['B'] + figure_positions['N'] + figure_positions['P']
    # for defender_square in white_positions:
    #     if square in board.attacks(defender_square):
    #         return True
    if board.is_attacked_by(chess.WHITE, square):
        return True
    return False

def is_black_protected(board, square, figure_positions):
    # white_positions = figure_positions['k'] + figure_positions['q'] + figure_positions['r'] + figure_positions['b'] + figure_positions['n'] + figure_positions['p']
    # for defender_square in white_positions:
    #     if square in board.attacks(defender_square):
    #         return True
    if board.is_attacked_by(chess.BLACK, square):
        return True
    return False

def get_black_bishop_attacks(board, figure_positions):
    bishop_positions = figure_positions['b']
    bishop_moves = []
    for square in bishop_positions:
        for move in board.attacks(square):
            bishop_moves.append(move)
    return bishop_moves

def get_white_bishop_attacks(board, figure_positions):
    bishop_positions = figure_positions['B']
    bishop_moves = []
    for square in bishop_positions:
        bishop_moves += [move for move in board.attacks(square)]
    return bishop_moves

# Возвращает именно удары по диагонали, а не возможные ходы
def get_black_pawn_attacks(board, figure_positions):
    pawn_positions = figure_positions['p']
    pawn_moves = []
    for square in pawn_positions:
        for move in board.attacks(square):
            pawn_moves.append(move)
    return pawn_moves

def get_white_pawn_attacks(board, figure_positions):
    pawn_positions = figure_positions['P']
    pawn_moves = []
    for square in pawn_positions:
        for move in board.attacks(square):
            pawn_moves.append(move)
    return pawn_moves

def get_black_knight_attacks(board, figure_positions):
    knight_positions = figure_positions['n']
    knight_moves = []
    for square in knight_positions:
        for move in board.attacks(square):
            knight_moves.append(move)
    return knight_moves

def get_white_knight_attacks(board, figure_positions):
    knight_positions = figure_positions['N']
    knight_moves = []
    for square in knight_positions:
        for move in board.attacks(square):
            knight_moves.append(move)
    return knight_moves

def get_black_rook_attacks(board, figure_positions):
    rook_positions = figure_positions['r']
    rook_moves = []
    for square in rook_positions:
        for move in board.attacks(square):
            rook_moves.append(move)
    return rook_moves

def get_black_queen_attacks(board, figure_positions):
    queen_positions = figure_positions['q']
    queen_moves = []
    for square in queen_positions:
        for move in board.attacks(square):
            queen_moves.append(move)
    return queen_moves

def is_white_knight_safe(board, knight_position, figure_positions):
    pawn_attacks = get_black_pawn_attacks(board, figure_positions)
    bishop_attacks = get_black_bishop_attacks(board, figure_positions)
    knight_attacks = get_black_knight_attacks(board, figure_positions)
    if knight_position in bishop_attacks or knight_position in knight_attacks or knight_position in pawn_attacks:
        return False

    # Проверка на атаку ферзем, ладьей или королем
    heavy_figures = figure_positions['q'] + figure_positions['r'] + figure_positions['k']
    for square in heavy_figures:
        if knight_position in board.attacks(square):
            if not is_white_protected(board, knight_position, figure_positions):
                return False
    return True

def is_white_bishop_safe(board, bishop_position, figure_positions):
    pawn_attacks = get_black_pawn_attacks(board, figure_positions)
    bishop_attacks = get_black_bishop_attacks(board, figure_positions)
    knight_attacks = get_black_knight_attacks(board, figure_positions)
    if bishop_position in bishop_attacks or bishop_position in knight_attacks or bishop_position in pawn_attacks:
        return False

    # Проверка на атаку ферзем, ладьей или королем
    heavy_figures_positions = figure_positions['q'] + figure_positions['r'] + figure_positions['k']
    for square in heavy_figures_positions:
        if bishop_position in board.attacks(square):
            if not is_white_protected(board, bishop_position, figure_positions):
                return False
    return True

def is_white_rook_safe(board, rook_position, figure_positions):
    if rook_position in get_black_pawn_attacks(board, figure_positions) or rook_position in get_black_bishop_attacks(board, figure_positions) or rook_position in get_black_knight_attacks(board, figure_positions) or rook_position in get_black_rook_attacks(board, figure_positions):
        return False

    attacking_figures_positions = figure_positions['q'] + figure_positions['k']
    for square in attacking_figures_positions:
        if rook_position in board.attacks(square):
            if not is_white_protected(board, rook_position, figure_positions):
                return False
    return True

def is_white_queen_safe(board, queen_position):
    if board.is_attacked_by(chess.BLACK, queen_position):
        return False
    return True


def detect_piece_sacrifice(board, move, previous_board):
    # Получаем фигуру, которая была убрана с доски
    captured_piece = previous_board.piece_at(move.to_square)
    if captured_piece is None:
        return False  # Нет жертвы
    # Определяем фигуру, которая сделала ход
    moving_piece = board.piece_at(move.from_square)

    piece_values = {
        chess.PAWN: 1,
        chess.KNIGHT: 3,
        chess.BISHOP: 3,
        chess.ROOK: 5,
        chess.QUEEN: 9,
        chess.KING: 200
    }
    if not board.is_attacked_by(chess.BLACK, move.to_square):
        return False
    if piece_values[captured_piece.piece_type] < piece_values[moving_piece.piece_type]:
        print("Жертва")
        return True
    return False

def is_pin(board, square, pinned_figure_color):
    return board.is_pinned(pinned_figure_color, square)

def may_be_occupied_by_black_pawn(board, square):
    if square // 8 == 7:
        return False
    if square // 8 == 4: # поле на пятом ряду
        square_1 = square + 8
        if board.piece_at(square_1):
            if board.piece_at(square_1).symbol() == 'p':
                move = chess.Move(square_1, square)
                if move in board.legal_moves:
                    return True
                return False
            return False
        square_2 = square + 16
        if board.piece_at(square_2) and board.piece_at(square_1).symbol() == 'p':
            move = chess.Move(square_2, square)
            if move in board.legal_moves:
                board_1 = board.copy() # Проверяем взятие на проходе, если оно есть, то будем возвращать False
                board_1.push(move)
                if board_1.has_legal_en_passant():
                    return False
                return True
            return False
        return False

    else:
        square_1 = square + 8
        if board.piece_at(square_1) and board.piece_at(square_1).symbol() == 'p':
            move = chess.Move(square_1, square)
            if move in board.legal_moves:
                return True
            return False

def white_attackers_with_types(board, square):
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
    return white_pawns, white_light_figures, white_rooks, white_heavy_figures

def black_attackers_with_types(board, square):
    black_attackers = [board.piece_at(square).symbol() for square in board.attackers(chess.BLACK, square)]
    black_pawns = 0
    black_rooks = 0
    black_light_figures = 0
    black_heavy_figures = 0
    for piece in black_attackers:
        if piece == 'p':
            black_pawns += 1
        elif piece == 'n' or piece == 'b':
            black_light_figures += 1
        elif piece == 'q' or piece == 'r' or piece == 'k':
            black_heavy_figures += 1
        elif piece == 'r':
            black_rooks += 1

    return black_pawns, black_light_figures, black_rooks, black_heavy_figures

def possible_block_pin_square(board, square, figure_positions):
    if board.is_attacked_by(chess.BLACK, square):
        if may_be_occupied_by_black_pawn(board, square):
            black_pawns, black_light_figures, black_rooks, black_heavy_figures = black_attackers_with_types(board, square)

            white_pawns, white_light_figures, white_rooks, white_heavy_figures = white_attackers_with_types(board, square)

            # двух атак пешек (для обеих сторон) быть не может, т.к. связки не будет
            if black_pawns == white_pawns:
                # Т.к. функция для связки слоном, как минимум одна легкая фигура белых атакует заданное поле
                if white_light_figures - black_light_figures > 2:
                    return False

                if white_light_figures - black_light_figures > 0:
                    return len(black_attackers) >= len(white_attackers)

                if white_light_figures - black_light_figures <= 0:
                    return True

            if black_pawns == 0 and white_pawns == 1: # False только если в конце концов можно совершить взятие слоном
                if black_light_figures > 0:
                    if white_light_figures - black_light_figures > 0:
                        return False

                    if white_light_figures - black_light_figures <= 0:
                        return True
                return False


            if black_pawns == 1 and white_pawns == 0:
                return True

        if square in get_white_pawn_attacks(board, figure_positions):
            return False

        black_attackers = [board.piece_at(square).symbol() for square in board.attackers(chess.BLACK, square)]
        black_light_figures = 0
        black_heavy_figures = 0
        for piece in black_attackers:
            if piece == 'n' or piece == 'b':
                black_light_figures += 1
            elif piece == 'q' or piece == 'r' or piece == 'k':
                black_heavy_figures += 1

        if black_light_figures == 0: # Перекрываться можно только легкой фигурой
            return False

        if square in get_black_pawn_attacks(board, figure_positions): # Значит есть одна черная пешка
            if white_light_figures - black_light_figures < 2:
                return True
            return len(black_attackers) >= len(white_attackers)


        white_attackers = [board.piece_at(square).symbol() for square in board.attackers(chess.WHITE, square)]
        white_light_figures = 0
        white_heavy_figures = 0
        for piece in white_attackers:
            if piece == 'N' or piece == 'B':
                white_light_figures += 1
            elif piece == 'Q' or piece == 'R' or piece == 'K':
                white_heavy_figures += 1
        if len(black_attackers) <= len(white_attackers): # Защитников должно быть больше, т.к. одна из фигур будет перекрываться
            return False

        if black_heavy_figures == 0 and white_heavy_figures == 0:
            return True
        if black_light_figures == 0 and white_light_figures == 0:
            return True
        if black_light_figures < white_light_figures:
            return False
        return True

    return False

# Определяет можно ли выиграть фигуру на заданном поле (выигрыш пешки - так же пешки)
# Проблема методов attackers, attacks в том, что связанная фигура также считается
# Нужно добавить взятие на проходе
def may_be_winned_material(board, square):
    if not board.piece_at(square):
        return False

    if not board.is_attacked_by(chess.WHITE, square):
        return False

    if board.is_attacked_by(chess.BLACK, square):
        piece_at_square = board.piece_at(square).symbol()

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

        if piece_at_square == 'q':
            if white_pawns + white_light_figures + white_rooks > 0:
                return True
            if white_heavy_figures > 0:
                return True
            return False

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

        if piece_at_square == 'r':
            if white_pawns + white_light_figures > 0:
                return True
            if white_rooks > 0:
                if black_light_figures + black_pawns <= 1:
                    return len(black_attackers) < len(white_attackers)

                if black_light_figures + black_pawns > 1:
                    return False


        if piece_at_square == 'b' or piece_at_square == 'n':
            if white_pawns > 0:
                return True

            if black_pawns == 0:
                if white_light_figures > 0:
                    if white_light_figures - black_light_figures > 1:
                        return True
                    if white_light_figures - black_light_figures >= -1:
                        return len(black_attackers) < len(white_attackers)
                    if white_light_figures - black_light_figures < -1:
                        return False

                if black_light_figures > 1:
                    return False

                if black_light_figures == 1:
                    return len(black_attackers) < len(white_attackers)

                return len(black_attackers) < len(white_attackers)

            if black_pawns == 1:
                if white_light_figures > 0:
                    if white_light_figures - black_light_figures < 1:
                        return False
                    return len(black_attackers) < len(white_attackers)
                return False

            if black_pawns > 1:
                return False

        if piece_at_square == 'p':
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
