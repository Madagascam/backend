import io
import os
import re
import subprocess
import tempfile
from datetime import datetime
from typing import List, Tuple, Dict, Any

import chess.pgn


async def parse_video_filename(filename: str) -> Tuple[int, int]:
    """
    Parses video filename in format <start_ts>-<end_ts>.<ext> and returns
    start and end timestamps in milliseconds
    """
    base = os.path.basename(filename)
    match = re.match(r"(\d+)-(\d+)\.\w+", base)
    if not match:
        raise ValueError("Video filename must be in format <start_ts>-<end_ts>.<extension>")

    start_timestamp = int(match.group(1))  # milliseconds
    end_timestamp = int(match.group(2))  # milliseconds
    return start_timestamp, end_timestamp


async def extract_move_timestamps_from_pgn(pgn_data: str) -> Dict[int, int]:
    """Extracts timestamps for each move from PGN data"""
    pgn_io = io.StringIO(pgn_data)
    game = chess.pgn.read_game(pgn_io)

    if not game:
        raise ValueError("Could not parse PGN data")

    move_timestamps = {}
    node = game
    move_number = 0

    while node.variations:
        next_node = node.variations[0]
        move_number += 1

        if next_node.comment:
            ts_match = re.search(r"\[%ts (\d+)\]", next_node.comment)
            if ts_match:
                move_timestamps[move_number] = int(ts_match.group(1))

        node = next_node

    return move_timestamps


async def find_segments_for_highlight(
        highlight_start_move: str,
        highlight_end_move: str,
        move_timestamps: Dict[int, int],
        video_ranges: List[Dict[str, Any]],
        buffer_before: float = 3.0,
        buffer_after: float = 3.0
) -> List[Dict[str, Any]]:
    """
    Finds video segments that correspond to a highlight

    Args:
        highlight_start_move: Move notation (e.g. "15w")
        highlight_end_move: Move notation (e.g. "23b")
        move_timestamps: Dictionary mapping move numbers to timestamps
        video_ranges: List of video info dictionaries
        buffer_before: Seconds to include before the move
        buffer_after: Seconds to include after the move

    Returns:
        List of segment dictionaries with video, start time, duration
    """
    # Parse move numbers from notation
    start_move_color = highlight_start_move[-1]
    start_move_num = int(highlight_start_move[:-1])
    end_move_color = highlight_end_move[-1]
    end_move_num = int(highlight_end_move[:-1])

    start_move = (start_move_num - 1) * 2 + (1 if start_move_color == 'W' else 2)
    end_move = (end_move_num - 1) * 2 + (1 if end_move_color == 'W' else 2)

    # Get timestamps for moves in this highlight
    highlight_move_timestamps = []
    for move_num in range(start_move, end_move + 1):
        if move_num in move_timestamps:
            highlight_move_timestamps.append((move_num, move_timestamps[move_num]))

    if not highlight_move_timestamps:
        return []

    # Convert move timestamps to video-relative times
    segments_to_cut = []

    for move_num, move_ts in highlight_move_timestamps:
        move_datetime = datetime.utcfromtimestamp(move_ts / 1000)

        # Find which video contains this move
        for video_range in video_ranges:
            if video_range['start_datetime'] <= move_datetime <= video_range['end_datetime']:
                # Calculate time relative to video start (in seconds)
                time_in_video = (move_datetime - video_range['start_datetime']).total_seconds()

                # Add buffer around the move
                start_sec = max(0, time_in_video - buffer_before)
                duration = buffer_before + buffer_after

                segments_to_cut.append({
                    'video': video_range['video'],
                    'filepath': video_range['filepath'],
                    'start': start_sec,
                    'duration': duration,
                    'move_number': move_num
                })
                break

    return segments_to_cut


async def merge_segments(segments: List[Dict[str, Any]], gap_threshold: float = 10) -> List[Dict[str, Any]]:
    """
    Merges overlapping or close segments that are in the same video

    Args:
        segments: List of segment dictionaries
        gap_threshold: Maximum gap in seconds to merge segments

    Returns:
        List of merged segment dictionaries
    """
    if not segments:
        return []

    # Sort by video and start time
    segments.sort(key=lambda x: (x['video'].id, x['start']))

    merged_segments = []
    current_segment = segments[0].copy()

    for segment in segments[1:]:
        # If same video and starts before the current segment ends plus gap
        if (segment['video'].id == current_segment['video'].id and
                segment['start'] <= current_segment['start'] + current_segment['duration'] + gap_threshold):
            # Extend current segment
            new_end = max(
                current_segment['start'] + current_segment['duration'],
                segment['start'] + segment['duration']
            )
            current_segment['duration'] = new_end - current_segment['start']
        else:
            # Start a new segment
            merged_segments.append(current_segment)
            current_segment = segment.copy()

    merged_segments.append(current_segment)
    return merged_segments


async def cut_and_merge_video_segments(
        segments: List[Dict[str, Any]],
        output_file: str
) -> bool:
    """
    Cuts segments from videos and merges them into a single output file

    Args:
        segments: List of segment dictionaries (video, filepath, start, duration)
        output_file: Path to save the final merged video

    Returns:
        True if successful, False otherwise
    """
    if not segments:
        return False

    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Create temporary directory for processing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Cut each segment
        temp_files = []
        for i, segment in enumerate(segments):
            temp_file = os.path.join(temp_dir, f"segment_{i}.mp4")

            try:
                # Cut segment using ffmpeg
                cut_command = [
                    "ffmpeg", "-y", "-i", segment['filepath'],
                    "-ss", str(segment['start']),
                    "-t", str(segment['duration']),
                    "-c", "copy", temp_file
                ]
                subprocess.run(cut_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                if os.path.exists(temp_file) and os.path.getsize(temp_file) > 0:
                    temp_files.append(temp_file)
            except Exception as e:
                print(f"Error cutting segment {i}: {e}")

        if not temp_files:
            return False

        try:
            # Merge segments if multiple
            if len(temp_files) > 1:
                # Create file list for ffmpeg concat
                file_list_path = os.path.join(temp_dir, "file_list.txt")
                with open(file_list_path, "w") as f:
                    for temp in temp_files:
                        f.write(f"file '{temp}'\n")

                # Merge files
                merge_command = [
                    "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                    "-i", file_list_path, "-c", "copy", output_file
                ]
                subprocess.run(merge_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                # Just copy the single file
                import shutil
                shutil.copy2(temp_files[0], output_file)

            return os.path.exists(output_file) and os.path.getsize(output_file) > 0
        except Exception as e:
            print(f"Error merging segments: {e}")
            return False
