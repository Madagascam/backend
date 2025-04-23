import asyncio

from loguru import logger

from app import TaskStatus, Highlight
from app.core import ChessAnalysisInterface
from app.core.analysis_base.analysis_interface import StrategyType
from app.db import get_sql_sessionmaker, SQLAlchemyUnitOfWork


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
            analysis_task = await uow.task.get(analysis_task_id)
            while analysis_task.status != TaskStatus.COMPLETED:
                logger.info(f"Waiting for analysis task with id: {analysis_task_id} to complete")
                await asyncio.sleep(3)
                await uow.session.refresh(analysis_task)

            task = await uow.task.get(task_id)
            task.status = TaskStatus.PROCESSING

            videos = await uow.video.get_all(game_id=game_id)
            print(videos)
            print('aboba')

        except Exception as e:
            ...
