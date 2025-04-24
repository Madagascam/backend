import os
from typing import Annotated, List

from fastapi import Depends, APIRouter, HTTPException, Path, status, Body
from fastapi.responses import FileResponse

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
            response_model=VideoSegmentResponseSchema,
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
    highlights = []
    video_segments = []

    for highlight in game.highlights:
        highlights.append(HighlightResponseSchema.model_validate(highlight))
        video_segments.append(highlight.video_segment.id)

    return VideoSegmentResponseSchema(
        highlights=highlights,
        video_segments=video_segments,
    )


@router.get("/{game_id}/video-segments/{segment_id}/stream",
            summary="Stream a video segment")
async def stream_video_segment(
        game_id: Annotated[int, Path()],
        segment_id: Annotated[int, Path()],
        uow: Annotated[SQLAlchemyUnitOfWork, Depends(get_uow)],
        current_user: Annotated[User, Depends(get_current_user)]
):
    # Проверка доступа к игре
    game = await uow.game.get_all(id=game_id, user_id=current_user.id)
    if not game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")

    # Получение сегмента видео
    video_segment = await uow.video_segment.get(segment_id)
    if not video_segment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video segment not found")

    # Проверка принадлежности сегмента к указанной игре
    highlight = video_segment.highlight
    if highlight.game_id != game_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Video segment does not belong to this game")

    # Проверка наличия URL
    if not video_segment.url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Video URL not found")

    # Если путь является локальным файлом
    if os.path.isfile(video_segment.url):
        return FileResponse(video_segment.url,
                            media_type="video/mp4",
                            filename=f"segment_{segment_id}.mp4")

    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Video file not found")
