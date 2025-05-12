import os
import re
import chess.pgn
import subprocess
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
import asyncio
import aiofiles
import aiofiles.os

# список видеофайлов
video_files = [
    "1740905773552-1740906269417.mp4",
    "1740906269417-1740906765263.mp4",
    "1740906765267-1740907258498.mp4",
]


def parse_video_start_end(filename: str) -> Tuple[int, int]:
    match = re.match(r"(\d+)-(\d+)\.\w+", filename)
    if not match:
        raise ValueError(f"Некорректное имя видеофайла: {filename}")
    return int(match.group(1)), int(match.group(2))


def find_video_segment(timestamp_ms: int) -> Optional[str]:
    for video_file in video_files:
        start_ms, end_ms = parse_video_start_end(video_file)
        if start_ms <= timestamp_ms < end_ms:
            return video_file
    return None


def parse_video_start_time(filename: str) -> datetime:
    start_ms, _ = parse_video_start_end(filename)
    return datetime.utcfromtimestamp(start_ms / 1000)


async def get_first_move_timestamp(pgn_file: str) -> int:
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


def merge_close_timestamps(timestamps: List[Tuple[str, float, float]], gap: float = 10) -> List[Tuple[str, float, float]]:
    if not timestamps:
        return []
    timestamps.sort(key=lambda x: (x[0], x[1]))
    merged = [timestamps[0]]
    for file, start, dur in timestamps[1:]:
        last_file, last_start, last_dur = merged[-1]
        if file == last_file and start - (last_start + last_dur) <= gap:
            merged[-1] = (last_file, last_start, (start + dur) - last_start)
        else:
            merged.append((file, start, dur))
    return merged


async def extract_move_timestamps(pgn_file: str, start_move: int, end_move: int) -> List[Tuple[str, float, float]]:
    async with aiofiles.open(pgn_file, "r", encoding="utf-8") as f:
        content = await f.read()
        from io import StringIO
        pgn_io = StringIO(content)
        game = chess.pgn.read_game(pgn_io)
        if not game:
            raise ValueError("Не удалось загрузить партию из PGN")

    node = game
    move_number = 1
    base_ts = None
    result = []
    while node.variations:
        next_node = node.variations[0]
        if next_node.comment:
            match = re.search(r"\[%ts (\d+)\]", next_node.comment)
            if match:
                ts = int(match.group(1))
                if base_ts is None:
                    base_ts = ts
                if start_move <= move_number <= end_move:
                    rel_sec = (ts - base_ts) / 1000.0
                    video_file = find_video_segment(ts)
                    if not video_file:
                        raise ValueError(f"Не найден видеофайл для timestamp {ts}")
                    video_start_ms, _ = parse_video_start_end(video_file)
                    start_in_video = (ts - video_start_ms) / 1000.0
                    result.append((video_file, max(0, start_in_video - 3), 6))
        if move_number >= end_move:
            break
        node = next_node
        if node.comment and re.search(r"\[%ts (\d+)\]", node.comment):
            move_number += 1

    return merge_close_timestamps(result)


async def run_ffmpeg_command(command: List[str]) -> None:
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE
    )
    _, stderr = await process.communicate()
    if process.returncode != 0:
        print(stderr.decode(errors='ignore'))
        raise RuntimeError(f"ffmpeg завершился с ошибкой: {' '.join(command)}")


async def cut_video_segments(timestamps: List[Tuple[str, float, float]], output_path: str) -> None:
    temp_files = []
    tasks = []
    for i, (file, start, dur) in enumerate(timestamps):
        out_name = f"cut_part_{i}.mp4"
        temp_files.append(out_name)
        cmd = ["ffmpeg", "-y", "-ss", str(start), "-i", file, "-t", str(dur), "-c", "copy", out_name]
        tasks.append(run_ffmpeg_command(cmd))
    await asyncio.gather(*tasks)
    list_file = "file_list.txt"
    async with aiofiles.open(list_file, "w") as f:
        for name in temp_files:
            await f.write(f"file '{name}'\n")
    merge_cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file, "-c", "copy", output_path]
    await run_ffmpeg_command(merge_cmd)
    await asyncio.gather(*(aiofiles.os.remove(f) for f in temp_files + [list_file]))


async def main():
    pgn_file = "_1_Safmar_Rapid_C_Kavalenya_Ivan_Leonidovich_Serov_Timofej_Andreevich.pgn"
    output_file = "result_async.mp4"
    start_move = 1
    end_move = 30
    try:
        segments = await extract_move_timestamps(pgn_file, start_move, end_move)
        if segments:
            await cut_video_segments(segments, output_file)
            print(f"Видео сохранено в {output_file}")
        else:
            print("Не найдено подходящих сегментов для вырезки")
    except Exception as e:
        print(f"Ошибка: {e}")


if __name__ == "__main__":
    asyncio.run(main())
