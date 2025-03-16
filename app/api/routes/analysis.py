from typing import Annotated, List

from fastapi import Depends, APIRouter, BackgroundTasks, HTTPException, Path, status

from app import User, Task, TaskType, TaskStatus
from app.api.dependencies import get_current_user, get_uow
from app.core.DTO import AnalysisResponseSchema, HighlightResponseSchema
from app.db import SQLAlchemyUnitOfWork
from app.utils.helpers import run_analysis

router = APIRouter(tags=["analysis"])


@router.post("/games/{game_id}/analysis",
             response_model=AnalysisResponseSchema,
             status_code=status.HTTP_202_ACCEPTED)
async def start_game_analysis(
        game_id: int,
        background_tasks: BackgroundTasks,
        uow: Annotated[SQLAlchemyUnitOfWork, Depends(get_uow)],
        current_user: Annotated[User, Depends(get_current_user)],
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
        user_id=current_user.id
    )

    await uow.task.create(analysis_task)
    await uow.commit()

    background_tasks.add_task(run_analysis, game_id, analysis_task.id)

    return analysis_task


@router.get("/games/{game_id}/analysis/status",
            response_model=AnalysisResponseSchema)
async def get_analysis_status(
        game_id: Annotated[int, Path()],
        uow: Annotated[SQLAlchemyUnitOfWork, Depends(get_uow)],
        current_user: Annotated[User, Depends(get_current_user)]
):
    task = await uow.task.get_by_game_id(game_id)
    return task


@router.get("/games/{game_id}/analysis/result",
            response_model=List[HighlightResponseSchema])
async def get_analysis_result(
        game_id: Annotated[int, Path()],
        uow: Annotated[SQLAlchemyUnitOfWork, Depends(get_uow)],
        current_user: Annotated[User, Depends(get_current_user)]
):
    game = await uow.game.get_all(id=game_id, user_id=current_user.id)
    if not game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")

    game = game[0]

    return game.highlights
