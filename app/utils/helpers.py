from app import TaskStatus, Highlight
from app.db import get_sql_sessionmaker, SQLAlchemyUnitOfWork


async def run_analysis(game_id: int, task_id: int):
    async with SQLAlchemyUnitOfWork(get_sql_sessionmaker()) as uow:
        try:
            task = await uow.task.get(task_id)
            task.status = TaskStatus.PROCESSING
            await uow.commit()

            # game = await uow.game.get(game_id)
            # result = await analyze_game(game.pgn_data)

            results = [[10, 15, "WOW horse dies"], [18, 20, "РокировОчка"]]

            for result in results:
                highlight = Highlight(
                    start_move=result[0],
                    end_move=result[1],
                    description=result[2],
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
