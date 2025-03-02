from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import Column, DateTime
from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy.types import Enum as SQLModelEnum


class TimestampModel(SQLModel):
    created_at: datetime = Field(default=datetime.now, nullable=False)
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"nullable": False, "default": datetime.now, "onupdate": datetime.now}
    )


class UserRole(str, Enum):
    USER = "user"
    MANAGER = "manager"
    ADMIN = "admin"


class User(TimestampModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(primary_key=True, nullable=False, default=None)
    username: str
    password_hash: str
    role: UserRole = Field(sa_column=Column(SQLModelEnum(UserRole)), default=UserRole.USER)

    # One-to-many relationship with games
    games: List["Game"] = Relationship(back_populates="user")

    # One-to-many relationship with tasks
    tasks: List["Task"] = Relationship(back_populates="user")


class Game(TimestampModel, table=True):
    __tablename__ = "games"

    id: int | None = Field(primary_key=True, nullable=False, default=None)
    title: str
    event: str | None = None
    date: datetime
    white_player: str
    black_player: str
    pgn_data: str

    # Many-to-one relationship with user
    user_id: int | None = Field(default=None, foreign_key="users.id")
    user: "User" | None = Relationship(back_populates="games")

    # One-to-many relationship with highlights
    highlights: List["Highlight"] = Relationship(back_populates="game")

    # One-to-one relationship with video
    video: "Video" | None = Relationship(back_populates="game", sa_relationship_kwargs={"uselist": False})

    # One-to-many relationship with tasks
    tasks: List["Task"] = Relationship(back_populates="game")


class Highlight(TimestampModel, table=True):
    __tablename__ = "highlights"

    id: int | None = Field(primary_key=True, nullable=False, default=None)
    category: str
    start_move: int  # From pgn notation
    end_move: int  # From pgn notation
    importance_score: float
    position_before: str  # FEN notation (maybe will be removed)
    position_after: str  # FEN notation
    description: str
    detected_by: str

    # Many-to-one relationship with game
    game_id: int | None = Field(default=None, foreign_key="games.id")
    game: "Game" | None = Relationship(back_populates="highlights")

    # One-to-one relationship with video segment
    video_segment: "VideoSegment" | None = Relationship(
        sa_relationship_kwargs={"uselist": False, "back_populates": "highlight"}
    )


class Video(TimestampModel, table=True):
    __tablename__ = "videos"

    id: int | None = Field(primary_key=True, nullable=False, default=None)
    original_video_url: str
    processed_video_url: str
    status: str

    # One-to-one relationship with game
    game_id: int | None = Field(default=None, foreign_key="games.id", unique=True)
    game: "Game" | None = Relationship(back_populates="video")

    # One-to-many relationship with video segments
    segments: List["VideoSegment"] = Relationship(back_populates="video")


class VideoSegment(TimestampModel, table=True):
    __tablename__ = "video_segments"

    id: int | None = Field(primary_key=True, nullable=False, default=None)
    start_time: int
    end_time: int
    sequence_order: int

    # Many-to-one relationship with video
    video_id: int | None = Field(default=None, foreign_key="videos.id")
    video: "Video" | None = Relationship(back_populates="segments")

    # One-to-one relationship with highlight
    highlight_id: int | None = Field(default=None, foreign_key="highlights.id", unique=True)
    highlight: "Highlight" | None = Relationship(back_populates="video_segment")

class TaskType(str, Enum):
    GAME_ANALYSIS = "game_analysis"
    VIDEO_PROCESSING = "video_processing"
    HIGHLIGHT_DETECTION = "highlight_detection"
    VIDEO_EFFECTS = "video_effects"

class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Task(TimestampModel, table=True):
    __tablename__ = "tasks"

    id: Optional[int] = Field(primary_key=True, nullable=False, default=None)
    type: TaskType = Field(sa_column=Column(SQLModelEnum(TaskType)))
    status: TaskStatus = Field(sa_column=Column(SQLModelEnum(TaskStatus)), default=TaskStatus.PENDING)
    error_message: Optional[str] = None

    # Every task belongs to a game (central entity)
    game_id: int = Field(foreign_key="games.id")
    game: Game = Relationship(back_populates="tasks")

    # Every task has a user assigned
    user_id: int = Field(foreign_key="users.id")
    user: User = Relationship(back_populates="tasks")

    # Optional links to specific objects
    # video_id: Optional[int] = Field(default=None, foreign_key="videos.id")
    # highlight_id: Optional[int] = Field(default=None, foreign_key="highlights.id")

