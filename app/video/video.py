import cv2
import numpy as np
from pydantic import BaseModel


class TrimVideoRequest(BaseModel):
    input_path: str
    output_path: str
    start_sec: float
    end_sec: float


def trim_video(request: TrimVideoRequest) -> dict:
    cap = cv2.VideoCapture(request.input_path)
    if not cap.isOpened():
        return {"Error": "Ошибка: не удалось открыть видео"}
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    start_frame = int(request.start_sec * fps)
    end_frame = int(request.end_sec * fps)
    if start_frame >= total_frames or end_frame > total_frames or start_frame >= end_frame:
        return {"Error": "Ошибка: некорректные значения start_sec и end_sec"}
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(request.output_path, fourcc, fps, (width, height))
    for frame_num in range(start_frame, end_frame):
        ret, frame = cap.read()
        if not ret:
            break
        out.write(frame)
    cap.release()
    out.release()
    return {"message": f"Видео сохранено как {request.output_path}"}


def detect_board_by_edges(frame: np.ndarray) -> np.ndarray | None:
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
            if 40000 < area < 500000:
                return approx
    return None


def extract_board_region(frame: np.ndarray, board_contour: np.ndarray) -> np.ndarray:
    pts = np.array([p[0] for p in board_contour], dtype="float32")
    size = 400
    dst_pts = np.array([[0, 0], [size - 1, 0], [size - 1, size - 1], [0, size - 1]], dtype="float32")
    M = cv2.getPerspectiveTransform(pts, dst_pts)
    return cv2.warpPerspective(frame, M, (size, size))


def detect_changes_only_in_board(frame: np.ndarray, prev_frame: np.ndarray, board_contour: np.ndarray) -> bool:
    board = extract_board_region(frame, board_contour)
    prev_board = extract_board_region(prev_frame, board_contour)
    board_gray = cv2.cvtColor(board, cv2.COLOR_BGR2GRAY)
    prev_board_gray = cv2.cvtColor(prev_board, cv2.COLOR_BGR2GRAY)
    diff = cv2.absdiff(board_gray, prev_board_gray)
    _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
    kernel = np.ones((3, 3), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    num_changes = np.sum(thresh == 255)
    base_threshold = board_gray.size * 0.02
    return num_changes > base_threshold


def detect_first_move(video_path: str):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {"Error": "Ошибка: не удалось открыть видео"}
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_skip_initial = int(fps * 2)
    frame_skip_fine = int(fps / 2)
    frame_skip = frame_skip_initial
    prev_frame = None
    frame_counter = 0
    move_detected = False
    move_time = None
    stability_frames = 5
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
                    frame_skip = frame_skip_fine
                stable_frames_count = 0
            else:
                stable_frames_count += 1
            if last_change_time and stable_frames_count >= stability_frames:
                move_detected = True
                move_time = last_change_time
                break
        prev_frame = frame
    cap.release()
    return {"message": f"Первый ход зафиксирован на {move_time:.2f} секунде"} if move_detected else {
        "message": "Первый ход не обнаружен."}


request = TrimVideoRequest(input_path="video_part.MP4", output_path="output.MP4", start_sec=1020, end_sec=1025)
print(trim_video(request))
print(detect_first_move("v_part2.MP4"))




