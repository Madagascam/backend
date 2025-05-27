import io
from typing import List, Tuple, Dict, Set

import chess
import chess.pgn
import chess.engine
from util import merge_intervals, is_in_bad_spot, intervals_format

# --- «цена» фигур в пешках -----------------------------------------------
PIECE_VALUE = {
    chess.PAWN:   1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK:   5,
    chess.QUEEN:  9,
    chess.KING: 100,
}


def detect_forks(pgn: str) -> List[Tuple[str, str]]:
    """
    Выявляет интервалы вилок в партии.

    Возвращает список кортежей, например [('23W', '25B'), …].
    """

    game = chess.pgn.read_game(io.StringIO(pgn))
    board = game.board()

    active_forks = []
    results = []
    ply = 0

    # === проход по всем полуходам =========================================
    for move in game.mainline_moves():
        ply += 1

        # 1. ОБНОВЛЯЕМ уже идущие вилки ПЕРЕД выполнением хода

        for fork in active_forks[:]:
            attacker_sq   = fork["attacker_sq"]
            attacker_val  = fork["attacker_val"]
            targets       = fork["targets"]

            # походила ли атакующая фигура?
            if move.from_square == attacker_sq:
                # фигура-вилочник сдвинулась

                if board.is_capture(move) and move.to_square in targets:   # взяла одну из целей
                    captured_piece   = board.piece_at(move.to_square)
                    captured_val     = PIECE_VALUE[captured_piece.piece_type]
                    defended_before  = board.is_attacked_by(captured_piece.color,
                                                             move.to_square)

                    # равная + защищена  → НЕ считается
                    if not (captured_val == attacker_val and defended_before):
                        results.append(extend_interval(pgn, fork["start"] - 1, ply))

                # фигура ушла, а цель не взята → вилка аннулируется
                active_forks.remove(fork)
                continue

            #  цель ушла на другое поле
            if move.from_square in targets:
                targets[move.to_square] = targets.pop(move.from_square)

            #  цель съедена кем-то другим
            if board.is_capture(move) and move.to_square in targets:
                results.append(extend_interval(pgn, fork["start"] - 1, ply))
                active_forks.remove(fork)
                continue

        board.push(move)

        # Проверяем: возникла ли новая вилка после этого хода

        attacker_sq  = move.to_square
        attacker     = board.piece_at(attacker_sq)
        if attacker is None:
            continue

        attacker_val = PIECE_VALUE[attacker.piece_type]

        # собираем подходящие цели
        attacked_now = {}
        for sq in board.attacks(attacker_sq):
            piece = board.piece_at(sq)
            if not piece or piece.color == attacker.color:          # пусто или своя фигура
                continue
            if piece.piece_type == chess.PAWN:                      # пешки игнорируем
                continue

            defended = board.is_attacked_by(piece.color, sq)

            # условие первоначальной вилки
            if PIECE_VALUE[piece.piece_type] > attacker_val or not defended:
                attacked_now[sq] = (piece.color, piece.piece_type)

        # если целей ≥ 2 → фиксируем новую «живую» вилку
        if len(attacked_now) >= 2:
            active_forks.append(
                {
                    "start":        ply,
                    "attacker_sq":  attacker_sq,
                    "attacker_val": attacker_val,
                    "targets":      attacked_now
                }
            )

    return results

def extend_interval(
    pgn: str,
    start_ply: int,
    end_ply: int,
) -> Tuple[int, int]:
    """
    «Доращивает» уже найденный интервал вилки согласно правилам:

    1.  Если текущий полуход — **взятие**, он включается в интервал
        и сразу проверяется следующий полуход.
    2.  Если текущий полуход — **шах**, он включается в интервал
        *вместе* со следующим полуходом-ответом (если партия не закончилась).
        Далее проверка продолжается со второго полухода после шаха.
    3.  В противном случае расширение прекращается,
        функция возвращает окончательные границы интервала.

    ----------
    Параметры
    ----------
    pgn        : str   – та же партия, что и для поиска вилки
    start_ply  : int   – 1-based полуход, на котором вилка началась
    end_ply    : int   – 1-based полуход, на котором была взята цель вилки
                          (то, что вернул detect_forks)

    """
    game = chess.pgn.read_game(io.StringIO(pgn))
    moves = list(game.mainline_moves())
    total = len(moves)

    board = game.board()
    for idx in range(end_ply):
        board.push(moves[idx])

    new_end_ply = end_ply
    idx = end_ply

    while idx < total:
        move = moves[idx]

        is_capture = board.is_capture(move)
        is_check   = board.gives_check(move)

        if is_capture:
            board.push(move)
            new_end_ply = idx + 1            # +1, т.к. ply c единицы
            idx += 1                         # переходим к следующему полуходу
            continue

        if is_check:
            # добавляем ход-шах
            board.push(move)
            new_end_ply = idx + 1

            # добавляем обязательный ответ, если не конец партии
            if idx + 1 < total:
                board.push(moves[idx + 1])
                new_end_ply = idx + 2
                idx += 2                     # «через ход» от шаха
            else:
                break                        # партия закончилась шахом
            continue

        # ни взятия, ни шаха — расширение закончено
        break

    return (start_ply, new_end_ply)

# фигуры ценные для связки
VALUABLE = {chess.ROOK, chess.QUEEN, chess.KING}


# все диагональные смещения
_DIAG_STEPS = ((1, 1), (1, -1), (-1, 1), (-1, -1))


# ---------------------------------------------------------------------------
def _find_bishop_pins(board: chess.Board, bishop_sq: chess.Square) -> List[Tuple[int, int]]:
    """
    Возвращает список пар (front_sq, back_sq) – всех связок,
    которые прямо сейчас создаёт слон, стоящий на bishop_sq.
    """
    color = board.piece_at(bishop_sq).color
    pins = []

    for df, dr in _DIAG_STEPS:
        f = chess.square_file(bishop_sq) + df
        r = chess.square_rank(bishop_sq) + dr

        front_sq = None

        while 0 <= f < 8 and 0 <= r < 8:
            sq = chess.square(f, r)
            piece = board.piece_at(sq)

            if piece is None:
                f += df
                r += dr
                continue

            # первая встреченная фигура – потенциальная «передняя»
            if front_sq is None:
                if piece.color != color and piece.piece_type in VALUABLE:
                    front_sq = sq
                    f += df
                    r += dr
                    continue
                break  # своя или «неценная» – связки нет на этом луче

            # это уже «за» front_sq  → ищем «заднюю» ценную
            if piece.color != color and piece.piece_type in VALUABLE:
                pins.append((front_sq, sq))
            break

    return pins


def detect_pins(pgn: str) -> List[Tuple[str, str]]:
    """
    Находит ВСЕ «связки-с-участием-слона» в партии PGN.

    Возвращает отрезки вида ('23W', '27B'), где
    • начало – полуход появления связки;
    • конец   – полуход, на котором ОДНА из связанных фигур была взята.

    Алгоритм:
      1. шагаем по полуходам,
      2. ведём список «живых» связок,
      3. засчитываем успех, если front- или back-фигура съедена,
      4. убираем связку, если слон ушёл и не сохранил луч.
    """
    game = chess.pgn.read_game(io.StringIO(pgn))
    board = game.board()

    active: List[Dict] = []        # [{start, bishop, pinned:Set[int]} …]
    result: List[Tuple[str, str]] = []

    ply = 0
    moves = game.mainline_moves()

    for move in moves:
        ply += 1

        # обновляем действующие связки
        for pin in active[:]:
            bishop_sq = pin["bishop"]
            pinned: Set[int] = pin["pinned"]

            # слон сделал ход
            if move.from_square == bishop_sq:
                # взял одну из связанных фигур?  → успех
                if board.is_capture(move) and move.to_square in pinned:
                    result.append(extend_interval(pgn, pin["start"] - 1, ply))
                # независимо от результата слон покинул клетку – удаляем связку
                active.remove(pin)
                continue

            # 1.2 слона забрали
            if move.to_square == bishop_sq:
                active.remove(pin)
                continue

            # 1.3 съели front или back фигуру
            if board.is_capture(move) and move.to_square in pinned:
                result.append(extend_interval(pgn, pin["start"] - 1, ply))
                active.remove(pin)
                continue

            # 1.4 связанные фигуры куда-то отошли – удаляем их
            if move.from_square in pinned:
                pinned.remove(move.from_square)
                if not pinned:
                    active.remove(pin)


        board.push(move)


        bivouac = board.piece_at(move.to_square)
        if bivouac and bivouac.piece_type == chess.BISHOP:
            for front, back in _find_bishop_pins(board, move.to_square):
                active.append(
                    {
                        "start":  ply,
                        "bishop": move.to_square,
                        "pinned": {front, back},
                    }
                )

    return result

def is_trapped(board: chess.Board, square: int) -> bool:
    """
    Фигура «поймана», если:
      • не пешка и не король;
      • под боем более дешёвой фигуры или висит;
      • нет собственного хода, который выводит её в безопасное положение.
    """
    piece = board.piece_at(square)
    if not piece or piece.piece_type in (chess.PAWN, chess.KING):
        return False
    if board.is_check() or board.is_pinned(piece.color, square):
        return False
    if not is_in_bad_spot(board, square):
        return False

    for mv in list(board.legal_moves):
        if mv.from_square != square:
            continue

        captured = board.piece_at(mv.to_square)
        if captured and PIECE_VALUE[captured.piece_type] >= PIECE_VALUE[piece.piece_type]:
            return False

        board.push(mv)
        safe = not is_in_bad_spot(board, mv.to_square)
        board.pop()
        if safe:
            return False
    return True


def detect_trapped_pieces(pgn: str) -> List[Tuple[str, str]]:
    """
    Возвращает интервалы вида ('23W', '27B'), где
      • начало — момент, когда фигура стала «пойманной»;
      • конец   — полуход, на котором её действительно съели.
    """
    game = chess.pgn.read_game(io.StringIO(pgn))
    board = game.board()

    active: List[Dict] = []        # [{start, square}]
    result: List[Tuple[str, str]] = []
    ply = 0

    for move in game.mainline_moves():
        ply += 1

        for trap in active[:]:
            sq = trap["square"]


            if board.is_capture(move) and move.to_square == sq:
                result.append(extend_interval(pgn, trap["start"] - 1, ply))
                active.remove(trap)
                continue

            if move.from_square == sq:
                trap["square"] = move.to_square


        board.push(move)

        for trap in active[:]:
            if not board.piece_at(trap["square"]) or not is_trapped(board, trap["square"]):
                active.remove(trap)

        side_to_move = board.turn
        for p_type in (chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN):
            for sq in board.pieces(p_type, side_to_move):
                if any(sq == t["square"] for t in active):  # уже отслеживаем
                    continue
                if is_trapped(board, sq):
                    active.append({"start": ply, "square": sq})

    return result

def detect_sacrifices(pgn: str) -> List[Tuple[str, str]]:
    """
    «Жертва» = фигура X берёт менее ценную фигуру Y
               и сразу (на следующем полуходе соперника) оказывается съеденной.
               Если X сделала хотя бы ещё один собственный ход — это уже не жертва.
    Возвращает интервалы ('startTag', 'endTag').
    """
    game = chess.pgn.read_game(io.StringIO(pgn))
    if game is None:
        return []

    board = game.board()
    ply = 0

    # active:  отслеживаемые потенциальные жертвы до следующего ответа соперника
    #   {'start': int, 'square': int, 'color': bool, 'piece_type': int}
    active: List[Dict] = []
    result: List[Tuple[str, str]] = []

    for move in game.mainline_moves():
        ply += 1
        side_to_move = board.turn            # цвет, делающий ХОД с точки зрения board

        # ───── 1. обработка активных жертв ДО хода ────────────────────────
        for sac in active[:]:
            sq = sac["square"]

            # 1.1 соперник съел жертвующую фигуру → успех
            if board.is_capture(move) and move.to_square == sq:
                result.append(extend_interval(pgn, sac["start"] - 1, ply))
                active.remove(sac)
                continue

            # 1.2 «жертвующая» фигура сама делает второй ход → не жертва
            if move.from_square == sq:
                active.remove(sac)
                continue

        # ───── 2. проверяем, был ли ход жертвой ───────────────────────────
        is_capture = board.is_capture(move)
        if is_capture:
            capturing_piece = board.piece_at(move.from_square)
            captured_piece = board.piece_at(move.to_square)

            if capturing_piece and captured_piece:
                if PIECE_VALUE[captured_piece.piece_type] < PIECE_VALUE[capturing_piece.piece_type]:
                    active.append(
                        dict(start=ply,
                             square=move.to_square,
                             color=capturing_piece.color,
                             piece_type=capturing_piece.piece_type)
                    )

        board.push(move)

        for sac in active[:]:
            if sac["color"] == board.turn:
                active.remove(sac)

    return result


def stockfish_moments(
    pgn_string: str,
    engine_path: str,
    threshold: int = 290,
    analysis_depth: int = 16,
) -> List[Tuple[str, str]]:
    """
    Возвращает список интервалов (startTag, endTag) — «опорные моменты»,
    где оценка Stockfish изменилась минимум на `threshold` cp.
    Интервал дополнительно растягивается `extend_interval`, а
    в результат попадают только те, что длиннее 3 полуходов.
    """
    engine = chess.engine.SimpleEngine.popen_uci(engine_path)

    game = chess.pgn.read_game(io.StringIO(pgn_string))
    if game is None:
        engine.quit()
        raise ValueError("PGN-строка не содержит партию.")

    # ── 1. собираем все оценки (позиция *после* каждого хода) ──
    board = game.board()
    moves = list(game.mainline_moves())

    evaluations: List[int] = [
        engine.analyse(board, chess.engine.Limit(depth=analysis_depth))["score"]
        .white()
        .score(mate_score=10000)
    ]

    for mv in moves:
        board.push(mv)
        cp = (
            engine.analyse(board, chess.engine.Limit(depth=analysis_depth))["score"]
            .white()
            .score(mate_score=10000)
        )
        evaluations.append(cp)

    result: List[Tuple[str, str]] = []

    board = game.board()
    ply = 0

    for idx, mv in enumerate(moves, start=1):
        board.push(mv)
        ply += 1                    # теперь board = позиция *после* ply-го полухода

        diff = evaluations[idx] - evaluations[idx - 1]
        if abs(diff) >= threshold:
            start_tag, end_tag = extend_interval(pgn_string, ply - 1, ply)
            if end_tag - start_tag > 2:
                result.append((start_tag, end_tag))

    engine.quit()
    return result



def find_moments_without_stockfish(pgn_string):
    moments = detect_forks(pgn_string) + detect_pins(pgn_string) + detect_sacrifices(pgn_string) + detect_sacrifices(pgn_string)
    return intervals_format(merge_intervals(moments))

def find_all_moments(pgn_string, engine_path):
    moments = detect_forks(pgn_string) + detect_pins(pgn_string) + detect_sacrifices(pgn_string) + detect_sacrifices(pgn_string) + stockfish_moments(pgn_string, engine_path)
    return intervals_format(merge_intervals(moments))


# pgn_string = "1. e4 e5 2. Nf3 Nc6 3. Bc4 Nf6 4. Ng5 d6 5. Nxf7 Be6 6. Nxh8 Bxc4 7. Qh5+ Nxh5 8. d3 Be6"
# engine_path = "C:/Users/Thinkpad/Desktop/Гоша/Friflex/stockfish-windows-x86-64-avx2/stockfish/stockfish-windows-x86-64-avx2.exe"
# print(find_all_moments(pgn_string, engine_path))
# print(find_moments_without_stockfish(pgn_string))
