from app import TaskStatus, Highlight
from app.db import get_sql_sessionmaker, SQLAlchemyUnitOfWork
from app.ml import ChessAnalysisInterface


async def run_analysis(game_id: int, task_id: int):
    async with SQLAlchemyUnitOfWork(get_sql_sessionmaker()) as uow:
        try:
            task = await uow.task.get(task_id)
            task.status = TaskStatus.PROCESSING
            await uow.commit()

            game = await uow.game.get(game_id)

            analysis = ChessAnalysisInterface()
            results = await analysis.analyze_game(game.pgn_data)

            for result in results:
                highlight = Highlight(
                    start_move=result[0],
                    end_move=result[1],
                    description=result[2] if len(result) > 2 else "Not provided",
                    game_id=game_id
                )
                await uow.highlight.create(highlight)

            task.status = TaskStatus.COMPLETED
            await uow.commit()

        except Exception as e:
            task = await uow.task.get(task_id)
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            await uow.commit()
