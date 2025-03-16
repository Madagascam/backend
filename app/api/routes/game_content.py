import os
from typing import Annotated, List

from fastapi import Depends, APIRouter, UploadFile, File, HTTPException, Path, status

from app import User, Video, Highlight, VideoSegment
from app.api.dependencies import get_current_user, get_uow
from app.db import SQLAlchemyUnitOfWork

router = APIRouter(tags=["game_content"], prefix="/games")


@router.post("/{game_id}/video",
             status_code=status.HTTP_201_CREATED)
async def upload_game_video(
        game_id: Annotated[int, Path()],
        video_file: Annotated[UploadFile, File(...)],
        uow: Annotated[SQLAlchemyUnitOfWork, Depends(get_uow)],
        current_user: Annotated[User, Depends(get_current_user)],
):
    game = await uow.game.get_all(id=game_id, user_id=current_user.id)
    if not game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")

    os.makedirs("uploads/videos", exist_ok=True)

    video_path = f"uploads/videos/{game_id}_{video_file.filename}"
    with open(video_path, "wb") as f:
        f.write(await video_file.read())

    video = Video(
        original_video_url=video_path,
        processed_video_url="",  # Will be updated after processing
        status="uploaded",
        game_id=game_id
    )

    await uow.video.create(video)
    await uow.commit()

    return {"message": "Video uploaded successfully", "video_id": video.id}


@router.get("/{game_id}/highlights",
            status_code=status.HTTP_200_OK,
            response_model=List[Highlight])
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
            response_model=List[VideoSegment])
async def get_video_segments(
        game_id: Annotated[int, Path()],
        uow: Annotated[SQLAlchemyUnitOfWork, Depends(get_uow)],
        current_user: Annotated[User, Depends(get_current_user)]
):
    game = await uow.game.get_all(id=game_id, user_id=current_user.id)
    if not game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")

    game = game[0]

    return [highlight.video_segment for highlight in game.highlights]
