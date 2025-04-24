import io
from datetime import datetime
from typing import Annotated, List, Optional

import chess.pgn
from fastapi import Form, Depends, APIRouter, UploadFile, File, HTTPException, status, Path

from app import User, Game, Video
from app.api.dependencies import get_current_user, get_uow
from app.core.DTO import GameResponseSchema, HighlightResponseSchema, \
    GameWithHighlightsResponseSchema
from app.db import SQLAlchemyUnitOfWork

router = APIRouter(tags=["Games Managment"], prefix="/api/games")


@router.post("/",
             response_model=GameResponseSchema,
             status_code=status.HTTP_201_CREATED,
             summary="Create a new game with provided PGN data",
             description="This endpoint has two purposes: create a new game and accept related pgn file")
async def create_game_with_pgn(
        uow: Annotated[SQLAlchemyUnitOfWork, Depends(get_uow)],
        current_user: Annotated[User, Depends(get_current_user)],
        title: Annotated[str, Form(...)],
        pgn_file: Annotated[UploadFile, File(...)],
        video_links: Annotated[Optional[List[str]], Form()] = None,
):
    if video_links is None:
        video_links = []

    pgn_content = await pgn_file.read()
    pgn_text = pgn_content.decode("utf-8")

    pgn_data = pgn_text.split("\n\n")[-1]

    pgn_io = io.StringIO(pgn_text)
    chess_game = chess.pgn.read_game(pgn_io)

    if not chess_game:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid PGN file")

    white_player = chess_game.headers.get("White", "Unknown")
    black_player = chess_game.headers.get("Black", "Unknown")
    event_name = chess_game.headers.get("Event", "Unknown")
    game_date = chess_game.headers.get("UTCDate", datetime.now().strftime("%Y.%m.%d"))

    game = Game(
        title=title,
        event=event_name,
        date=datetime.strptime(game_date, "%Y.%m.%d") if "." in game_date else datetime.now(),
        white_player=white_player,
        black_player=black_player,
        pgn_data=pgn_data,
        user_id=current_user.id
    )

    await uow.game.create(game)

    # Create videos from the provided links
    for link in video_links:
        video = Video(
            original_video_url=link,
            processed_video_url="",  # Will be updated after processing
            status="uploaded",
            game_id=game.id
        )
        await uow.video.create(video)
    
    await uow.commit()

    return game


@router.get("/",
            response_model=List[GameResponseSchema],
            status_code=status.HTTP_200_OK,
            summary="List all games for auth user")
async def list_games(
        uow: Annotated[SQLAlchemyUnitOfWork, Depends(get_uow)],
        current_user: Annotated[User, Depends(get_current_user)],
):
    return await uow.game.get_all(user_id=current_user.id)


@router.get("/{game_id}",
            response_model=GameWithHighlightsResponseSchema,
            status_code=status.HTTP_200_OK,
            summary="Get game with provided game_id details")
async def get_game(
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
        video_segments.append(highlight.video_segment.id if highlight.video_segment else -1)

    return GameWithHighlightsResponseSchema(
        game=GameResponseSchema.model_validate(game),
        highlights=highlights,
        video_segments=video_segments
    )


@router.delete("/{game_id}",
               status_code=status.HTTP_204_NO_CONTENT,
               summary="Delete a game with provided game_id")
async def delete_game(
        game_id: Annotated[int, Path()],
        uow: Annotated[SQLAlchemyUnitOfWork, Depends(get_uow)],
        current_user: Annotated[User, Depends(get_current_user)]
):
    game = await uow.game.get(game_id)
    if not game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")

    await uow.game.delete(game)
    await uow.commit()
