import asyncio
import os
from datetime import datetime

from loguru import logger

from app import TaskStatus, Highlight, VideoSegment
from app.core import ChessAnalysisInterface
from app.core.analysis_base.analysis_interface import StrategyType
from app.db import get_sql_sessionmaker, SQLAlchemyUnitOfWork
from app.video import *


async def run_analysis(game_id: int, task_id: int):
    logger.info(f"Running analysis for game with id: {game_id}")

    async with SQLAlchemyUnitOfWork(get_sql_sessionmaker()) as uow:
        try:
            task = await uow.task.get(task_id)
            task.status = TaskStatus.PROCESSING
            await uow.commit()

            game = await uow.game.get(game_id)

            strategy_type = task.strategy_type or StrategyType.ANALYTICS
            logger.info(f"Using strategy: {strategy_type} for game with id: {game_id}")
            
            analysis = ChessAnalysisInterface()

            # Устанавливаем стратегию анализа
            analysis.set_strategy(strategy_type)

            # Используем выбранную стратегию для анализа
            results = await analysis.analyze_game(game.pgn_data)

            for result in results:
                highlight = Highlight(
                    start_move=result[0],
                    end_move=result[1],
                    description="Not provided",
                    detected_by=strategy_type,
                    game_id=game_id
                )
                await uow.highlight.create(highlight)

            task.status = TaskStatus.COMPLETED
            logger.info(f"Analysis completed for game with id: {game_id} using strategy: {strategy_type}")
            await uow.commit()

        except Exception as e:
            logger.error(f"Error during analysis for game with id: {game_id}: {e}")

            task = await uow.task.get(task_id)
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            await uow.commit()


async def run_video_cut(game_id: int, task_id: int, analysis_task_id: int):
    logger.info(f"Running video cutting for game with id: {game_id}")

    async with SQLAlchemyUnitOfWork(get_sql_sessionmaker()) as uow:
        try:
            # Wait for analysis task to complete
            analysis_task = await uow.task.get(analysis_task_id)
            while analysis_task.status != TaskStatus.COMPLETED:
                logger.info(f"Waiting for analysis task with id: {analysis_task_id} to complete")
                await asyncio.sleep(3)
                await uow.session.refresh(analysis_task)

            # Update task status to processing
            task = await uow.task.get(task_id)
            task.status = TaskStatus.PROCESSING
            await uow.commit()

            # Get game data and videos
            game = await uow.game.get(game_id)
            videos = game.videos

            if not videos:
                raise ValueError(f"No videos found for game with id: {game_id}")

            logger.info(f"Found {len(videos)} videos for game with id: {game_id}")

            # Get all highlights for the game
            highlights = game.highlights

            if not highlights:
                logger.warning(f"No highlights found for game with id: {game_id}")
                task.status = TaskStatus.COMPLETED
                await uow.commit()
                return

            # Process each video to extract timestamp information
            video_ranges = []
            for video in videos:
                try:
                    # Parse video filename to get timestamps
                    start_ts, end_ts = await parse_video_filename(video.original_video_url)

                    video_ranges.append({
                        'video': video,
                        'filepath': video.original_video_url,
                        'start_ts': start_ts,
                        'end_ts': end_ts,
                        'start_datetime': datetime.utcfromtimestamp(start_ts / 1000),
                        'end_datetime': datetime.utcfromtimestamp(end_ts / 1000)
                    })
                except Exception as e:
                    logger.warning(f"Could not parse video filename {video.original_video_url}: {e}")

            # Sort videos by start time
            video_ranges.sort(key=lambda x: x['start_ts'])

            if not video_ranges:
                raise ValueError("No valid videos found after processing filenames")

            # Extract move timestamps from PGN
            move_timestamps = await extract_move_timestamps_from_pgn(game.pgn_data)

            if not move_timestamps:
                raise ValueError("No move timestamps found in PGN data")

            logger.info(f"Extracted {len(move_timestamps)} move timestamps from PGN")

            # Process each highlight
            for highlight in highlights:
                logger.info(f"Processing highlight {highlight.id}: {highlight.start_move} to {highlight.end_move}")

                try:
                    # Find segments for this highlight
                    segments = await find_segments_for_highlight(
                        highlight_start_move=highlight.start_move,
                        highlight_end_move=highlight.end_move,
                        move_timestamps=move_timestamps,
                        video_ranges=video_ranges
                    )

                    if not segments:
                        logger.warning(f"No segments found for highlight {highlight.id}")
                        continue

                    # Merge close or overlapping segments
                    merged_segments = await merge_segments(segments)

                    logger.info(f"Cutting {len(merged_segments)} segments for highlight {highlight.id}")

                    # Prepare output file path
                    output_dir = os.path.join("media", "highlights")
                    output_file = os.path.join(output_dir, f"highlight_{game_id}_{highlight.id}.mp4")

                    # Cut and merge video segments
                    success = await cut_and_merge_video_segments(
                        segments=merged_segments,
                        output_file=output_file
                    )

                    if success:
                        # Create video segment record
                        total_duration = sum(segment['duration'] for segment in merged_segments)

                        video_segment = VideoSegment(
                            start_time=0,  # Start time in the output video
                            end_time=int(total_duration),
                            video_id=merged_segments[0]['video'].id,  # Link to the first video used
                            highlight_id=highlight.id,
                            url=output_file
                        )
                        await uow.video_segment.create(video_segment)

                        logger.info(f"Created highlight video: {output_file}")
                    else:
                        logger.error(f"Failed to create highlight video for highlight {highlight.id}")

                except Exception as e:
                    logger.error(f"Error processing highlight {highlight.id}: {e}")

            # Update task status
            task.status = TaskStatus.COMPLETED
            await uow.commit()
            logger.info(f"Video cutting completed for game with id: {game_id}")

        except Exception as e:
            logger.error(f"Error during video cutting for game with id: {game_id}: {e}")

            task = await uow.task.get(task_id)
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            await uow.commit()
