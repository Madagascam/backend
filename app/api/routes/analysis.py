from typing import Annotated

from fastapi import Depends, APIRouter, BackgroundTasks, HTTPException, Path, status, Body
from loguru import logger

from app import User, Task, TaskType, TaskStatus
from app.api.dependencies import get_current_user, get_uow
from app.core.DTO import AnalysisResponseSchema, HighlightResponseSchema, AnalysisResultResponseSchema, AnalysisRequest
from app.db import SQLAlchemyUnitOfWork
from app.utils.helpers import run_analysis, run_video_cut

router = APIRouter(tags=["Analysis"], prefix="/api/games/{game_id}/analysis")


@router.post("/",
             response_model=AnalysisResponseSchema,
             status_code=status.HTTP_202_ACCEPTED,
             summary="Start game analysis")
async def start_game_analysis(
        uow: Annotated[SQLAlchemyUnitOfWork, Depends(get_uow)],
        current_user: Annotated[User, Depends(get_current_user)],
        game_id: Annotated[int, Path(title='Id of the game to analyze')],
        background_tasks: BackgroundTasks,
        analysis_request: Annotated[AnalysisRequest, Body()]
):
    game = await uow.game.get_all(id=game_id, user_id=current_user.id)
    if not game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")

    game = game[0]

    if not game.pgn_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="PGN data is required for analysis")

    analysis_task = Task(
        type=TaskType.GAME_ANALYSIS,
        status=TaskStatus.PENDING,
        game_id=game_id,
        user_id=current_user.id,
        strategy_type=analysis_request.strategy_type
    )

    await uow.task.create(analysis_task)
    background_tasks.add_task(run_analysis, game_id, analysis_task.id)

    response = AnalysisResponseSchema(
        analysis_id=analysis_task.id,
        video_id=-1
    )

    if analysis_request.create_video is True:
        video_task = Task(
            type=TaskType.VIDEO_PROCESSING,
            status=TaskStatus.PENDING,
            game_id=game_id,
            user_id=current_user.id,
        )

        await uow.task.create(video_task)
        background_tasks.add_task(run_video_cut, game_id, video_task.id, analysis_task.id)
        response.video_id = video_task.id

    await uow.commit()

    logger.info(
        f"Added analysis task with id: {analysis_task.id} for game with id: {game_id} with strategy: {analysis_task.strategy_type}")

    return response


@router.get("/result",
            response_model=AnalysisResultResponseSchema,
            summary="Get analysis results")
async def get_analysis_result(
        game_id: Annotated[int, Path(title='Id of the game to analyze')],
        uow: Annotated[SQLAlchemyUnitOfWork, Depends(get_uow)],
        current_user: Annotated[User, Depends(get_current_user)]
):
    game = await uow.game.get_all(id=game_id, user_id=current_user.id)
    if not game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")

    game = game[0]

    logger.info(f"Got analysis results for game with id: {game_id}")

    return AnalysisResultResponseSchema(pgn_data=game.pgn_data,
                                        highlights=[HighlightResponseSchema.model_validate(hi) for hi in
                                                    game.highlights])