from typing import Annotated, List

from fastapi import Depends, APIRouter, HTTPException, Path, status, Body

from app import User, Video
from app.api.dependencies import get_current_user, get_uow
from app.core.DTO import HighlightResponseSchema, VideoSegmentResponseSchema
from app.db import SQLAlchemyUnitOfWork

router = APIRouter(tags=["Game content"], prefix="/api/games")


@router.post("/{game_id}/videos",
             status_code=status.HTTP_201_CREATED,
             summary="Add videos for a game")
async def add_game_videos(
        game_id: Annotated[int, Path()],
        video_links: Annotated[List[str], Body()],
        uow: Annotated[SQLAlchemyUnitOfWork, Depends(get_uow)],
        current_user: Annotated[User, Depends(get_current_user)],
):
    game = await uow.game.get_all(id=game_id, user_id=current_user.id)
    if not game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")

    created_videos = []

    for link in video_links:
        video = Video(
            original_video_url=link,
            processed_video_url="",  # Will be updated after processing
            status="uploaded",
            game_id=game_id
        )

        await uow.video.create(video)
        created_videos.append(video)
    
    await uow.commit()

    return {"message": f"{len(created_videos)} videos added successfully", "video_ids": [v.id for v in created_videos]}


@router.get("/{game_id}/highlights",
            status_code=status.HTTP_200_OK,
            response_model=List[HighlightResponseSchema],
            summary="Get highlights/interesting moves for a game")
async def get_highlights(
        game_id: Annotated[int, Path()],
        uow: Annotated[SQLAlchemyUnitOfWork, Depends(get_uow)],
        current_user: Annotated[User, Depends(get_current_user)]
):
    game = await uow.game.get_all(id=game_id, user_id=current_user.id)
    if not game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")

    game = game[0]

    return game.highlights


@router.get("/{game_id}/video-segments",
            status_code=status.HTTP_200_OK,
            response_model=List[VideoSegmentResponseSchema],
            summary="Get processed video segments")
async def get_video_segments(
        game_id: Annotated[int, Path()],
        uow: Annotated[SQLAlchemyUnitOfWork, Depends(get_uow)],
        current_user: Annotated[User, Depends(get_current_user)]
):
    game = await uow.game.get_all(id=game_id, user_id=current_user.id)
    if not game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")

    game = game[0]
    result = []

    # Get all videos for this game
    videos = await uow.video.get_all(game_id=game_id)
    
    for highlight in game.highlights:
        video_segment = await highlight.awaitable_attrs.video_segment
        if video_segment is not None:
            result.append(video_segment)

    return result
