import os
import re
import chess.pgn
import subprocess
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
import time
import asyncio
import aiofiles
import aiofiles.os


def parse_video_start_time(filename: str) -> datetime:
    """Парсит название видео <start_ts>-<end_ts>.<ext> и возвращает datetime начала"""
    base = os.path.basename(filename)
    match = re.match(r"(\d+)-\d+\.\w+", base)
    if not match:
        raise ValueError("Название видео должно быть в формате <start_ts>-<end_ts>.<расширение>")

    start_timestamp = int(match.group(1))  # в миллисекундах
    return datetime.utcfromtimestamp(start_timestamp / 1000)


async def get_first_move_timestamp(pgn_file: str) -> int:
    """Извлекает timestamp первого хода из PGN (асинхронно)"""
    try:
        async with aiofiles.open(pgn_file, "r", encoding="utf-8") as f:
            content = await f.read()
            from io import StringIO
            pgn_io = StringIO(content)
            game = chess.pgn.read_game(pgn_io)
            if not game:
                 raise ValueError("Не удалось загрузить партию из PGN файла.")
        node = game
        while node.variations:
            next_node = node.variations[0]
            if next_node.comment:
                match = re.search(r"\[%ts (\d+)\]", next_node.comment)
                if match:
                    return int(match.group(1))
            node = next_node

        raise ValueError("Не найден timestamp первого хода в PGN")
    except FileNotFoundError:
        raise FileNotFoundError(f"PGN файл не найден: {pgn_file}")


async def calculate_offset_in_video(video_filename: str, pgn_file: str) -> float:
    """Вычисляет смещение первого хода относительно начала видео (асинхронно)"""
    video_start_time = parse_video_start_time(video_filename)
    first_move_ts = await get_first_move_timestamp(pgn_file)
    first_move_time = datetime.utcfromtimestamp(first_move_ts / 1000)

    offset = (first_move_time - video_start_time).total_seconds()
    if offset < 0:
        raise ValueError("Первый ход был раньше начала видео — проверь синхронизацию")

    print(f"Первый ход был на {offset:.2f} секунде видео")
    return offset

def merge_close_timestamps(timestamps: List[Tuple[float, float]], gap: float = 10) -> List[Tuple[float, float]]:
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


async def extract_move_timestamps(pgn_file: str, start_move: int, end_move: int, first_move_time: float) -> List[Tuple[float, float]]:
    """Извлекает временные метки ходов из PGN и объединяет близкие фрагменты (асинхронно)"""
    try:
        async with aiofiles.open(pgn_file, "r", encoding="utf-8") as f:
            content = await f.read()
            from io import StringIO
            pgn_io = StringIO(content)
            game = chess.pgn.read_game(pgn_io)
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
                    current_node_for_start = game
                    first_ts_in_pgn = None
                    while current_node_for_start.variations:
                         n_node = current_node_for_start.variations[0]
                         if n_node.comment:
                              m = re.search(r"\[%ts (\d+)\]", n_node.comment)
                              if m:
                                   first_ts_in_pgn = int(m.group(1))
                                   break
                         current_node_for_start = n_node
                    if first_ts_in_pgn is None:
                         raise ValueError("Не найден ни один timestamp [%ts] в PGN для точки отсчета")
                    elapsed_time = timestamp - first_ts_in_pgn
                    elapsed_time_td = timedelta(milliseconds=elapsed_time)
                    timestamp_sec = elapsed_time_td.total_seconds() + first_move_time

                    if start_move <= move_number <= end_move:
                        start_sec = max(0, timestamp_sec - 3)
                        duration = 6
                        timestamps.append((start_sec, duration))

            if move_number >= end_move:
                break

            node = next_node

            if node.comment and re.search(r"\[%ts (\d+)\]", node.comment):
                 move_number += 1

        return merge_close_timestamps(timestamps)
    except FileNotFoundError:
        raise FileNotFoundError(f"PGN файл не найден: {pgn_file}")


async def run_ffmpeg_command(command: List[str]) -> None:
    """Асинхронно запускает команду ffmpeg"""
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        print(f"Ошибка выполнения ffmpeg (код {process.returncode}):")
        if stderr:
            print(stderr.decode(errors='ignore'))
        raise RuntimeError(f"ffmpeg завершился с ошибкой: {' '.join(command)}")


async def cut_video_ffmpeg(video_path: str, timestamps: List[Tuple[float, float]], output_path: str) -> None:
    """Вырезает фрагменты и склеивает их в одно видео (асинхронно)"""
    temp_files: List[str] = []
    cut_tasks = []
    for i, (start, duration) in enumerate(timestamps):
        temp_file = f"cut_part_{i}.mp4"
        temp_files.append(temp_file)
        cut_command = [
            "ffmpeg", "-y", "-ss", str(start), "-i", video_path, "-t", str(duration),
            "-map", "0",
            "-c", "copy", "-avoid_negative_ts", "make_zero",
             temp_file
        ]
        cut_tasks.append(run_ffmpeg_command(cut_command))
    await asyncio.gather(*cut_tasks)
    list_file_path = "file_list.txt"
    try:
        async with aiofiles.open(list_file_path, "w", encoding="utf-8") as f:
            for temp in temp_files:
                safe_temp_path = temp.replace("'", "'\\''")
                await f.write(f"file '{safe_temp_path}'\n")
        merge_command = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file_path,
            "-c", "copy", output_path
        ]
        await run_ffmpeg_command(merge_command)

    finally:
        delete_tasks = []
        for temp in temp_files:
             delete_tasks.append(aiofiles.os.remove(temp))
        if os.path.exists(list_file_path):
            delete_tasks.append(aiofiles.os.remove(list_file_path))
        results = await asyncio.gather(*delete_tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, Exception):
                print(f"Ошибка при удалении временного файла: {result}")
    print(f"Финальное видео сохранено в {output_path}")


async def main():
    import time
    start_time = time.perf_counter()
    video_file: str = "1740905773552-1740906269417.mp4"
    pgn_file: str = "_1_Safmar_Rapid_C_Kavalenya_Ivan_Leonidovich_Serov_Timofej_Andreevich.pgn"
    output_file: str = "result_async.mp4"
    start_move_num = 1
    end_move_num = 10

    try:
        first_move_offset: float = await calculate_offset_in_video(video_file, pgn_file)

        timestamps: List[Tuple[float, float]] = await extract_move_timestamps(
            pgn_file=pgn_file,
            start_move=start_move_num,
            end_move=end_move_num,
            first_move_time=first_move_offset
        )

        if not timestamps:
            return
        await cut_video_ffmpeg(video_file, timestamps, output_file)
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        print(f"Произошла ошибка: {e}")
    finally:
        end_time = time.perf_counter()
        print(f"Общее время выполнения: {end_time - start_time:.2f} секунд")


if __name__ == "__main__":
    asyncio.run(main())