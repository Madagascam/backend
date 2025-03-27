import chess.pgn
import cv2
import numpy as np
import subprocess
import os
import re
import chess.pgn
from datetime import timedelta


def detect_board_by_edges(frame: np.ndarray) -> np.ndarray | None:
    """Определяет границы шахматной доски, отсекая лишние контуры"""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    contrast = np.std(gray)
    if contrast < 30:
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    edges = cv2.Canny(blurred, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for contour in contours:
        approx = cv2.approxPolyDP(contour, 0.03 * cv2.arcLength(contour, True), True)
        if len(approx) == 4:
            area = cv2.contourArea(approx)
            if 60000 < area < 300000:
                return approx
    return None


def extract_board_region(frame: np.ndarray, board_contour: np.ndarray) -> np.ndarray:
    """Извлекает область шахматной доски и убирает 5% краев для уменьшения ложных изменений"""
    pts = np.array([p[0] for p in board_contour], dtype="float32")
    size = 400
    dst_pts = np.array([[0, 0], [size - 1, 0], [size - 1, size - 1], [0, size - 1]], dtype="float32")
    M = cv2.getPerspectiveTransform(pts, dst_pts)
    board = cv2.warpPerspective(frame, M, (size, size))
    crop_margin = int(size * 0.05)
    return board[crop_margin:-crop_margin, crop_margin:-crop_margin]


def detect_changes_only_in_board(frame: np.ndarray, prev_frame: np.ndarray, board_contour: np.ndarray) -> bool:
    """Определяет, произошло ли изменение на шахматной доске, уменьшая чувствительность"""
    board = extract_board_region(frame, board_contour)
    prev_board = extract_board_region(prev_frame, board_contour)
    board_gray = cv2.cvtColor(board, cv2.COLOR_BGR2GRAY)
    prev_board_gray = cv2.cvtColor(prev_board, cv2.COLOR_BGR2GRAY)
    board_gray = cv2.GaussianBlur(board_gray, (5, 5), 0)
    prev_board_gray = cv2.GaussianBlur(prev_board_gray, (5, 5), 0)
    diff = cv2.absdiff(board_gray, prev_board_gray)
    _, thresh = cv2.threshold(diff, 35, 255, cv2.THRESH_BINARY)
    kernel = np.ones((3, 3), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    num_changes = np.sum(thresh == 255)
    base_threshold = board_gray.size * 0.05
    return num_changes > base_threshold


def detect_first_move(video_path: str):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {"Error": "Ошибка: не удалось открыть видео"}
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_skip_initial = 10
    frame_skip_fine = 2
    frame_skip = frame_skip_initial
    prev_frame = None
    frame_counter = 0
    move_detected = False
    move_time = None
    stability_frames = 2
    stable_frames_count = 0
    last_change_time = None
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame_counter += 1
        if frame_counter % frame_skip != 0:
            continue
        board_contour = detect_board_by_edges(frame)
        if board_contour is None:
            continue
        if prev_frame is not None:
            if detect_changes_only_in_board(frame, prev_frame, board_contour):
                if last_change_time is None:
                    last_change_time = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
                    frame_skip = frame_skip_fine  # Уменьшаем шаг для точности
                stable_frames_count = 0
            else:
                stable_frames_count += 1

            if last_change_time and stable_frames_count >= stability_frames:
                move_detected = True
                move_time = last_change_time
                break
        prev_frame = frame
    cap.release()
    print("Нашли первый ход")
    return move_time if move_detected else None


def merge_close_timestamps(timestamps, gap=10):
    """Объединяет временные отрезки, если между ними менее gap секунд"""
    if not timestamps:
        return []

    merged = [timestamps[0]]

    for start, duration in timestamps[1:]:
        prev_start, prev_duration = merged[-1]
        prev_end = prev_start + prev_duration

        if start - prev_end <= gap:
            merged[-1] = (prev_start, (start + duration) - prev_start)
        else:
            merged.append((start, duration))

    return merged


def extract_move_timestamps(pgn_file, start_move, end_move, first_move_time):
    """Извлекает временные метки ходов из PGN и объединяет близкие фрагменты"""
    with open(pgn_file, "r", encoding="utf-8") as f:
        game = chess.pgn.read_game(f)
    if not game:
        raise ValueError("Не удалось загрузить партию из PGN")

    timestamps = []
    node = game
    start_time = None
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
                elapsed_time = timedelta(milliseconds=elapsed_time)
                timestamp_sec = elapsed_time.total_seconds() + first_move_time

                if start_move <= move_number <= end_move:
                    start_sec = max(0, timestamp_sec - 3)
                    duration = 6
                    timestamps.append((start_sec, duration))

        if move_number >= end_move:
            break

        node = next_node
        move_number += 1

    return merge_close_timestamps(timestamps)


def cut_video_ffmpeg(video_path, timestamps, output_path):
    """Вырезает фрагменты и склеивает их в одно видео"""
    temp_files = []

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


files = [
    ("_1_Moscow_Open_2024_Turnir_A_eh_tap_Kubka_Rossii_po_shahmatam_sredi.pgn", "video.MP4", "output_1.MP4", 10, 13, 1440),
    ("11_table.pgn", "11_table_2.MP4", "output_2.MP4", 38, 47, 625),
    ("1_table.pgn", "1_table_1.MP4", "output_3.MP4", 34, 49, 2596)
]

for pgn_file, video_file, output_video, start_move, end_move, first_move_time in files:
    timestamps = extract_move_timestamps(pgn_file, start_move, end_move, first_move_time)
    cut_video_ffmpeg(video_file, timestamps, output_video)

