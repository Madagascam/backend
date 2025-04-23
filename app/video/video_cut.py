import os
import re
import subprocess
from datetime import datetime, timedelta
from typing import List, Tuple, Optional

import chess.pgn


async def parse_video_start_time(filename: str) -> datetime:
    """Парсит название видео <start_ts>-<end_ts>.<ext> и возвращает datetime начала"""
    base = os.path.basename(filename)
    match = re.match(r"(\d+)-\d+\.\w+", base)
    if not match:
        raise ValueError("Название видео должно быть в формате <start_ts>-<end_ts>.<расширение>")

    start_timestamp = int(match.group(1))  # в миллисекундах
    return datetime.utcfromtimestamp(start_timestamp / 1000)


async def get_first_move_timestamp(pgn_file: str) -> int:
    """Извлекает timestamp первого хода из PGN"""
    with open(pgn_file, "r", encoding="utf-8") as f:
        game = chess.pgn.read_game(f)

    node = game
    while node.variations:
        next_node = node.variations[0]
        if next_node.comment:
            match = re.search(r"\[%ts (\d+)\]", next_node.comment)
            if match:
                return int(match.group(1))
        node = next_node

    raise ValueError("Не найден timestamp первого хода в PGN")


async def calculate_offset_in_video(video_filename: str, pgn_file: str) -> float:
    """Вычисляет смещение первого хода относительно начала видео"""
    video_start_time = parse_video_start_time(video_filename)
    first_move_ts = get_first_move_timestamp(pgn_file)
    first_move_time = datetime.utcfromtimestamp(first_move_ts / 1000)

    offset = (first_move_time - video_start_time).total_seconds()
    if offset < 0:
        raise ValueError("Первый ход был раньше начала видео — проверь синхронизацию")

    print(f"Первый ход был на {offset:.2f} секунде видео")
    return offset


async def merge_close_timestamps(timestamps: List[Tuple[float, float]], gap: float = 10) -> List[Tuple[float, float]]:
    """Объединяет временные отрезки, если между ними менее gap секунд"""
    if not timestamps:
        return []

    merged: List[Tuple[float, float]] = [timestamps[0]]

    for start, duration in timestamps[1:]:
        prev_start, prev_duration = merged[-1]
        prev_end = prev_start + prev_duration

        if start - prev_end <= gap:
            merged[-1] = (prev_start, (start + duration) - prev_start)
        else:
            merged.append((start, duration))

    return merged


async def extract_move_timestamps(pgn_file: str, start_move: int, end_move: int, first_move_time: float) -> List[
    Tuple[float, float]]:
    """Извлекает временные метки ходов из PGN и объединяет близкие фрагменты"""
    with open(pgn_file, "r", encoding="utf-8") as f:
        game = chess.pgn.read_game(f)
    if not game:
        raise ValueError("Не удалось загрузить партию из PGN")

    timestamps: List[Tuple[float, float]] = []
    node = game
    start_time: Optional[int] = None
    move_number = 1

    while node.variations:
        next_node = node.variations[0]
        if next_node.comment:
            match = re.search(r"\[%ts (\d+)\]", next_node.comment)
            if match:
                timestamp = int(match.group(1))
                if start_time is None:
                    start_time = timestamp
                elapsed_time = timestamp - start_time
                elapsed_time_td = timedelta(milliseconds=elapsed_time)
                timestamp_sec = elapsed_time_td.total_seconds() + first_move_time

                if start_move <= move_number <= end_move:
                    start_sec = max(0, timestamp_sec - 3)
                    duration = 6
                    timestamps.append((start_sec, duration))

        if move_number >= end_move:
            break

        node = next_node
        move_number += 1

    return merge_close_timestamps(timestamps)


async def cut_video_ffmpeg(video_path: str, timestamps: List[Tuple[float, float]], output_path: str) -> None:
    """Вырезает фрагменты и склеивает их в одно видео"""
    temp_files: List[str] = []

    for i, (start, duration) in enumerate(timestamps):
        temp_file = f"cut_part_{i}.mp4"

        cut_command = [
            "ffmpeg", "-y", "-i", video_path, "-ss", str(start), "-t", str(duration),
            "-c", "copy", temp_file
        ]
        subprocess.run(cut_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        temp_files.append(temp_file)

    with open("file_list.txt", "w") as f:
        for temp in temp_files:
            f.write(f"file '{temp}'\n")

    merge_command = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "file_list.txt",
        "-c", "copy", output_path
    ]
    subprocess.run(merge_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    for temp in temp_files:
        os.remove(temp)

    print(f"Финальное видео сохранено в {output_path}")


# Пример использования
video_file: str = "1740905773552-1740906269417.mp4"
pgn_file: str = "_1_Safmar_Rapid_C_Kavalenya_Ivan_Leonidovich_Serov_Timofej_Andreevich.pgn"
output_file: str = "result.mp4"

first_move_offset: float = calculate_offset_in_video(video_file, pgn_file)

timestamps: List[Tuple[float, float]] = extract_move_timestamps(
    pgn_file=pgn_file,
    start_move=1,
    end_move=10,
    first_move_time=first_move_offset
)

cut_video_ffmpeg(video_file, timestamps, output_file)

